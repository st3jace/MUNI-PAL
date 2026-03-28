"""
Template and clause library routes for document management.

Feature-gated under document_management_v1.
"""

from typing import Annotated
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
    ClauseCreate,
    ClauseRead,
    ClauseRecommendation,
    ClauseRecommendationRequest,
    ClauseUpdate,
    TemplateCreate,
    TemplateRead,
    TemplateRenderRequest,
    TemplateRenderResult,
    TemplateUpdate,
)
from munipal.services.template_service import TemplateService

router = APIRouter()


def _check_feature_flag() -> None:
    if not get_settings().document_management_v1:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document management is not enabled",
        )


@router.post("/", response_model=TemplateRead, status_code=status.HTTP_201_CREATED)
async def create_template(
    data: TemplateCreate,
    db: DbSession,
    tenant_id: CurrentTenantId,
    _user_id: AuthenticatedUserId,
    _: str = Depends(require_roles("admin", "analyst")),
) -> TemplateRead:
    """Create a template in the tenant-scoped library."""
    _check_feature_flag()
    service = TemplateService(db)
    try:
        return await service.create_template(data, tenant_id=tenant_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/", response_model=dict)
async def list_templates(
    db: DbSession,
    tenant_id: CurrentTenantId,
    _user_id: AuthenticatedUserId,
    document_type_id: Annotated[UUID | None, Query()] = None,
    jurisdiction: str | None = Query(None),
    active_only: bool = Query(True),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    _: str = Depends(require_roles("admin", "analyst", "viewer")),
) -> dict:
    """List templates with optional filters."""
    _check_feature_flag()
    service = TemplateService(db)
    templates, total = await service.list_templates(
        tenant_id=tenant_id,
        document_type_id=document_type_id,
        jurisdiction=jurisdiction,
        active_only=active_only,
        skip=skip,
        limit=limit,
    )
    return {
        "templates": [t.model_dump() for t in templates],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.post("/clauses", response_model=ClauseRead, status_code=status.HTTP_201_CREATED)
async def create_clause(
    data: ClauseCreate,
    db: DbSession,
    tenant_id: CurrentTenantId,
    _user_id: AuthenticatedUserId,
    _: str = Depends(require_roles("admin", "analyst")),
) -> ClauseRead:
    """Create a clause entry in the reusable clause library."""
    _check_feature_flag()
    service = TemplateService(db)
    try:
        return await service.create_clause(data, tenant_id=tenant_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/clauses", response_model=dict)
async def list_clauses(
    db: DbSession,
    tenant_id: CurrentTenantId,
    _user_id: AuthenticatedUserId,
    template_id: Annotated[UUID | None, Query()] = None,
    category: str | None = Query(None),
    jurisdiction: str | None = Query(None),
    text_query: str | None = Query(None),
    active_only: bool = Query(True),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    _: str = Depends(require_roles("admin", "analyst", "viewer")),
) -> dict:
    """List clause library entries."""
    _check_feature_flag()
    service = TemplateService(db)
    clauses, total = await service.list_clauses(
        tenant_id=tenant_id,
        template_id=template_id,
        category=category,
        jurisdiction=jurisdiction,
        text_query=text_query,
        active_only=active_only,
        skip=skip,
        limit=limit,
    )
    return {
        "clauses": [clause.model_dump() for clause in clauses],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.post("/clauses/recommendations", response_model=list[ClauseRecommendation])
async def recommend_clauses(
    request: ClauseRecommendationRequest,
    db: DbSession,
    tenant_id: CurrentTenantId,
    _user_id: AuthenticatedUserId,
    _: str = Depends(require_roles("admin", "analyst", "viewer")),
) -> list[ClauseRecommendation]:
    """Recommend clauses based on deal structure and feature signals."""
    _check_feature_flag()
    service = TemplateService(db)
    return await service.recommend_clauses(request, tenant_id=tenant_id)


@router.get("/clauses/{clause_id}", response_model=ClauseRead)
async def get_clause(
    clause_id: UUID,
    db: DbSession,
    _user_id: AuthenticatedUserId,
    _: str = Depends(require_roles("admin", "analyst", "viewer")),
) -> ClauseRead:
    """Get a clause by ID."""
    _check_feature_flag()
    service = TemplateService(db)
    clause = await service.get_clause(clause_id)
    if not clause:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Clause {clause_id} not found",
        )
    return clause


@router.patch("/clauses/{clause_id}", response_model=ClauseRead)
async def update_clause(
    clause_id: UUID,
    data: ClauseUpdate,
    db: DbSession,
    _user_id: AuthenticatedUserId,
    _: str = Depends(require_roles("admin", "analyst")),
) -> ClauseRead:
    """Update a clause entry."""
    _check_feature_flag()
    service = TemplateService(db)
    clause = await service.update_clause(clause_id, data)
    if not clause:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Clause {clause_id} not found",
        )
    return clause


@router.get("/{template_id}", response_model=TemplateRead)
async def get_template(
    template_id: UUID,
    db: DbSession,
    _user_id: AuthenticatedUserId,
    _: str = Depends(require_roles("admin", "analyst", "viewer")),
) -> TemplateRead:
    """Get a template by ID."""
    _check_feature_flag()
    service = TemplateService(db)
    template = await service.get_template(template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template {template_id} not found",
        )
    return template


@router.patch("/{template_id}", response_model=TemplateRead)
async def update_template(
    template_id: UUID,
    data: TemplateUpdate,
    db: DbSession,
    _user_id: AuthenticatedUserId,
    _: str = Depends(require_roles("admin", "analyst")),
) -> TemplateRead:
    """Update a template entry."""
    _check_feature_flag()
    service = TemplateService(db)
    template = await service.update_template(template_id, data)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template {template_id} not found",
        )
    return template


@router.post("/{template_id}/render", response_model=TemplateRenderResult)
async def render_template(
    template_id: UUID,
    data: TemplateRenderRequest,
    db: DbSession,
    _user_id: AuthenticatedUserId,
    _: str = Depends(require_roles("admin", "analyst")),
) -> TemplateRenderResult:
    """Render a template to TipTap JSON using input variables."""
    _check_feature_flag()
    service = TemplateService(db)
    try:
        return await service.render_template(template_id, data)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
