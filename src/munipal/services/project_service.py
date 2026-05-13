"""
Project service - business logic for project management.

Per spec: Project is the workspace for one bond-eligible project.
"""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from munipal.core.models import Artifact, ExtractedFact, Playbook, Project
from munipal.core.schemas.project import ProjectCreate, ProjectRead, ProjectSummary, ProjectUpdate
from munipal.services.sector_archetypes import resolve_archetype


class ProjectService:
    """Service for project CRUD operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        data: ProjectCreate,
        owner_id: str,
        tenant_id: str = "default",
    ) -> ProjectRead:
        """
        Create a new project.

        If no playbook_id is provided, uses the default active playbook.
        """
        # Get playbook (use provided or default)
        if data.playbook_id:
            playbook = await self.db.get(Playbook, str(data.playbook_id))
            if not playbook:
                raise ValueError(f"Playbook {data.playbook_id} not found")
        else:
            playbook = await self._resolve_create_playbook()

        archetype = resolve_archetype(data.sector, data.subsector)

        project = Project(
            name=data.name,
            description=data.description,
            issuer_name=data.issuer_name,
            project_location=data.project_location,
            target_bond_amount=data.target_bond_amount,
            sector=data.sector or archetype.sector,
            subsector=data.subsector or archetype.subsector,
            archetype_id=data.archetype_id or archetype.id,
            archetype_version=data.archetype_version or archetype.version,
            owner_id=owner_id,
            playbook_id=playbook.id,
            tenant_id=tenant_id,
        )

        self.db.add(project)
        await self.db.flush()
        await self.db.refresh(project)

        return await self._to_read_schema(project)

    async def _resolve_create_playbook(self) -> Playbook:
        """Resolve the playbook used for project creation when none is supplied.

        Prefer the explicit active default. In development/demo workspaces, tolerate
        one active playbook with no default flag so the Create Project form remains
        usable after seeding demo data. Multiple active non-default playbooks still
        require a configured default to avoid silently selecting the wrong playbook.
        """
        default_result = await self.db.execute(
            select(Playbook).where(
                Playbook.is_default.is_(True),
                Playbook.is_active.is_(True),
            )
        )
        default_playbook = default_result.scalar_one_or_none()
        if default_playbook:
            return default_playbook

        active_result = await self.db.execute(
            select(Playbook).where(Playbook.is_active.is_(True)).order_by(Playbook.created_at.asc())
        )
        active_playbooks = active_result.scalars().all()
        if len(active_playbooks) == 1:
            return active_playbooks[0]

        if active_playbooks:
            raise ValueError(
                "No default playbook configured. Please mark one active playbook as default before creating a project."
            )
        raise ValueError("No active playbook configured. Please create one first.")

    async def get(self, project_id: UUID) -> ProjectRead | None:
        """Get a project by ID with computed fields."""
        project = await self.db.get(Project, str(project_id))
        if not project:
            return None
        return await self._to_read_schema(project)

    async def list(
        self,
        owner_id: str | None = None,
        tenant_id: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[ProjectSummary], int]:
        """
        List projects with pagination.

        Returns (projects, total_count).
        """
        # Base query
        query = select(Project)
        count_query = select(func.count(Project.id))

        if owner_id:
            query = query.where(Project.owner_id == owner_id)
            count_query = count_query.where(Project.owner_id == owner_id)
        if tenant_id:
            query = query.where(Project.tenant_id == tenant_id)
            count_query = count_query.where(Project.tenant_id == tenant_id)

        # Get total count
        total = (await self.db.execute(count_query)).scalar() or 0

        # Get paginated results
        query = query.order_by(Project.updated_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        projects = result.scalars().all()

        # Convert to summaries
        summaries = []
        for project in projects:
            artifact_count = await self._count_artifacts(project.id)
            readiness_score = await self._get_readiness_score(project.id)

            summaries.append(
                ProjectSummary(
                    id=UUID(project.id),
                    name=project.name,
                    tenant_id=project.tenant_id,
                    issuer_name=project.issuer_name,
                    sector=project.sector,
                    subsector=project.subsector,
                    archetype_id=project.archetype_id,
                    archetype_version=project.archetype_version,
                    artifact_count=artifact_count,
                    overall_readiness_score=readiness_score,
                    updated_at=project.updated_at,
                )
            )

        return summaries, total

    async def update(
        self,
        project_id: UUID,
        data: ProjectUpdate,
    ) -> ProjectRead | None:
        """Update a project's metadata."""
        project = await self.db.get(Project, str(project_id))
        if not project:
            return None

        # Update only provided fields
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(project, field, value)

        await self.db.flush()
        await self.db.refresh(project)

        return await self._to_read_schema(project)

    async def delete(self, project_id: UUID) -> bool:
        """
        Delete a project and all associated data.

        Returns True if deleted, False if not found.
        """
        project = await self.db.get(Project, str(project_id))
        if not project:
            return False

        await self.db.delete(project)
        await self.db.flush()
        return True

    async def _to_read_schema(self, project: Project) -> ProjectRead:
        """Convert project model to read schema with computed fields."""
        artifact_count = await self._count_artifacts(project.id)
        fact_count, approved_fact_count = await self._count_facts(project.id)
        readiness_score = await self._get_readiness_score(project.id)

        return ProjectRead(
            id=UUID(project.id),
            name=project.name,
            description=project.description,
            issuer_name=project.issuer_name,
            project_location=project.project_location,
            target_bond_amount=project.target_bond_amount,
            sector=project.sector,
            subsector=project.subsector,
            archetype_id=project.archetype_id,
            archetype_version=project.archetype_version,
            playbook_id=UUID(project.playbook_id),
            owner_id=UUID(project.owner_id),
            tenant_id=project.tenant_id,
            artifact_count=artifact_count,
            fact_count=fact_count,
            approved_fact_count=approved_fact_count,
            overall_readiness_score=readiness_score,
            created_at=project.created_at,
            updated_at=project.updated_at,
        )

    async def _count_artifacts(self, project_id: str) -> int:
        """Count artifacts for a project."""
        result = await self.db.execute(
            select(func.count(Artifact.id)).where(Artifact.project_id == project_id)
        )
        return result.scalar() or 0

    async def _count_facts(self, project_id: str) -> tuple[int, int]:
        """Count total and approved facts for a project."""
        # Total facts
        total_result = await self.db.execute(
            select(func.count(ExtractedFact.id)).where(ExtractedFact.project_id == project_id)
        )
        total = total_result.scalar() or 0

        # Approved facts
        approved_result = await self.db.execute(
            select(func.count(ExtractedFact.id)).where(
                ExtractedFact.project_id == project_id,
                ExtractedFact.review_status == "approved",
            )
        )
        approved = approved_result.scalar() or 0

        return total, approved

    async def _get_readiness_score(self, project_id: str) -> float | None:
        """Calculate deterministic overall readiness score for a project."""
        from munipal.services.readiness_service import ReadinessService

        assessment = await ReadinessService(self.db).compute_assessment(UUID(project_id))
        return round(assessment.overall_score, 2)
