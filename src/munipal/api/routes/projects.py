"""
Project management endpoints.

Per spec: Project is the workspace for one bond-eligible project.
All artifacts, facts, and deliverables belong to a project.
"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from munipal.db.session import get_async_session

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_project(
    # TODO: Add project create schema
    db: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """
    Create a new project.

    A project is the workspace for one bond-eligible project.
    """
    # TODO: Implement project creation
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Project creation not yet implemented",
    )


@router.get("/")
async def list_projects(
    db: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """List all projects accessible to the current user."""
    # TODO: Implement project listing with pagination
    return {"projects": [], "total": 0}


@router.get("/{project_id}")
async def get_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """Get a specific project by ID."""
    # TODO: Implement project retrieval
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Project {project_id} not found",
    )


@router.patch("/{project_id}")
async def update_project(
    project_id: UUID,
    # TODO: Add project update schema
    db: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """Update a project's metadata."""
    # TODO: Implement project update
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Project update not yet implemented",
    )


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_async_session),
) -> None:
    """
    Delete a project.

    WARNING: This will delete all associated artifacts, facts, and deliverables.
    """
    # TODO: Implement project deletion (soft delete preferred)
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Project deletion not yet implemented",
    )
