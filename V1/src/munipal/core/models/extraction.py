"""
ExtractionJob model.

Per spec: ExtractionJob is the async wrapper for AI and parsing work.
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from munipal.db.base import Base, TimestampMixin, UUIDType


class ExtractionJob(Base, TimestampMixin):
    """Async wrapper for AI extraction work."""

    __tablename__ = "extraction_jobs"

    id: Mapped[str] = mapped_column(
        UUIDType,
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    # Job configuration
    job_type: Mapped[str] = mapped_column(String(100), nullable=False)
    target_schema_paths: Mapped[list] = mapped_column(
        JSON, nullable=False, default=list
    )

    # Artifact scope
    artifact_ids: Mapped[list] = mapped_column(JSON, nullable=False)
    chunk_ids: Mapped[list | None] = mapped_column(JSON)

    # Status
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="queued", index=True
    )  # queued, running, completed, failed
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Progress
    total_chunks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    processed_chunks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    facts_extracted: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Error handling
    error_message: Mapped[str | None] = mapped_column(Text)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Celery task tracking
    celery_task_id: Mapped[str | None] = mapped_column(String(255))

    # Foreign keys
    project_id: Mapped[str] = mapped_column(
        UUIDType,
        ForeignKey("projects.id"),
        nullable=False,
        index=True,
    )

    # Relationships
    project = relationship("Project", back_populates="extraction_jobs")
    facts = relationship("ExtractedFact", back_populates="extraction_job")
