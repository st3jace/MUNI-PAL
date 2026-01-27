"""
Playbook management endpoints.

Per spec: Playbook is a versioned configuration defining "bond-ready" criteria.
"""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from munipal.api.dependencies import AuthenticatedUserId, DbSession
from munipal.core.schemas.playbook import PlaybookDetail, PlaybookRead
from munipal.services.playbook_service import PlaybookService

router = APIRouter()


@router.get("/", response_model=list[PlaybookRead])
async def list_playbooks(
    db: DbSession,
    user_id: AuthenticatedUserId,
) -> list[PlaybookRead]:
    """List all active playbooks."""
    service = PlaybookService(db)
    return await service.list_active()


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
