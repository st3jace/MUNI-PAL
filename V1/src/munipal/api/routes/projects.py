"""
Project management endpoints.

Per spec: Project is the workspace for one bond-eligible project.
All artifacts, facts, and deliverables belong to a project.
"""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from munipal.api.dependencies import AuthenticatedUserId, DbSession
from munipal.core.schemas.project import (
    ProjectCreate,
    ProjectRead,
    ProjectSummary,
    ProjectUpdate,
)
from munipal.services.project_service import ProjectService

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=ProjectRead)
async def create_project(
    data: ProjectCreate,
    db: DbSession,
    user_id: AuthenticatedUserId,
) -> ProjectRead:
    """
    Create a new project.

    A project is the workspace for one bond-eligible project.
    If no playbook_id is provided, the default UCS CAB+SLB playbook is used.
    """
    service = ProjectService(db)
    try:
        return await service.create(data, owner_id=user_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/", response_model=dict)
async def list_projects(
    db: DbSession,
    user_id: AuthenticatedUserId,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> dict:
    """
    List all projects accessible to the current user.

    Returns paginated list with summary information.
    """
    service = ProjectService(db)
    projects, total = await service.list(owner_id=user_id, skip=skip, limit=limit)

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
) -> ProjectRead:
    """Get a specific project by ID with computed metrics."""
    service = ProjectService(db)
    project = await service.get(project_id)

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    # TODO: Add ownership/permission check
    return project


@router.patch("/{project_id}", response_model=ProjectRead)
async def update_project(
    project_id: UUID,
    data: ProjectUpdate,
    db: DbSession,
    user_id: AuthenticatedUserId,
) -> ProjectRead:
    """Update a project's metadata."""
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
) -> None:
    """
    Delete a project.

    WARNING: This will delete all associated artifacts, facts, and deliverables.
    This action cannot be undone.
    """
    service = ProjectService(db)
    deleted = await service.delete(project_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )
