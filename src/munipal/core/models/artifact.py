"""
Artifact and Chunk models.

Per spec:
- Artifact: Any user-supplied input (docs, spreadsheets, images)
- Chunk: Immutable evidence units with provenance
"""

from uuid import uuid4

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, event, func, select
from sqlalchemy.orm import Mapped, mapped_column, relationship

from munipal.db.base import Base, TimestampMixin, UUIDType


class Artifact(Base, TimestampMixin):
    """User-supplied input document."""

    __tablename__ = "artifacts"

    id: Mapped[str] = mapped_column(
        UUIDType,
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

    # Processing status (chunking)
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    processing_error: Mapped[str | None] = mapped_column(Text)

    # Extraction status (fact extraction)
    is_extracted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_extraction_job_id: Mapped[str | None] = mapped_column(UUIDType)

    # Foreign keys
    project_id: Mapped[str] = mapped_column(
        UUIDType,
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
        UUIDType,
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
        UUIDType,
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


def _chunk_has_reviewed_fact(connection, chunk_id: str) -> bool:
    from munipal.core.models.fact import ExtractedFact, FactChunkAssociation

    count = connection.execute(
        select(func.count())
        .select_from(FactChunkAssociation)
        .join(ExtractedFact, ExtractedFact.id == FactChunkAssociation.fact_id)
        .where(
            FactChunkAssociation.chunk_id == str(chunk_id),
            ExtractedFact.review_status.in_(["approved", "rejected"]),
        )
    ).scalar_one()
    return bool(count)


def _artifact_has_reviewed_fact(connection, artifact_id: str) -> bool:
    from munipal.core.models.fact import ExtractedFact, FactChunkAssociation

    count = connection.execute(
        select(func.count())
        .select_from(Chunk)
        .join(FactChunkAssociation, FactChunkAssociation.chunk_id == Chunk.id)
        .join(ExtractedFact, ExtractedFact.id == FactChunkAssociation.fact_id)
        .where(
            Chunk.artifact_id == str(artifact_id),
            ExtractedFact.review_status.in_(["approved", "rejected"]),
        )
    ).scalar_one()
    return bool(count)


def _raise_provenance_mutation_error() -> None:
    raise ValueError(
        "Cannot mutate provenance for a reviewed fact; archive/supersede the fact instead"
    )


@event.listens_for(Chunk, "before_update")
def _prevent_reviewed_chunk_update(mapper, connection, target):  # noqa: ANN001
    if _chunk_has_reviewed_fact(connection, target.id):
        _raise_provenance_mutation_error()


@event.listens_for(Chunk, "before_delete")
def _prevent_reviewed_chunk_delete(mapper, connection, target):  # noqa: ANN001
    if _chunk_has_reviewed_fact(connection, target.id):
        _raise_provenance_mutation_error()


@event.listens_for(Artifact, "before_update")
def _prevent_reviewed_artifact_update(mapper, connection, target):  # noqa: ANN001
    if _artifact_has_reviewed_fact(connection, target.id):
        _raise_provenance_mutation_error()


@event.listens_for(Artifact, "before_delete")
def _prevent_reviewed_artifact_delete(mapper, connection, target):  # noqa: ANN001
    if _artifact_has_reviewed_fact(connection, target.id):
        _raise_provenance_mutation_error()
