"""
Checklist management endpoints.

Per spec: ChecklistItem represents operational bond diligence requirements.
Status is computed from linked facts, not stored directly.

Playbook defines P1-P6 phases with specific checklist items per phase.
"""

from typing import Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from munipal.db.session import get_async_session

router = APIRouter()


@router.get("/")
async def list_checklist_items(
    project_id: UUID,
    phase: Literal["P1", "P2", "P3", "P4", "P5", "P6"] | None = None,
    status_filter: Literal["not_started", "in_progress", "blocked", "ready"] | None = None,
    db: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """
    List checklist items for a project.

    Per spec: Checklist phases are:
    - P1: Issuer Authority & Deal Formation
    - P2: Project & Technology Definition
    - P3: Financial Structure & Revenue Model
    - P4: Risk, Security & Disclosure
    - P5: SLB Architecture & Final Modeling
    - P6: Advisor Engagement & Execution
    """
    # TODO: Implement checklist listing
    return {"checklist_items": [], "total": 0}


@router.get("/{item_id}")
async def get_checklist_item(
    item_id: UUID,
    db: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """
    Get a specific checklist item with its linked facts and computed status.

    Returns the item definition, required fact paths, current status,
    and any blocking issues.
    """
    # TODO: Implement checklist item retrieval
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Checklist item {item_id} not found",
    )


@router.get("/{item_id}/gaps")
async def get_checklist_gaps(
    item_id: UUID,
    db: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """
    Get missing evidence for a checklist item.

    Returns the specific schema paths that lack approved facts,
    enabling targeted document upload or fact entry.
    """
    # TODO: Implement gap analysis
    return {"missing_paths": [], "partially_covered_paths": []}


@router.get("/summary")
async def get_checklist_summary(
    project_id: UUID,
    db: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """
    Get a summary of checklist completion by phase.

    Returns counts and percentages for each P1-P6 phase.
    """
    # TODO: Implement checklist summary
    return {
        "summary": {
            "P1": {"total": 0, "ready": 0, "in_progress": 0, "blocked": 0, "not_started": 0},
            "P2": {"total": 0, "ready": 0, "in_progress": 0, "blocked": 0, "not_started": 0},
            "P3": {"total": 0, "ready": 0, "in_progress": 0, "blocked": 0, "not_started": 0},
            "P4": {"total": 0, "ready": 0, "in_progress": 0, "blocked": 0, "not_started": 0},
            "P5": {"total": 0, "ready": 0, "in_progress": 0, "blocked": 0, "not_started": 0},
            "P6": {"total": 0, "ready": 0, "in_progress": 0, "blocked": 0, "not_started": 0},
        }
    }
