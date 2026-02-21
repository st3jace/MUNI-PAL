"""
Authorization service for project-scoped access checks.
"""

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from munipal.config import get_settings
from munipal.core.models import Artifact, ExtractionJob, Project, User
from munipal.core.models.fact import ExtractedFact

DEFAULT_TENANT_ID = "default"


class AuthorizationService:
    """Project/object authorization checks."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def is_superuser(self, user_id: str) -> bool:
        """Public superuser check."""
        return await self._is_superuser(user_id)

    async def should_filter_tenant(self, user_id: str) -> bool:
        """Return whether tenant filtering should be applied for current request."""
        settings = get_settings()
        if not settings.tenant_isolation_v2:
            return False
        return True

    async def can_read_project(
        self,
        user_id: str,
        project_id: UUID,
        tenant_id: str | None = None,
    ) -> bool:
        """Return True when user can read the project."""
        project = await self.db.get(Project, str(project_id))
        if not project:
            return False

        if await self._is_cross_tenant_access(
            user_id=user_id,
            project_tenant_id=project.tenant_id,
            tenant_id=tenant_id,
        ):
            return False

        if project.owner_id == user_id:
            return True

        return await self._is_superuser(user_id)

    async def can_write_project(
        self,
        user_id: str,
        project_id: UUID,
        tenant_id: str | None = None,
    ) -> bool:
        """Return True when user can modify the project."""
        project = await self.db.get(Project, str(project_id))
        if not project:
            return False

        if await self._is_cross_tenant_access(
            user_id=user_id,
            project_tenant_id=project.tenant_id,
            tenant_id=tenant_id,
        ):
            return False

        if project.owner_id == user_id:
            return True

        return await self._is_superuser(user_id)

    async def require_project_read(
        self,
        user_id: str,
        project_id: UUID,
        tenant_id: str | None = None,
    ) -> None:
        """Raise 403 if user cannot read project, 404 if project doesn't exist."""
        project = await self.db.get(Project, str(project_id))
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found",
            )

        if await self._is_cross_tenant_access(
            user_id=user_id,
            project_tenant_id=project.tenant_id,
            tenant_id=tenant_id,
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: cross-tenant access denied",
            )

        if project.owner_id == user_id:
            return

        if await self._is_superuser(user_id):
            return

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: insufficient access to project",
        )

    async def require_project_write(
        self,
        user_id: str,
        project_id: UUID,
        tenant_id: str | None = None,
    ) -> None:
        """Raise 403 if user cannot modify project, 404 if project doesn't exist."""
        project = await self.db.get(Project, str(project_id))
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found",
            )

        if await self._is_cross_tenant_access(
            user_id=user_id,
            project_tenant_id=project.tenant_id,
            tenant_id=tenant_id,
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: cross-tenant access denied",
            )

        if project.owner_id == user_id:
            return

        if await self._is_superuser(user_id):
            return

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: insufficient access to project",
        )

    async def require_artifact_read(
        self,
        user_id: str,
        artifact_id: UUID,
        tenant_id: str | None = None,
    ) -> None:
        """Raise 403 if user cannot read artifact, 404 if artifact doesn't exist."""
        artifact = await self.db.get(Artifact, str(artifact_id))
        if not artifact:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Artifact {artifact_id} not found",
            )
        await self.require_project_read(user_id, UUID(artifact.project_id), tenant_id=tenant_id)

    async def require_artifact_write(
        self,
        user_id: str,
        artifact_id: UUID,
        tenant_id: str | None = None,
    ) -> None:
        """Raise 403 if user cannot modify artifact, 404 if artifact doesn't exist."""
        artifact = await self.db.get(Artifact, str(artifact_id))
        if not artifact:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Artifact {artifact_id} not found",
            )
        await self.require_project_write(user_id, UUID(artifact.project_id), tenant_id=tenant_id)

    async def require_extraction_job_read(
        self,
        user_id: str,
        job_id: UUID,
        tenant_id: str | None = None,
    ) -> None:
        """Raise 403 if user cannot read extraction job, 404 if job doesn't exist."""
        job = await self.db.get(ExtractionJob, str(job_id))
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Extraction job {job_id} not found",
            )
        await self.require_project_read(user_id, UUID(job.project_id), tenant_id=tenant_id)

    async def require_extraction_job_write(
        self,
        user_id: str,
        job_id: UUID,
        tenant_id: str | None = None,
    ) -> None:
        """Raise 403 if user cannot modify extraction job, 404 if job doesn't exist."""
        job = await self.db.get(ExtractionJob, str(job_id))
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Extraction job {job_id} not found",
            )
        await self.require_project_write(user_id, UUID(job.project_id), tenant_id=tenant_id)

    async def require_fact_read(
        self,
        user_id: str,
        fact_id: UUID,
        tenant_id: str | None = None,
    ) -> None:
        """Raise 403 if user cannot read fact, 404 if fact doesn't exist."""
        fact = await self.db.get(ExtractedFact, str(fact_id))
        if not fact:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Fact {fact_id} not found",
            )
        await self.require_project_read(user_id, UUID(fact.project_id), tenant_id=tenant_id)

    async def require_fact_write(
        self,
        user_id: str,
        fact_id: UUID,
        tenant_id: str | None = None,
    ) -> None:
        """Raise 403 if user cannot modify fact, 404 if fact doesn't exist."""
        fact = await self.db.get(ExtractedFact, str(fact_id))
        if not fact:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Fact {fact_id} not found",
            )
        await self.require_project_write(user_id, UUID(fact.project_id), tenant_id=tenant_id)

    async def _is_superuser(self, user_id: str) -> bool:
        """Check superuser privilege when user row exists."""
        user = await self.db.get(User, user_id)
        if not user:
            return False
        return bool(user.is_superuser)

    async def _is_cross_tenant_access(
        self,
        *,
        user_id: str,
        project_tenant_id: str,
        tenant_id: str | None,
    ) -> bool:
        """Return True when request tenant does not match project tenant."""
        settings = get_settings()
        if not settings.tenant_isolation_v2:
            return False

        effective_tenant = (
            tenant_id.strip() if isinstance(tenant_id, str) and tenant_id.strip() else None
        )
        if not effective_tenant:
            user = await self.db.get(User, user_id)
            if user and user.organization and user.organization.strip():
                effective_tenant = user.organization.strip()
            else:
                effective_tenant = DEFAULT_TENANT_ID

        normalized_project_tenant = project_tenant_id.strip() or DEFAULT_TENANT_ID
        return effective_tenant != normalized_project_tenant
