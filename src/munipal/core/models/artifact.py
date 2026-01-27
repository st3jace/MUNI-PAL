"""
Artifact and Chunk models.

Per spec:
- Artifact: Any user-supplied input (docs, spreadsheets, images)
- Chunk: Immutable evidence units with provenance
"""

from uuid import uuid4

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from munipal.db.base import Base, TimestampMixin


class Artifact(Base, TimestampMixin):
    """User-supplied input document."""

    __tablename__ = "artifacts"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    # File metadata
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(255))
    artifact_type: Mapped[str] = mapped_column(String(20), nullable=False)  # pdf, docx, xlsx, etc.
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)

    # Processing status
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    processing_error: Mapped[str | None] = mapped_column(Text)

    # Foreign keys
    project_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("projects.id"),
        nullable=False,
        index=True,
    )

    # Relationships
    project = relationship("Project", back_populates="artifacts")
    chunks = relationship("Chunk", back_populates="artifact", cascade="all, delete-orphan")


class Chunk(Base, TimestampMixin):
    """
    Immutable evidence unit extracted from an artifact.

    Per spec: Chunks are IMMUTABLE after creation.
    """

    __tablename__ = "chunks"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    # Location
    chunk_type: Mapped[str] = mapped_column(String(20), nullable=False)  # page, sheet, section
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    page_number: Mapped[int | None] = mapped_column(Integer)
    sheet_name: Mapped[str | None] = mapped_column(String(100))
    section_title: Mapped[str | None] = mapped_column(String(255))

    # Content
    text_content: Mapped[str | None] = mapped_column(Text)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)  # SHA-256
    has_image: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Foreign keys
    artifact_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("artifacts.id"),
        nullable=False,
        index=True,
    )

    # Relationships
    artifact = relationship("Artifact", back_populates="chunks")
    # Facts that cite this chunk (many-to-many through fact_chunks)
    fact_citations = relationship(
        "FactChunkAssociation",
        back_populates="chunk",
        cascade="all, delete-orphan",
    )
