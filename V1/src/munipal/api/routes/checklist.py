"""
Checklist management endpoints.

Per spec: ChecklistItem represents operational bond diligence requirements.
Status is computed from linked facts, not stored directly.

Playbook defines P1-P6 phases with specific checklist items per phase.
"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from munipal.core.schemas.base import ChecklistPhase, ChecklistStatus
from munipal.core.schemas.checklist import (
    ChecklistItemDefinition,
    ChecklistItemStatus,
    ChecklistPhaseSummary,
)
from munipal.db.session import get_async_session
from munipal.services.checklist_service import ChecklistService

router = APIRouter()


def get_checklist_service(
    db: AsyncSession = Depends(get_async_session),
) -> ChecklistService:
    """Dependency to get ChecklistService instance."""
    return ChecklistService(db)


# -----------------------------------------------------------------------------
# Checklist Items
# -----------------------------------------------------------------------------


@router.get("/", response_model=dict[str, Any])
async def list_checklist_items(
    project_id: UUID,
    phase: ChecklistPhase | None = None,
    status_filter: ChecklistStatus | None = None,
    service: ChecklistService = Depends(get_checklist_service),
) -> dict[str, Any]:
    """
    List checklist items for a project with computed status.

    Per spec: Checklist phases are:
    - P1: Issuer Authority & Deal Formation
    - P2: Project & Technology Definition
    - P3: Financial Structure & Revenue Model
    - P4: Risk, Security & Disclosure
    - P5: SLB Architecture & Final Modeling
    - P6: Advisor Engagement & Execution

    Status is computed from linked facts:
    - not_started: No approved facts for required paths
    - in_progress: Some required paths covered
    - blocked: Critical path missing or low confidence
    - ready: All required paths have approved facts
    """
    items = await service.list_items_with_status(
        project_id=project_id,
        phase=phase,
        status_filter=status_filter,
    )

    return {
        "checklist_items": [item.model_dump() for item in items],
        "total": len(items),
        "filters": {
            "phase": phase.value if phase else None,
            "status": status_filter.value if status_filter else None,
        },
    }


@router.get("/definitions", response_model=list[ChecklistItemDefinition])
async def list_definitions(
    phase: ChecklistPhase | None = None,
    service: ChecklistService = Depends(get_checklist_service),
) -> list[ChecklistItemDefinition]:
    """
    List checklist item definitions from playbook.

    Returns the template definitions without project-specific status.
    Useful for understanding what evidence is needed.
    """
    return service.get_item_definitions(phase)


@router.get("/summary", response_model=dict[str, ChecklistPhaseSummary])
async def get_checklist_summary(
    project_id: UUID,
    service: ChecklistService = Depends(get_checklist_service),
) -> dict[str, ChecklistPhaseSummary]:
    """
    Get a summary of checklist completion by phase.

    Returns counts and percentages for each P1-P6 phase,
    including whether each phase can proceed to the next.
    """
    return await service.get_all_phases_summary(project_id)


@router.get("/gaps", response_model=dict[str, Any])
async def get_project_gaps(
    project_id: UUID,
    service: ChecklistService = Depends(get_checklist_service),
) -> dict[str, Any]:
    """
    Get comprehensive gap analysis for entire project.

    Returns all missing evidence organized by phase and criticality.
    Useful for understanding what documents to upload next.
    """
    return await service.get_project_gaps(project_id)


# -----------------------------------------------------------------------------
# Single Item Operations
# -----------------------------------------------------------------------------


@router.get("/{item_code}", response_model=ChecklistItemStatus)
async def get_checklist_item(
    project_id: UUID,
    item_code: str,
    service: ChecklistService = Depends(get_checklist_service),
) -> ChecklistItemStatus:
    """
    Get a specific checklist item with its computed status.

    Returns the item definition, required fact paths, current status,
    and any blocking issues.
    """
    item_status = await service.compute_item_status(project_id, item_code)
    if not item_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Checklist item {item_code} not found",
        )

    return item_status


@router.get("/{item_code}/definition", response_model=ChecklistItemDefinition)
async def get_item_definition(
    item_code: str,
    service: ChecklistService = Depends(get_checklist_service),
) -> ChecklistItemDefinition:
    """
    Get the playbook definition for a checklist item.

    Returns the template without project-specific status.
    """
    definition = service.get_item_definition(item_code)
    if not definition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Checklist item {item_code} not found in playbook",
        )

    return definition


@router.get("/{item_code}/gaps", response_model=dict[str, Any])
async def get_checklist_gaps(
    project_id: UUID,
    item_code: str,
    service: ChecklistService = Depends(get_checklist_service),
) -> dict[str, Any]:
    """
    Get missing evidence for a checklist item.

    Returns the specific schema paths that lack approved facts,
    enabling targeted document upload or fact entry.

    Also provides recommendations for closing gaps.
    """
    gaps = await service.get_item_gaps(project_id, item_code)
    if "error" in gaps:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=gaps["error"],
        )

    return gaps


@router.get("/{item_code}/facts", response_model=list[dict])
async def get_item_facts(
    project_id: UUID,
    item_code: str,
    approved_only: bool = Query(True, description="Only return approved facts"),
    service: ChecklistService = Depends(get_checklist_service),
) -> list[dict]:
    """
    Get all facts relevant to a checklist item.

    Returns facts whose schema paths match the item's required
    and optional paths.
    """
    facts = await service.get_facts_for_item(
        project_id=project_id,
        item_code=item_code,
        approved_only=approved_only,
    )

    return [
        {
            "id": f.id,
            "schema_path": f.schema_path,
            "value": f.value,
            "confidence_score": f.confidence_score,
            "review_status": f.review_status,
            "criticality": f.criticality,
        }
        for f in facts
    ]


# -----------------------------------------------------------------------------
# Phase Operations
# -----------------------------------------------------------------------------


@router.get("/phase/{phase}", response_model=ChecklistPhaseSummary)
async def get_phase_summary(
    project_id: UUID,
    phase: ChecklistPhase,
    service: ChecklistService = Depends(get_checklist_service),
) -> ChecklistPhaseSummary:
    """
    Get detailed summary for a specific phase.

    Includes completion percentage and whether all blocking
    items are ready to proceed to next phase.
    """
    return await service.get_phase_summary(project_id, phase)


@router.get("/phase/{phase}/items", response_model=list[ChecklistItemStatus])
async def list_phase_items(
    project_id: UUID,
    phase: ChecklistPhase,
    service: ChecklistService = Depends(get_checklist_service),
) -> list[ChecklistItemStatus]:
    """
    List all checklist items in a phase with computed status.
    """
    return await service.list_items_with_status(project_id, phase)
