"""
Playbook management endpoints.

Per spec: Playbook is a versioned configuration defining "bond-ready" criteria.
"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from munipal.api.dependencies import AuthenticatedUserId, DbSession
from munipal.core.schemas.playbook import PlaybookDetail, PlaybookRead
from munipal.services.playbook_service import PlaybookService
from munipal.services.playbook_data import (
    get_schema_path_metadata,
    get_all_schema_paths_with_metadata,
    SCHEMA_PATH_METADATA,
)

router = APIRouter()


@router.get("/", response_model=dict[str, list[PlaybookRead]])
async def list_playbooks(
    db: DbSession,
    user_id: AuthenticatedUserId,
    include_inactive: bool = Query(False, description="Include inactive playbooks"),
) -> dict[str, list[PlaybookRead]]:
    """List playbooks."""
    service = PlaybookService(db)
    playbooks = await service.list(include_inactive=include_inactive)
    return {"playbooks": playbooks}


@router.get("/default", response_model=PlaybookRead)
async def get_default_playbook(
    db: DbSession,
    user_id: AuthenticatedUserId,
) -> PlaybookRead:
    """Get the default active playbook."""
    service = PlaybookService(db)
    playbook = await service.get_default()

    if not playbook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No default playbook configured. Run POST /api/v1/playbooks/seed to initialize.",
        )

    return playbook


@router.get("/{playbook_id}", response_model=PlaybookDetail)
async def get_playbook(
    playbook_id: UUID,
    db: DbSession,
    user_id: AuthenticatedUserId,
) -> PlaybookDetail:
    """Get a playbook by ID with full configuration details."""
    service = PlaybookService(db)
    playbook = await service.get(playbook_id)

    if not playbook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Playbook {playbook_id} not found",
        )

    return playbook


@router.get("/{playbook_id}/schema-paths", response_model=dict[str, Any], include_in_schema=False)
async def get_playbook_schema_paths(
    playbook_id: UUID,
    db: DbSession,
    user_id: AuthenticatedUserId,
    criticality: str | None = Query(None, description="Optional criticality filter"),
) -> dict[str, Any]:
    """
    Legacy endpoint returning schema paths scoped to a playbook.
    """
    service = PlaybookService(db)
    playbook = await service.get(playbook_id)
    if not playbook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Playbook {playbook_id} not found",
        )

    paths: dict[str, Any] = {}
    for schema_path in playbook.schema_paths:
        path = schema_path.path
        item = schema_path.model_dump()
        if criticality and item.get("criticality") != criticality:
            continue
        paths[path] = item

    return {"schema_paths": paths}


@router.get("/{playbook_id}/checklist-items", response_model=dict[str, Any], include_in_schema=False)
async def get_playbook_checklist_items(
    playbook_id: UUID,
    db: DbSession,
    user_id: AuthenticatedUserId,
) -> dict[str, Any]:
    """
    Legacy endpoint returning checklist definitions scoped to a playbook.
    """
    service = PlaybookService(db)
    playbook = await service.get(playbook_id)
    if not playbook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Playbook {playbook_id} not found",
        )

    return {
        "checklist_items": [item.model_dump() for item in playbook.checklist_items],
    }


@router.post("/seed", response_model=PlaybookRead, status_code=status.HTTP_201_CREATED)
async def seed_playbook(
    db: DbSession,
    user_id: AuthenticatedUserId,
) -> PlaybookRead:
    """
    Seed the default UCS CAB+SLB playbook.

    This endpoint initializes the system with the UCS Bond Intelligence
    Configuration Playbook v0.2. Safe to call multiple times - will return
    existing playbook if already seeded.
    """
    service = PlaybookService(db)
    return await service.seed_ucs_playbook()


# -----------------------------------------------------------------------------
# Schema Path Metadata Endpoints
# -----------------------------------------------------------------------------


@router.get("/schema-paths", response_model=list[dict[str, Any]])
async def list_schema_paths() -> list[dict[str, Any]]:
    """
    List all schema paths with their metadata.

    Returns enriched schema path definitions including:
    - path: The dotted schema path (e.g., 'project.canonicaldescription')
    - display_name: Human-readable name
    - value_type: Expected data type (string, number, currency, etc.)
    - criticality: Importance tier (critical, material, secondary)
    - description: Full explanation of what this field represents
    - short_description: Brief one-line summary
    - guidance: Instructions for what content is expected
    - example: Sample acceptable value
    - who_needs_it: List of stakeholders who require this information

    This endpoint is used by the frontend to provide context and guidance
    to users entering or reviewing facts.
    """
    return get_all_schema_paths_with_metadata()


@router.get("/schema-paths/{schema_path:path}", response_model=dict[str, Any])
async def get_schema_path_detail(
    schema_path: str,
) -> dict[str, Any]:
    """
    Get detailed metadata for a specific schema path.

    Returns comprehensive information about the schema path including:
    - description: Full explanation of what this field represents in bond/finance terms
    - short_description: Brief one-line summary
    - guidance: Instructions for what content is expected
    - example: Sample acceptable value
    - who_needs_it: List of stakeholders who require this information

    This is useful for providing contextual help when users click on
    schema paths in the Facts Review, Checklist, or other sections.
    """
    metadata = get_schema_path_metadata(schema_path)
    if not metadata:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schema path '{schema_path}' not found in metadata registry",
        )

    # Include the path in the response
    result = {"path": schema_path, **metadata}
    return result


@router.get("/schema-paths-batch", response_model=dict[str, dict[str, Any]])
async def get_schema_paths_batch(
    paths: list[str] = Query(..., description="List of schema paths to retrieve"),
) -> dict[str, dict[str, Any]]:
    """
    Get metadata for multiple schema paths in a single request.

    Useful for efficiently loading metadata for all paths shown on a page.
    Returns a dictionary keyed by schema path.

    Paths that don't exist in the metadata registry are omitted from the response.
    """
    result = {}
    for path in paths:
        metadata = get_schema_path_metadata(path)
        if metadata:
            result[path] = {"path": path, **metadata}
    return result
