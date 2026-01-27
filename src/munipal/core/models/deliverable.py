"""
DeliverablePack model.

Per spec: DeliverablePack is the generated advisor-ready output bundle.
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from munipal.db.base import Base, TimestampMixin


class DeliverablePack(Base, TimestampMixin):
    """Generated advisor-ready output bundle."""

    __tablename__ = "deliverable_packs"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    # Metadata
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    generated_for: Mapped[str] = mapped_column(String(255), nullable=False)

    # Generation status
    is_complete: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    generation_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    generation_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Configuration
    include_sections: Mapped[list] = mapped_column(
        JSON, nullable=False, default=lambda: [1, 2, 3, 4, 5, 6, 7, 8, 9]
    )
    include_appendices: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Content (sections stored as JSON)
    sections: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    # Snapshot metrics at generation time
    facts_included_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    readiness_score_at_generation: Mapped[float | None] = mapped_column(Float)

    # Warnings
    warnings: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    # Storage
    pdf_storage_path: Mapped[str | None] = mapped_column(String(500))

    # Celery task tracking
    celery_task_id: Mapped[str | None] = mapped_column(String(255))

    # Foreign keys
    project_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("projects.id"),
        nullable=False,
        index=True,
    )

    # Relationships
    project = relationship("Project", back_populates="deliverable_packs")
