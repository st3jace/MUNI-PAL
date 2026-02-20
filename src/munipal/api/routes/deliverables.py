"""
Deliverable pack management endpoints.

Per spec (WP6): Warm Handoff Pack Assembly
- Generate advisor-ready deliverable bundles
- 9 sections per playbook
- Include mandatory disclaimer
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from munipal.api.dependencies import AuthenticatedUserId, require_auth
from munipal.core.schemas.deliverable import (
    DeliverablePackCreate,
    DeliverablePackRead,
    DeliverablePackSummary,
)
from munipal.db.session import get_async_session
from munipal.services.audit_service import AuditService
from munipal.services.deliverable_service import DeliverableService
from munipal.workers.tasks.deliverable_tasks import export_pack_pdf, generate_pack

router = APIRouter(dependencies=[Depends(require_auth)])


def get_deliverable_service(
    db: AsyncSession = Depends(get_async_session),
) -> DeliverableService:
    """Dependency to get DeliverableService instance."""
    return DeliverableService(db)


# -----------------------------------------------------------------------------
# Pack Management
# -----------------------------------------------------------------------------


@router.post("/", response_model=dict, status_code=status.HTTP_202_ACCEPTED)
async def create_pack(
    pack_data: DeliverablePackCreate,
    sync: bool = Query(False, description="Generate synchronously (for testing without Celery)"),
    service: DeliverableService = Depends(get_deliverable_service),
) -> dict:
    """
    Create and generate a new deliverable pack.

    By default, the pack will be generated asynchronously via Celery.
    Use sync=true to generate synchronously (useful for testing without Celery).
    Poll GET /{pack_id} to check generation status.

    Per playbook, the pack has 9 sections:
    1. Cover
    2. Deal Overview Memo
    3. Readiness & Gap Report
    4. Checklist Status
    5. Evidence Index
    6. Assumption Register
    7. Financial Model Outputs
    8. SLB KPI Brief
    9. Disclosure Outline
    """
    pack = await service.create_pack(
        project_id=pack_data.project_id,
        title=pack_data.title,
        generated_for=pack_data.generated_for,
        include_sections=pack_data.include_sections,
        include_appendices=pack_data.include_appendices,
    )

    if sync:
        # Generate synchronously (for testing without Celery)
        result = await service.generate_pack(pack.id)
        return {
            "pack_id": str(pack.id),
            "status": "completed" if result.is_complete else "failed",
            "sections_generated": len(result.sections) if result.sections else 0,
            "facts_included": result.facts_included_count,
            "message": "Pack generated synchronously.",
        }
    else:
        # Queue async generation via Celery
        task = generate_pack.delay(pack.id)
        return {
            "pack_id": pack.id,
            "status": "queued",
            "task_id": task.id,
            "message": "Pack generation queued. Poll GET /deliverables/{pack_id} for status.",
        }


@router.get("/", response_model=list[DeliverablePackSummary])
async def list_packs(
    project_id: UUID,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: DeliverableService = Depends(get_deliverable_service),
) -> list[DeliverablePackSummary]:
    """
    List deliverable packs for a project.

    Returns pack summaries ordered by creation date (newest first).
    """
    packs = await service.list_packs(project_id, limit, offset)

    return [
        DeliverablePackSummary(
            id=UUID(p.id),
            title=p.title,
            generated_for=p.generated_for,
            is_complete=p.is_complete,
            created_at=p.created_at,
            generation_completed_at=p.generation_completed_at,
            readiness_score_at_generation=p.readiness_score_at_generation,
        )
        for p in packs
    ]


@router.get("/{pack_id}", response_model=DeliverablePackRead)
async def get_pack(
    pack_id: UUID,
    service: DeliverableService = Depends(get_deliverable_service),
) -> DeliverablePackRead:
    """
    Get a deliverable pack by ID.

    Returns full pack content if generation is complete,
    or status information if still in progress.
    """
    pack = await service.get_pack(pack_id)
    if not pack:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pack {pack_id} not found",
        )

    return DeliverablePackRead(
        id=UUID(pack.id),
        project_id=UUID(pack.project_id),
        title=pack.title,
        generated_for=pack.generated_for,
        is_complete=pack.is_complete,
        generation_started_at=pack.generation_started_at,
        generation_completed_at=pack.generation_completed_at,
        sections=pack.sections,
        facts_included_count=pack.facts_included_count,
        readiness_score_at_generation=pack.readiness_score_at_generation,
        warnings=pack.warnings,
        created_at=pack.created_at,
        updated_at=pack.updated_at,
    )


@router.get("/{pack_id}/status", response_model=dict)
async def get_pack_status(
    pack_id: UUID,
    service: DeliverableService = Depends(get_deliverable_service),
) -> dict:
    """
    Get generation status for a pack.

    Lightweight endpoint for polling during async generation.
    """
    pack = await service.get_pack(pack_id)
    if not pack:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pack {pack_id} not found",
        )

    if pack.is_complete:
        status_str = "completed"
    elif pack.generation_started_at:
        status_str = "generating"
    else:
        status_str = "queued"

    return {
        "pack_id": str(pack_id),
        "status": status_str,
        "is_complete": pack.is_complete,
        "generation_started_at": pack.generation_started_at,
        "generation_completed_at": pack.generation_completed_at,
        "sections_count": len(pack.sections) if pack.sections else 0,
        "warnings_count": len(pack.warnings) if pack.warnings else 0,
    }


# -----------------------------------------------------------------------------
# Regeneration
# -----------------------------------------------------------------------------


@router.post("/{pack_id}/regenerate", response_model=dict, status_code=status.HTTP_202_ACCEPTED)
async def regenerate_pack(
    pack_id: UUID,
    sync: bool = Query(False, description="Regenerate synchronously"),
    service: DeliverableService = Depends(get_deliverable_service),
) -> dict:
    """
    Regenerate a deliverable pack.

    Useful after new facts have been approved or reviewed.
    Use sync=true for synchronous regeneration.
    """
    pack = await service.get_pack(pack_id)
    if not pack:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pack {pack_id} not found",
        )

    if sync:
        # Regenerate synchronously
        result = await service.generate_pack(pack_id)
        return {
            "pack_id": str(pack_id),
            "status": "completed" if result.is_complete else "failed",
            "sections_generated": len(result.sections) if result.sections else 0,
            "message": "Pack regenerated synchronously.",
        }

    # Queue regeneration
    task = generate_pack.delay(str(pack_id))

    return {
        "pack_id": str(pack_id),
        "status": "queued",
        "task_id": task.id,
        "message": "Pack regeneration queued.",
    }


# -----------------------------------------------------------------------------
# Export
# -----------------------------------------------------------------------------


@router.post("/{pack_id}/export/pdf", response_model=dict, status_code=status.HTTP_202_ACCEPTED)
async def export_pdf(
    pack_id: UUID,
    user_id: AuthenticatedUserId,
    service: DeliverableService = Depends(get_deliverable_service),
) -> dict:
    """
    Export a deliverable pack to PDF format.

    Pack must be fully generated before export.
    """
    pack = await service.get_pack(pack_id)
    if not pack:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pack {pack_id} not found",
        )

    if not pack.is_complete:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pack generation not complete. Cannot export.",
        )

    task = export_pack_pdf.delay(str(pack_id))
    AuditService.emit_event(
        actor_id=user_id,
        action="export_deliverable_pack_pdf",
        target_type="deliverable_pack",
        target_id=str(pack_id),
        project_id=str(pack.project_id),
    )

    return {
        "pack_id": str(pack_id),
        "status": "queued",
        "task_id": task.id,
        "message": "PDF export queued.",
    }


@router.get("/{pack_id}/export/markdown", response_model=dict)
async def export_markdown(
    pack_id: UUID,
    user_id: AuthenticatedUserId,
    service: DeliverableService = Depends(get_deliverable_service),
) -> dict:
    """
    Export pack content as combined markdown.

    Returns all sections concatenated into a single markdown document.
    """
    pack = await service.get_pack(pack_id)
    if not pack:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pack {pack_id} not found",
        )

    if not pack.is_complete:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pack generation not complete.",
        )

    # Combine sections into single markdown
    sections = pack.sections or []
    combined = []

    for section in sorted(sections, key=lambda s: s.get("section_number", 0)):
        combined.append(section.get("content", ""))
        combined.append("\n\n---\n\n")

    # Add disclaimer
    disclaimer = (
        "## Disclaimer\n\n"
        "This document is provided for informational purposes only and does not "
        "constitute investment advice, a recommendation to purchase or sell securities, "
        "or an offer or solicitation of an offer to buy or sell any securities. "
        "The information contained herein has been prepared from sources believed to be "
        "reliable but is not guaranteed as to accuracy or completeness. All facts and "
        "figures are subject to verification by qualified professionals."
    )
    combined.append(disclaimer)
    AuditService.emit_event(
        actor_id=user_id,
        action="export_deliverable_pack_markdown",
        target_type="deliverable_pack",
        target_id=str(pack_id),
        project_id=str(pack.project_id),
    )

    return {
        "pack_id": str(pack_id),
        "title": pack.title,
        "format": "markdown",
        "content": "\n".join(combined),
    }


# -----------------------------------------------------------------------------
# Section Access
# -----------------------------------------------------------------------------


@router.get("/{pack_id}/sections/{section_number}", response_model=dict)
async def get_section(
    pack_id: UUID,
    section_number: int,
    service: DeliverableService = Depends(get_deliverable_service),
) -> dict:
    """
    Get a specific section from a deliverable pack.
    """
    pack = await service.get_pack(pack_id)
    if not pack:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pack {pack_id} not found",
        )

    sections = pack.sections or []
    for section in sections:
        if section.get("section_number") == section_number:
            return section

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Section {section_number} not found in pack",
    )
