"""
Deal document management endpoints.

Handles document CRUD, workflow state transitions, version history,
content editing, legal holds, export, and closing checklists.
Gated by document_management_v1 feature flag.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from munipal.api.dependencies import (
    AuthenticatedUserId,
    CurrentTenantId,
    DbSession,
    require_roles,
)
from munipal.config import get_settings
from munipal.core.schemas.deal_document import (
    ChecklistItemRead,
    ConsistencyCheckRequest,
    ConsistencyCheckResult,
    ContentUpdateRequest,
    DealDocumentCreate,
    DealDocumentRead,
    DealDocumentUpdate,
    DealDocumentVersionRead,
    StatusTransitionRequest,
    VersionDiff,
)
from munipal.services.deal_document_service import DealDocumentService
from munipal.services.document_consistency_service import DocumentConsistencyService

router = APIRouter()


def _check_feature_flag() -> None:
    """Raise 404 if document management is not enabled."""
    if not get_settings().document_management_v1:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document management is not enabled",
        )


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=DealDocumentRead)
async def create_deal_document(
    data: DealDocumentCreate,
    db: DbSession,
    user_id: AuthenticatedUserId,
    tenant_id: CurrentTenantId,
    _: str = Depends(require_roles("admin", "analyst")),
) -> DealDocumentRead:
    """Create a new deal document, optionally from a template."""
    _check_feature_flag()
    service = DealDocumentService(db)
    try:
        return await service.create(data, created_by_id=user_id, tenant_id=tenant_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.get("/", response_model=dict)
async def list_deal_documents(
    db: DbSession,
    user_id: AuthenticatedUserId,
    project_id: UUID = Query(..., description="Filter by project"),
    status_filter: str | None = Query(None, alias="status"),
    type_filter: str | None = Query(None, alias="type"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    _: str = Depends(require_roles("admin", "analyst", "viewer")),
) -> dict:
    """List deal documents for a project with optional filters."""
    _check_feature_flag()
    service = DealDocumentService(db)
    documents, total = await service.list_for_project(
        project_id=project_id,
        status_filter=status_filter,
        type_filter=type_filter,
        skip=skip,
        limit=limit,
    )
    return {
        "documents": [d.model_dump() for d in documents],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/types", response_model=list)
async def list_document_types(
    db: DbSession,
    _user_id: AuthenticatedUserId,
    deal_vertical: str | None = Query(None),
    __: str = Depends(require_roles("admin", "analyst", "viewer")),
) -> list:
    """List available document types."""
    _check_feature_flag()
    service = DealDocumentService(db)
    types = await service.list_document_types(deal_vertical=deal_vertical)
    return [t.model_dump() for t in types]


@router.get("/{document_id}", response_model=DealDocumentRead)
async def get_deal_document(
    document_id: UUID,
    db: DbSession,
    _user_id: AuthenticatedUserId,
    __: str = Depends(require_roles("admin", "analyst", "viewer")),
) -> DealDocumentRead:
    """Get a specific deal document by ID."""
    _check_feature_flag()
    service = DealDocumentService(db)
    document = await service.get(document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found",
        )
    return document


@router.patch("/{document_id}", response_model=DealDocumentRead)
async def update_deal_document(
    document_id: UUID,
    data: DealDocumentUpdate,
    db: DbSession,
    _user_id: AuthenticatedUserId,
    __: str = Depends(require_roles("admin", "analyst")),
) -> DealDocumentRead:
    """Update document metadata (title, assignment)."""
    _check_feature_flag()
    service = DealDocumentService(db)
    document = await service.update(document_id, data)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found",
        )
    return document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_deal_document(
    document_id: UUID,
    db: DbSession,
    user_id: AuthenticatedUserId,
    _: str = Depends(require_roles("admin")),
) -> None:
    """Delete a document. Blocked if under legal hold."""
    _check_feature_flag()
    service = DealDocumentService(db)
    try:
        deleted = await service.delete(document_id, user_id=user_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        ) from e

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found",
        )


# ---------------------------------------------------------------------------
# Content & Editor
# ---------------------------------------------------------------------------


@router.put("/{document_id}/content", response_model=DealDocumentRead)
async def update_document_content(
    document_id: UUID,
    data: ContentUpdateRequest,
    db: DbSession,
    user_id: AuthenticatedUserId,
    _: str = Depends(require_roles("admin", "analyst")),
) -> DealDocumentRead:
    """
    Update document content (editor auto-save).

    Optionally creates a version snapshot when auto_snapshot is true.
    Only allowed when document is in draft or under_review status.
    """
    _check_feature_flag()
    service = DealDocumentService(db)
    try:
        return await service.update_content(document_id, data, user_id=user_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


# ---------------------------------------------------------------------------
# Workflow Status
# ---------------------------------------------------------------------------


@router.post("/{document_id}/status", response_model=DealDocumentRead)
async def transition_document_status(
    document_id: UUID,
    data: StatusTransitionRequest,
    db: DbSession,
    user_id: AuthenticatedUserId,
    _: str = Depends(require_roles("admin", "analyst")),
) -> DealDocumentRead:
    """
    Transition document to a new workflow status.

    State machine: draft → under_review → approved → execution →
    signed → filed → archived.
    """
    _check_feature_flag()
    service = DealDocumentService(db)
    try:
        return await service.transition_status(
            document_id,
            new_status=data.new_status.value,
            user_id=user_id,
            comment=data.comment,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


# ---------------------------------------------------------------------------
# Version History
# ---------------------------------------------------------------------------


@router.get("/{document_id}/versions", response_model=list[DealDocumentVersionRead])
async def list_document_versions(
    document_id: UUID,
    db: DbSession,
    _user_id: AuthenticatedUserId,
    __: str = Depends(require_roles("admin", "analyst", "viewer")),
) -> list[DealDocumentVersionRead]:
    """List all version snapshots for a document."""
    _check_feature_flag()
    service = DealDocumentService(db)
    return await service.get_versions(document_id)


@router.post("/{document_id}/versions", response_model=DealDocumentVersionRead)
async def create_version_snapshot(
    document_id: UUID,
    db: DbSession,
    user_id: AuthenticatedUserId,
    reason: str = Query("manual_save"),
    change_summary: str | None = Query(None),
    _: str = Depends(require_roles("admin", "analyst")),
) -> DealDocumentVersionRead:
    """Create a manual version snapshot."""
    _check_feature_flag()
    service = DealDocumentService(db)
    try:
        return await service.create_version_snapshot(
            document_id, reason=reason, user_id=user_id, change_summary=change_summary
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.get("/{document_id}/compare", response_model=VersionDiff)
async def compare_versions(
    document_id: UUID,
    db: DbSession,
    _user_id: AuthenticatedUserId,
    v1: int = Query(..., ge=1),
    v2: int = Query(..., ge=1),
    __: str = Depends(require_roles("admin", "analyst", "viewer")),
) -> VersionDiff:
    """Compare two version snapshots of a document."""
    _check_feature_flag()
    service = DealDocumentService(db)
    return await service.compare_versions(document_id, v1=v1, v2=v2)


# ---------------------------------------------------------------------------
# Legal Hold
# ---------------------------------------------------------------------------


@router.post("/{document_id}/legal-hold", response_model=DealDocumentRead)
async def set_legal_hold(
    document_id: UUID,
    db: DbSession,
    user_id: AuthenticatedUserId,
    hold: bool = Query(True),
    _: str = Depends(require_roles("admin")),
) -> DealDocumentRead:
    """Set or release legal hold on a document. Admin only."""
    _check_feature_flag()
    service = DealDocumentService(db)
    try:
        return await service.set_legal_hold(document_id, hold=hold, user_id=user_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


# ---------------------------------------------------------------------------
# Audit Log
# ---------------------------------------------------------------------------


@router.get("/{document_id}/audit-log", response_model=dict)
async def get_document_audit_log(
    document_id: UUID,
    db: DbSession,
    _user_id: AuthenticatedUserId,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    __: str = Depends(require_roles("admin", "analyst")),
) -> dict:
    """Get the audit trail for a document."""
    _check_feature_flag()
    from munipal.services.document_audit_service import DocumentAuditService

    audit = DocumentAuditService(db)
    entries, total = await audit.get_log(document_id, skip=skip, limit=limit)
    return {
        "entries": [e.model_dump() for e in entries],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


# ---------------------------------------------------------------------------
# Model-to-Document Consistency
# ---------------------------------------------------------------------------


@router.post("/{document_id}/consistency-check", response_model=ConsistencyCheckResult)
async def check_document_consistency(
    document_id: UUID,
    data: ConsistencyCheckRequest,
    db: DbSession,
    user_id: AuthenticatedUserId,
    _: str = Depends(require_roles("admin", "analyst")),
) -> ConsistencyCheckResult:
    """
    Validate legal terms in a document against model parameters.

    This enforces model-to-document parity for covenant and waterfall terms.
    """
    _check_feature_flag()
    service = DocumentConsistencyService(db)
    try:
        return await service.check_document(
            document_id=document_id,
            request=data,
            actor_id=user_id,
        )
    except ValueError as e:
        detail = str(e)
        status_code = (
            status.HTTP_404_NOT_FOUND
            if detail.startswith("Document ") and detail.endswith(" not found")
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(status_code=status_code, detail=detail) from e


# ---------------------------------------------------------------------------
# Closing Checklist
# ---------------------------------------------------------------------------


@router.get("/checklist/{project_id}", response_model=list[ChecklistItemRead])
async def get_closing_checklist(
    project_id: UUID,
    db: DbSession,
    _user_id: AuthenticatedUserId,
    __: str = Depends(require_roles("admin", "analyst", "viewer")),
) -> list[ChecklistItemRead]:
    """Auto-generate a closing checklist from the document type registry."""
    _check_feature_flag()
    service = DealDocumentService(db)
    return await service.generate_closing_checklist(project_id)
