"""
Extracted facts management endpoints.

Per spec: ExtractedFact is the CORE PRIMITIVE - a structured, reviewable claim
about the project with full provenance tracing.

Facts have a review lifecycle: pending -> approved/rejected/needs_revision
"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from munipal.core.schemas.base import ReviewStatus, CriticalityTier, ChecklistPhase
from munipal.core.schemas.fact import (
    ExtractedFactRead,
    ExtractedFactSummary,
    FactReviewRequest,
    FactRevisionRead,
    ManualFactCreate,
    MissingPathInfo,
)
from munipal.db.session import get_async_session
from munipal.services.fact_service import FactService, FactConflictDetector

router = APIRouter()


def get_fact_service(db: AsyncSession = Depends(get_async_session)) -> FactService:
    """Dependency to get FactService instance."""
    return FactService(db)


def get_conflict_detector(
    db: AsyncSession = Depends(get_async_session),
) -> FactConflictDetector:
    """Dependency to get FactConflictDetector instance."""
    return FactConflictDetector(db)


# -----------------------------------------------------------------------------
# List and Query Facts
# -----------------------------------------------------------------------------


@router.get("/", response_model=dict[str, Any])
async def list_facts(
    project_id: UUID,
    status_filter: ReviewStatus | None = None,
    schema_path: str | None = Query(None, description="Filter by schema path prefix"),
    min_confidence: float | None = Query(None, ge=0.0, le=1.0),
    criticality: CriticalityTier | None = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    service: FactService = Depends(get_fact_service),
) -> dict[str, Any]:
    """
    List extracted facts for a project.

    Supports filtering by review status, schema path, confidence threshold,
    and criticality tier. Returns paginated results.
    """
    facts, total = await service.list_facts(
        project_id=project_id,
        status_filter=status_filter,
        schema_path_prefix=schema_path,
        min_confidence=min_confidence,
        criticality=criticality,
        limit=limit,
        offset=offset,
    )

    return {
        "facts": [service.fact_to_summary_schema(f) for f in facts],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/counts", response_model=dict[str, int])
async def get_review_counts(
    project_id: UUID,
    service: FactService = Depends(get_fact_service),
) -> dict[str, int]:
    """
    Get count of facts by review status for a project.

    Useful for dashboard displays showing pending review queue.
    """
    return await service.get_pending_review_count(project_id)


@router.get("/by-path", response_model=list[ExtractedFactSummary])
async def get_facts_by_path(
    project_id: UUID,
    schema_path: str = Query(..., description="Exact schema path to match"),
    approved_only: bool = Query(False, description="Only return approved facts"),
    service: FactService = Depends(get_fact_service),
) -> list[ExtractedFactSummary]:
    """
    Get all facts for a specific schema path.

    Returns facts ordered by confidence score (highest first).
    """
    facts = await service.get_facts_by_schema_path(
        project_id=project_id,
        schema_path=schema_path,
        approved_only=approved_only,
    )
    return [service.fact_to_summary_schema(f) for f in facts]


@router.get("/missing-paths", response_model=list[MissingPathInfo])
async def get_missing_paths(
    project_id: UUID,
    phase: str | None = Query(None, description="Filter by checklist phase (P1-P6)"),
    criticality: str | None = Query(None, description="Filter by criticality tier"),
    service: FactService = Depends(get_fact_service),
) -> list[MissingPathInfo]:
    """
    Get schema paths that don't have approved facts yet.

    Returns paths that are required by checklist items but don't have
    approved facts. Useful for identifying what manual facts need to be entered.

    Sorted by criticality (critical first) then by phase.
    """
    return await service.get_missing_paths(
        project_id=project_id,
        phase=phase,
        criticality=criticality,
    )


# -----------------------------------------------------------------------------
# Manual Fact Creation
# -----------------------------------------------------------------------------


@router.post("/manual", response_model=ExtractedFactRead)
async def create_manual_fact(
    request: ManualFactCreate,
    created_by: UUID = Query(..., description="ID of user creating the fact"),
    auto_approve: bool = Query(
        False,
        description="If true, fact is immediately approved without review",
    ),
    service: FactService = Depends(get_fact_service),
) -> ExtractedFactRead:
    """
    Create a manually-entered fact.

    Manual facts are entered by users when they have information but
    don't have documentation to extract from. These facts:
    - Have source_type='manual'
    - Have confidence_score=1.0 (user is authoritative)
    - Don't require source chunks (no extraction job)
    - Follow the same approval workflow as extracted facts

    Use auto_approve=true if you trust the input and want to skip review.
    """
    fact = await service.create_manual_fact(
        request=request,
        created_by=created_by,
        auto_approve=auto_approve,
    )
    return service.fact_to_read_schema(fact)


# -----------------------------------------------------------------------------
# Single Fact Operations
# -----------------------------------------------------------------------------


@router.get("/{fact_id}", response_model=ExtractedFactRead)
async def get_fact(
    fact_id: UUID,
    service: FactService = Depends(get_fact_service),
) -> ExtractedFactRead:
    """
    Get a specific fact with full provenance chain.

    Returns the fact value, confidence score, source chunk references,
    and review status. Use the /revisions endpoint for revision history.
    """
    fact = await service.get_fact(fact_id)
    if not fact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fact {fact_id} not found",
        )

    return service.fact_to_read_schema(fact)


# -----------------------------------------------------------------------------
# Review Workflow
# -----------------------------------------------------------------------------


@router.post("/{fact_id}/review", response_model=ExtractedFactRead)
async def review_fact(
    fact_id: UUID,
    review: FactReviewRequest,
    reviewer_id: UUID = Query(..., description="ID of user submitting review"),
    service: FactService = Depends(get_fact_service),
) -> ExtractedFactRead:
    """
    Submit a review for an extracted fact.

    Per spec: "AI proposes; humans approve." This endpoint allows human
    reviewers to approve, reject, or flag facts for revision.

    - approve: Accept the fact (optionally with corrections)
    - reject: Reject the fact (it won't contribute to readiness)
    - needs_revision: Flag for further review without rejecting
    """
    try:
        fact = await service.review_fact(fact_id, reviewer_id, review)
        return service.fact_to_read_schema(fact)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post("/{fact_id}/approve", response_model=ExtractedFactRead)
async def approve_fact(
    fact_id: UUID,
    reviewer_id: UUID = Query(..., description="ID of user approving"),
    corrected_value: Any | None = None,
    note: str | None = Query(None, max_length=1000),
    service: FactService = Depends(get_fact_service),
) -> ExtractedFactRead:
    """
    Approve an extracted fact.

    Per spec: "AI proposes; humans approve." This endpoint allows a human
    reviewer to approve a fact, optionally with corrections.

    If corrected_value is provided, the original AI-extracted value is
    preserved and the corrected value becomes the current value.
    """
    try:
        fact = await service.approve_fact(
            fact_id=fact_id,
            reviewer_id=reviewer_id,
            corrected_value=corrected_value,
            note=note,
        )
        return service.fact_to_read_schema(fact)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post("/{fact_id}/reject", response_model=ExtractedFactRead)
async def reject_fact(
    fact_id: UUID,
    reviewer_id: UUID = Query(..., description="ID of user rejecting"),
    reason: str | None = Query(None, max_length=1000),
    service: FactService = Depends(get_fact_service),
) -> ExtractedFactRead:
    """
    Reject an extracted fact.

    The fact will be marked as rejected and will not contribute to
    readiness scoring or checklist completion.
    """
    try:
        fact = await service.reject_fact(
            fact_id=fact_id,
            reviewer_id=reviewer_id,
            reason=reason,
        )
        return service.fact_to_read_schema(fact)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post("/{fact_id}/revise", response_model=ExtractedFactRead)
async def request_revision(
    fact_id: UUID,
    revision_note: str = Query(..., min_length=1, max_length=1000),
    reviewer_id: UUID = Query(..., description="ID of user requesting revision"),
    service: FactService = Depends(get_fact_service),
) -> ExtractedFactRead:
    """
    Request revision of an extracted fact.

    Flags the fact as needing human attention without fully rejecting it.
    Use this when the extracted value seems wrong but you want to
    investigate further rather than outright reject.
    """
    try:
        fact = await service.request_revision(
            fact_id=fact_id,
            reviewer_id=reviewer_id,
            revision_note=revision_note,
        )
        return service.fact_to_read_schema(fact)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# -----------------------------------------------------------------------------
# Revision History
# -----------------------------------------------------------------------------


@router.get("/{fact_id}/revisions", response_model=list[FactRevisionRead])
async def list_fact_revisions(
    fact_id: UUID,
    service: FactService = Depends(get_fact_service),
) -> list[FactRevisionRead]:
    """
    Get the full revision history for a fact.

    Per spec: FactRevision is an immutable audit log of all changes.
    Returns revisions in chronological order (oldest first).
    """
    # Verify fact exists
    fact = await service.get_fact(fact_id)
    if not fact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fact {fact_id} not found",
        )

    revisions = await service.list_revisions(fact_id)
    return [service.revision_to_schema(r) for r in revisions]


# -----------------------------------------------------------------------------
# Conflict Detection
# -----------------------------------------------------------------------------


@router.get("/conflicts/", response_model=list[dict])
async def find_conflicts(
    project_id: UUID,
    schema_path: str | None = Query(None, description="Specific path to check"),
    detector: FactConflictDetector = Depends(get_conflict_detector),
) -> list[dict]:
    """
    Find conflicting facts in a project.

    Conflicts occur when multiple extractions produce different values
    for the same schema path. Returns grouped conflicts with all
    competing facts listed.
    """
    return await detector.find_conflicts(project_id, schema_path)


@router.post("/conflicts/resolve", response_model=list[dict])
async def resolve_conflicts(
    project_id: UUID,
    strategy: str = Query(
        "highest_confidence",
        description="Resolution strategy: highest_confidence",
    ),
    detector: FactConflictDetector = Depends(get_conflict_detector),
) -> list[dict]:
    """
    Automatically resolve fact conflicts using specified strategy.

    Available strategies:
    - highest_confidence: Keep the fact with highest confidence score,
      reject others

    Returns list of resolution records showing which facts were kept
    and which were rejected.
    """
    try:
        return await detector.auto_resolve_conflicts(project_id, strategy)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
