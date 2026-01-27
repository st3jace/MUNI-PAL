"""
Playbook model.

Per spec: Playbook is a versioned configuration defining "bond-ready" criteria.
Contains schema paths, extractors, and checklist definitions.
"""

from uuid import uuid4

from sqlalchemy import Boolean, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from munipal.db.base import Base, TimestampMixin


class Playbook(Base, TimestampMixin):
    """Versioned configuration defining bond-ready criteria."""

    __tablename__ = "playbooks"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    # Identity
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    version: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    bond_archetype: Mapped[str] = mapped_column(String(255), nullable=False)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Configuration stored as JSON
    # These are the playbook's embedded definitions
    schema_paths: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        comment="List of SchemaPathDefinition objects",
    )
    extractors: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        comment="List of ExtractorDefinition objects",
    )
    checklist_items: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        comment="List of ChecklistItemDefinition objects",
    )
    readiness_config: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        comment="Readiness dimension weights and thresholds",
    )

    # Relationships
    projects = relationship("Project", back_populates="playbook")
