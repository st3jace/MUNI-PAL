"""
Extracted facts management endpoints.

Per spec: ExtractedFact is the CORE PRIMITIVE - a structured, reviewable claim
about the project with full provenance tracing.

Facts have a review lifecycle: pending -> approved/rejected/needs_revision
"""

from typing import Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from munipal.db.session import get_async_session

router = APIRouter()


@router.get("/")
async def list_facts(
    project_id: UUID,
    status_filter: Literal["pending", "approved", "rejected", "needs_revision"] | None = None,
    schema_path: str | None = Query(None, description="Filter by schema path prefix"),
    min_confidence: float | None = Query(None, ge=0.0, le=1.0),
    db: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """
    List extracted facts for a project.

    Supports filtering by review status, schema path, and confidence threshold.
    """
    # TODO: Implement fact listing with filters
    return {"facts": [], "total": 0}


@router.get("/{fact_id}")
async def get_fact(
    fact_id: UUID,
    db: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """
    Get a specific fact with full provenance chain.

    Returns the fact value, confidence score, source chunk references,
    and revision history.
    """
    # TODO: Implement fact retrieval
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Fact {fact_id} not found",
    )


@router.post("/{fact_id}/approve", status_code=status.HTTP_200_OK)
async def approve_fact(
    fact_id: UUID,
    # TODO: Add optional correction field
    db: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """
    Approve an extracted fact.

    Per spec: "AI proposes; humans approve." This endpoint allows a human
    reviewer to approve a fact, optionally with corrections.
    """
    # TODO: Implement fact approval
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Fact approval not yet implemented",
    )


@router.post("/{fact_id}/reject", status_code=status.HTTP_200_OK)
async def reject_fact(
    fact_id: UUID,
    reason: str | None = None,
    db: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """
    Reject an extracted fact.

    The fact will be marked as rejected and will not contribute to
    readiness scoring or checklist completion.
    """
    # TODO: Implement fact rejection
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Fact rejection not yet implemented",
    )


@router.post("/{fact_id}/revise", status_code=status.HTTP_200_OK)
async def request_revision(
    fact_id: UUID,
    revision_note: str,
    db: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """
    Request revision of an extracted fact.

    Flags the fact as needing human attention without fully rejecting it.
    """
    # TODO: Implement revision request
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Revision request not yet implemented",
    )


@router.get("/{fact_id}/revisions")
async def list_fact_revisions(
    fact_id: UUID,
    db: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """
    Get the full revision history for a fact.

    Per spec: FactRevision is an immutable audit log of all changes.
    """
    # TODO: Implement revision history
    return {"revisions": []}
