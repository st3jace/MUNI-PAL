"""
Playbook service - manages playbook configuration and seeding.

Per spec: Playbook is a versioned configuration defining "bond-ready" criteria.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from munipal.core.models import Playbook
from munipal.core.schemas.playbook import PlaybookDetail, PlaybookRead


class PlaybookService:
    """Service for playbook management."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_default(self) -> PlaybookRead | None:
        """Get the default active playbook."""
        result = await self.db.execute(
            select(Playbook).where(Playbook.is_default == True, Playbook.is_active == True)
        )
        playbook = result.scalar_one_or_none()
        if not playbook:
            return None
        return self._to_read_schema(playbook)

    async def get(self, playbook_id: UUID) -> PlaybookDetail | None:
        """Get a playbook by ID with full configuration."""
        playbook = await self.db.get(Playbook, str(playbook_id))
        if not playbook:
            return None
        return self._to_detail_schema(playbook)

    async def list(self, include_inactive: bool = False) -> list[PlaybookRead]:
        """List playbooks, optionally including inactive records."""
        query = select(Playbook)
        if not include_inactive:
            query = query.where(Playbook.is_active == True)

        result = await self.db.execute(query.order_by(Playbook.name))
        playbooks = result.scalars().all()
        return [self._to_read_schema(p) for p in playbooks]

    async def list_active(self) -> list[PlaybookRead]:
        """Backwards-compatible helper for active-only listing."""
        return await self.list(include_inactive=False)

    async def seed_ucs_playbook(self) -> PlaybookRead:
        """
        Seed the UCS CAB+SLB playbook if it doesn't exist.

        Returns the playbook (existing or newly created).
        """
        from munipal.services.playbook_data import UCS_PLAYBOOK_CONFIG

        # Check if already exists
        result = await self.db.execute(
            select(Playbook).where(
                Playbook.name == UCS_PLAYBOOK_CONFIG["name"],
                Playbook.version == UCS_PLAYBOOK_CONFIG["version"],
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            return self._to_read_schema(existing)

        # Create new playbook
        playbook = Playbook(
            name=UCS_PLAYBOOK_CONFIG["name"],
            version=UCS_PLAYBOOK_CONFIG["version"],
            description=UCS_PLAYBOOK_CONFIG["description"],
            bond_archetype=UCS_PLAYBOOK_CONFIG["bond_archetype"],
            is_active=True,
            is_default=True,
            schema_paths=UCS_PLAYBOOK_CONFIG["schema_paths"],
            extractors=UCS_PLAYBOOK_CONFIG["extractors"],
            checklist_items=UCS_PLAYBOOK_CONFIG["checklist_items"],
            readiness_config=UCS_PLAYBOOK_CONFIG["readiness_config"],
        )

        self.db.add(playbook)
        await self.db.flush()
        await self.db.refresh(playbook)

        return self._to_read_schema(playbook)

    def _to_read_schema(self, playbook: Playbook) -> PlaybookRead:
        """Convert to read schema."""
        return PlaybookRead(
            id=UUID(playbook.id),
            name=playbook.name,
            version=playbook.version,
            description=playbook.description,
            bond_archetype=playbook.bond_archetype,
            is_active=playbook.is_active,
            is_default=playbook.is_default,
            schema_path_count=len(playbook.schema_paths) if playbook.schema_paths else 0,
            extractor_count=len(playbook.extractors) if playbook.extractors else 0,
            checklist_item_count=len(playbook.checklist_items) if playbook.checklist_items else 0,
            created_at=playbook.created_at,
            updated_at=playbook.updated_at,
        )

    def _to_detail_schema(self, playbook: Playbook) -> PlaybookDetail:
        """Convert to detail schema with full configuration."""
        return PlaybookDetail(
            id=UUID(playbook.id),
            name=playbook.name,
            version=playbook.version,
            description=playbook.description,
            bond_archetype=playbook.bond_archetype,
            is_active=playbook.is_active,
            is_default=playbook.is_default,
            schema_path_count=len(playbook.schema_paths) if playbook.schema_paths else 0,
            extractor_count=len(playbook.extractors) if playbook.extractors else 0,
            checklist_item_count=len(playbook.checklist_items) if playbook.checklist_items else 0,
            created_at=playbook.created_at,
            updated_at=playbook.updated_at,
            schema_paths=playbook.schema_paths or [],
            extractors=playbook.extractors or [],
            checklist_items=playbook.checklist_items or [],
        )
