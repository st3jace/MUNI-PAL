"""
Disclosure document endpoints for WP7 - Disclosure Synthesis Engine.

Per spec: WP7 transforms the skeletal "Disclosure Outline" into a substantive
disclosure document by synthesizing extracted facts into coherent, disclosure-ready prose.
"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from munipal.api.dependencies import AuthenticatedUserId, require_auth
from munipal.core.schemas.disclosure import (
    DisclosureDocumentRead,
    DisclosureDocumentSummary,
    DisclosureSectionPreview,
    GenerateDisclosureRequest,
    GenerateDisclosureResponse,
)
from munipal.db.session import get_async_session
from munipal.services.audit_service import AuditService
from munipal.services.disclosure_service import DisclosureSynthesisService

router = APIRouter(dependencies=[Depends(require_auth)])


def get_disclosure_service(
    db: AsyncSession = Depends(get_async_session),
) -> DisclosureSynthesisService:
    """Dependency to get DisclosureSynthesisService instance."""
    return DisclosureSynthesisService(db)


# -----------------------------------------------------------------------------
# Document Generation
# -----------------------------------------------------------------------------


@router.post("/generate", response_model=GenerateDisclosureResponse)
async def generate_disclosure_document(
    request: GenerateDisclosureRequest,
    service: DisclosureSynthesisService = Depends(get_disclosure_service),
) -> GenerateDisclosureResponse:
    """
    Generate a disclosure document for a project.

    Per WP7 spec: Synthesizes content from extracted facts using templates.
    Every sentence traces to fact(s) or is a templated qualifier.
    TBD markers are inserted for insufficient evidence.
    """
    try:
        document = await service.generate_document(
            project_id=request.project_id,
            section_ids=request.sections,
            force_regenerate=request.force_regenerate,
        )
        return GenerateDisclosureResponse(
            document_id=UUID(document.id),
            status="completed",
            message=f"Document generated with {document.completeness_score:.1%} completeness",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


# -----------------------------------------------------------------------------
# Document Retrieval
# -----------------------------------------------------------------------------


@router.get("/{document_id}", response_model=DisclosureDocumentRead)
async def get_disclosure_document(
    document_id: UUID,
    service: DisclosureSynthesisService = Depends(get_disclosure_service),
) -> DisclosureDocumentRead:
    """Get a disclosure document by ID."""
    document = await service.get_document(document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Disclosure document {document_id} not found",
        )
    return service.document_to_read_schema(document)


@router.get("/", response_model=dict[str, Any])
async def list_disclosure_documents(
    project_id: UUID,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: DisclosureSynthesisService = Depends(get_disclosure_service),
) -> dict[str, Any]:
    """List disclosure documents for a project."""
    documents, total = await service.list_documents(
        project_id=project_id,
        limit=limit,
        offset=offset,
    )

    return {
        "documents": [
            DisclosureDocumentSummary(
                id=UUID(d.id),
                project_id=UUID(d.project_id),
                version=d.version,
                completeness_score=d.completeness_score,
                is_complete=d.is_complete,
                section_count=len(d.sections) if hasattr(d, "sections") else 0,
                tbd_count=len(d.tbd_items) if hasattr(d, "tbd_items") else 0,
                created_at=d.created_at,
            )
            for d in documents
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/project/{project_id}/latest", response_model=DisclosureDocumentRead | None)
async def get_latest_disclosure_document(
    project_id: UUID,
    service: DisclosureSynthesisService = Depends(get_disclosure_service),
) -> DisclosureDocumentRead | None:
    """Get the latest disclosure document for a project."""
    document = await service.get_latest_document(project_id)
    if not document:
        return None
    return service.document_to_read_schema(document)


# -----------------------------------------------------------------------------
# Section Preview
# -----------------------------------------------------------------------------


@router.get("/preview/section/{section_id}", response_model=DisclosureSectionPreview | None)
async def preview_disclosure_section(
    section_id: str,
    project_id: UUID,
    service: DisclosureSynthesisService = Depends(get_disclosure_service),
) -> DisclosureSectionPreview | None:
    """
    Preview what a disclosure section would contain.

    Returns information about required facts, available facts,
    and estimated confidence without generating the full document.
    """
    return await service.get_section_preview(project_id, section_id)


# -----------------------------------------------------------------------------
# Export
# -----------------------------------------------------------------------------


@router.get("/{document_id}/export")
async def export_disclosure_document(
    document_id: UUID,
    user_id: AuthenticatedUserId,
    format: str = Query("md", pattern="^(md|pdf|docx)$"),
    service: DisclosureSynthesisService = Depends(get_disclosure_service),
) -> dict[str, Any]:
    """
    Export a disclosure document in the specified format.

    Supported formats: md (Markdown), pdf, docx
    """
    document = await service.get_document(document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Disclosure document {document_id} not found",
        )

    # For now, return markdown content
    # PDF/DOCX generation would require additional libraries
    if format == "md":
        content = []
        for section in sorted(document.sections, key=lambda s: s.section_order):
            content.append(section.content_md)
        AuditService.emit_event(
            actor_id=user_id,
            action="export_disclosure_markdown",
            target_type="disclosure_document",
            target_id=str(document_id),
            project_id=str(document.project_id),
        )
        return {
            "format": format,
            "filename": f"disclosure_v{document.version}.md",
            "content": "\n\n".join(content),
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=f"Export format '{format}' not yet implemented",
        )
