"""
Project management endpoints.

Per spec: Project is the workspace for one bond-eligible project.
All artifacts, facts, and deliverables belong to a project.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from munipal.api.dependencies import (
    AuthenticatedUserId,
    CurrentTenantId,
    DbSession,
    require_roles,
)
from munipal.core.schemas.project import (
    ProjectCreate,
    ProjectRead,
    ProjectUpdate,
)
from munipal.services.audit_service import AuditService
from munipal.services.authorization_service import AuthorizationService
from munipal.services.project_service import ProjectService

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=ProjectRead)
async def create_project(
    data: ProjectCreate,
    db: DbSession,
    user_id: AuthenticatedUserId,
    tenant_id: CurrentTenantId,
    _: str = Depends(require_roles("admin", "analyst")),
) -> ProjectRead:
    """
    Create a new project.

    A project is the workspace for one bond-eligible project.
    If no playbook_id is provided, the default UCS CAB+SLB playbook is used.
    """
    service = ProjectService(db)
    try:
        return await service.create(data, owner_id=user_id, tenant_id=tenant_id)
    except ValueError as e:
        message = str(e)
        status_code = (
            status.HTTP_404_NOT_FOUND
            if "Playbook" in message
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(
            status_code=status_code,
            detail=message,
        ) from e


@router.get("/", response_model=dict)
async def list_projects(
    db: DbSession,
    user_id: AuthenticatedUserId,
    tenant_id: CurrentTenantId,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    _: str = Depends(require_roles("admin", "analyst", "viewer")),
) -> dict:
    """
    List all projects accessible to the current user.

    Returns paginated list with summary information.
    """
    service = ProjectService(db)
    authz = AuthorizationService(db)
    owner_filter = None if await authz.is_superuser(user_id) else user_id
    tenant_filter = tenant_id if await authz.should_filter_tenant(user_id) else None
    projects, total = await service.list(
        owner_id=owner_filter,
        tenant_id=tenant_filter,
        skip=skip,
        limit=limit,
    )

    return {
        "projects": [p.model_dump() for p in projects],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/{project_id}", response_model=ProjectRead)
async def get_project(
    project_id: UUID,
    db: DbSession,
    user_id: AuthenticatedUserId,
    tenant_id: CurrentTenantId,
    _: str = Depends(require_roles("admin", "analyst", "viewer")),
) -> ProjectRead:
    """Get a specific project by ID with computed metrics."""
    authz = AuthorizationService(db)
    await authz.require_project_read(user_id, project_id, tenant_id=tenant_id)

    service = ProjectService(db)
    project = await service.get(project_id)

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )
    return project


@router.patch("/{project_id}", response_model=ProjectRead)
async def update_project(
    project_id: UUID,
    data: ProjectUpdate,
    db: DbSession,
    user_id: AuthenticatedUserId,
    tenant_id: CurrentTenantId,
    _: str = Depends(require_roles("admin", "analyst")),
) -> ProjectRead:
    """Update a project's metadata."""
    authz = AuthorizationService(db)
    await authz.require_project_write(user_id, project_id, tenant_id=tenant_id)

    service = ProjectService(db)
    project = await service.update(project_id, data)

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: UUID,
    db: DbSession,
    user_id: AuthenticatedUserId,
    tenant_id: CurrentTenantId,
    _: str = Depends(require_roles("admin")),
) -> None:
    """
    Delete a project.

    WARNING: This will delete all associated artifacts, facts, and deliverables.
    This action cannot be undone.
    """
    authz = AuthorizationService(db)
    await authz.require_project_write(user_id, project_id, tenant_id=tenant_id)

    service = ProjectService(db)
    deleted = await service.delete(project_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    AuditService.emit_event(
        actor_id=user_id,
        action="delete_project",
        target_type="project",
        target_id=str(project_id),
        project_id=str(project_id),
    )
