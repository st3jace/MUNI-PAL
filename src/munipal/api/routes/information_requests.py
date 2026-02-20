"""
Information request endpoints for WP8 - Information Request System.

Per spec: WP8 transforms gap analysis from binary indicators into actionable
information requests that guide the team toward producing/procuring specific evidence.
"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from munipal.api.dependencies import require_auth
from munipal.core.schemas.information_request import (
    InformationRequestCreate,
    InformationRequestRead,
    InformationRequestReport,
    InformationRequestSummary,
    InformationRequestUpdate,
    LinkEvidenceRequest,
    RequestPriority,
    RequestStatus,
    ResolveRequestInput,
)
from munipal.db.session import get_async_session
from munipal.services.information_request_service import InformationRequestService

router = APIRouter(dependencies=[Depends(require_auth)])


def get_request_service(
    db: AsyncSession = Depends(get_async_session),
) -> InformationRequestService:
    """Dependency to get InformationRequestService instance."""
    return InformationRequestService(db)


# -----------------------------------------------------------------------------
# Request Generation
# -----------------------------------------------------------------------------


@router.post("/generate", response_model=dict[str, Any])
async def generate_information_requests(
    project_id: UUID,
    service: InformationRequestService = Depends(get_request_service),
) -> dict[str, Any]:
    """
    Generate information requests from gap analysis.

    Per WP8 spec: Each gap type maps to a request template.
    Requests include bond-domain context, guidance, and examples.
    """
    try:
        requests = await service.generate_requests_from_gaps(project_id)
        return {
            "generated_count": len(requests),
            "requests": [service.request_to_summary(r) for r in requests],
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


# -----------------------------------------------------------------------------
# Request CRUD
# -----------------------------------------------------------------------------


@router.post("/", response_model=InformationRequestRead)
async def create_information_request(
    request: InformationRequestCreate,
    service: InformationRequestService = Depends(get_request_service),
) -> InformationRequestRead:
    """Create a new information request manually."""
    info_request = await service.create_request(request)
    return service.request_to_read_schema(info_request)


@router.get("/{request_id}", response_model=InformationRequestRead)
async def get_information_request(
    request_id: UUID,
    service: InformationRequestService = Depends(get_request_service),
) -> InformationRequestRead:
    """Get an information request by ID."""
    request = await service.get_request(request_id)
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Information request {request_id} not found",
        )
    return service.request_to_read_schema(request)


@router.get("/", response_model=dict[str, Any])
async def list_information_requests(
    project_id: UUID,
    status_filter: RequestStatus | None = None,
    priority: RequestPriority | None = None,
    owner: str | None = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    service: InformationRequestService = Depends(get_request_service),
) -> dict[str, Any]:
    """
    List information requests for a project.

    Supports filtering by status, priority, and owner.
    """
    requests, total = await service.list_requests(
        project_id=project_id,
        status=status_filter,
        priority=priority,
        owner=owner,
        limit=limit,
        offset=offset,
    )

    return {
        "requests": [service.request_to_summary(r) for r in requests],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.patch("/{request_id}", response_model=InformationRequestRead)
async def update_information_request(
    request_id: UUID,
    update: InformationRequestUpdate,
    service: InformationRequestService = Depends(get_request_service),
) -> InformationRequestRead:
    """
    Update an information request.

    Use to change status, assign owner, or set target date.
    """
    request = await service.update_request(request_id, update)
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Information request {request_id} not found",
        )
    return service.request_to_read_schema(request)


# -----------------------------------------------------------------------------
# Request Lifecycle
# -----------------------------------------------------------------------------


@router.post("/{request_id}/acknowledge", response_model=InformationRequestRead)
async def acknowledge_request(
    request_id: UUID,
    user_id: UUID | None = None,
    service: InformationRequestService = Depends(get_request_service),
) -> InformationRequestRead:
    """
    Acknowledge a request (mark as in_progress).

    Per WP8 spec: OPEN -> IN_PROGRESS when owner acknowledges.
    """
    update = InformationRequestUpdate(status=RequestStatus.IN_PROGRESS)
    request = await service.update_request(request_id, update, user_id)
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Information request {request_id} not found",
        )
    return service.request_to_read_schema(request)


@router.post("/{request_id}/evidence", response_model=InformationRequestRead)
async def link_evidence_to_request(
    request_id: UUID,
    evidence: LinkEvidenceRequest,
    service: InformationRequestService = Depends(get_request_service),
) -> InformationRequestRead:
    """
    Link an artifact as evidence for a request.

    Per WP8 spec: IN_PROGRESS -> SUBMITTED when evidence is uploaded.
    """
    request = await service.link_evidence(
        request_id=request_id,
        artifact_id=evidence.artifact_id,
        notes=evidence.notes,
    )
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Information request {request_id} not found",
        )
    return service.request_to_read_schema(request)


@router.post("/{request_id}/resolve", response_model=InformationRequestRead)
async def resolve_request(
    request_id: UUID,
    resolution: ResolveRequestInput,
    service: InformationRequestService = Depends(get_request_service),
) -> InformationRequestRead:
    """
    Resolve a request with accepted facts.

    Per WP8 spec: SUBMITTED -> RESOLVED when facts are accepted via WP3.
    """
    request = await service.resolve_request(
        request_id=request_id,
        fact_ids=resolution.fact_ids,
        resolution_notes=resolution.resolution_notes,
    )
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Information request {request_id} not found",
        )
    return service.request_to_read_schema(request)


@router.post("/{request_id}/defer", response_model=InformationRequestRead)
async def defer_request(
    request_id: UUID,
    reason: str,
    review_date: str | None = None,
    service: InformationRequestService = Depends(get_request_service),
) -> InformationRequestRead:
    """
    Defer a request with explanation.

    Per WP8 spec: Any status -> DEFERRED with recorded reason.
    """
    from datetime import date

    update = InformationRequestUpdate(
        status=RequestStatus.DEFERRED,
        deferred_reason=reason,
        deferred_review_date=date.fromisoformat(review_date) if review_date else None,
    )
    request = await service.update_request(request_id, update)
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Information request {request_id} not found",
        )
    return service.request_to_read_schema(request)


# -----------------------------------------------------------------------------
# Reporting
# -----------------------------------------------------------------------------


@router.get("/report/{project_id}", response_model=InformationRequestReport)
async def get_request_report(
    project_id: UUID,
    service: InformationRequestService = Depends(get_request_service),
) -> InformationRequestReport:
    """
    Get a summary report of information requests for a project.

    Includes counts by status/priority, overdue requests, and grouping by owner.
    """
    return await service.get_report(project_id)


@router.get("/overdue/{project_id}", response_model=list[InformationRequestSummary])
async def get_overdue_requests(
    project_id: UUID,
    service: InformationRequestService = Depends(get_request_service),
) -> list[InformationRequestSummary]:
    """Get overdue information requests for a project."""
    report = await service.get_report(project_id)
    return report.overdue_requests
