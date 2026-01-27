"""
ExtractedFact and related models.

Per spec: ExtractedFact is THE CORE PRIMITIVE - structured, reviewable claim
with full provenance tracing.
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from munipal.db.base import Base, TimestampMixin


class ExtractedFact(Base, TimestampMixin):
    """
    THE CORE PRIMITIVE.

    A structured, reviewable claim about the project with full provenance.
    """

    __tablename__ = "extracted_facts"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    # Schema mapping
    schema_path: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    criticality: Mapped[str] = mapped_column(
        String(20), nullable=False, default="secondary"
    )  # critical, material, secondary

    # Value
    value: Mapped[dict] = mapped_column(JSON, nullable=False)  # Stored as JSON for flexibility
    value_type: Mapped[str] = mapped_column(String(50), nullable=False, default="string")
    unit: Mapped[str | None] = mapped_column(String(50))

    # Confidence
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    confidence_rationale: Mapped[str | None] = mapped_column(Text)

    # Review status
    review_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", index=True
    )  # pending, approved, rejected, needs_revision
    reviewed_by: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    review_note: Mapped[str | None] = mapped_column(Text)

    # Original value if corrected during review
    original_value: Mapped[dict | None] = mapped_column(JSON)

    # Foreign keys
    project_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("projects.id"),
        nullable=False,
        index=True,
    )
    extraction_job_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("extraction_jobs.id"),
        nullable=False,
    )

    # Relationships
    project = relationship("Project", back_populates="extracted_facts")
    extraction_job = relationship("ExtractionJob", back_populates="facts")
    reviewer = relationship("User", foreign_keys=[reviewed_by])
    revisions = relationship(
        "FactRevision", back_populates="fact", cascade="all, delete-orphan"
    )
    # Provenance - which chunks this fact was extracted from
    source_chunks = relationship(
        "FactChunkAssociation",
        back_populates="fact",
        cascade="all, delete-orphan",
    )
    evidence_links = relationship(
        "EvidenceLink", back_populates="fact", cascade="all, delete-orphan"
    )


class FactChunkAssociation(Base):
    """
    Association table linking facts to their source chunks.

    Per spec: Every fact must trace back to source evidence.
    """

    __tablename__ = "fact_chunks"

    fact_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("extracted_facts.id"),
        primary_key=True,
    )
    chunk_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("chunks.id"),
        primary_key=True,
    )

    # Citation details
    excerpt: Mapped[str | None] = mapped_column(Text)  # Relevant text excerpt

    # Relationships
    fact = relationship("ExtractedFact", back_populates="source_chunks")
    chunk = relationship("Chunk", back_populates="fact_citations")


class FactRevision(Base, TimestampMixin):
    """
    Immutable audit log of fact changes.

    Per spec: FactRevision tracks all modifications to facts.
    """

    __tablename__ = "fact_revisions"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    revision_number: Mapped[int] = mapped_column(Integer, nullable=False)

    # What changed
    previous_value: Mapped[dict | None] = mapped_column(JSON)
    new_value: Mapped[dict] = mapped_column(JSON, nullable=False)
    previous_status: Mapped[str | None] = mapped_column(String(20))
    new_status: Mapped[str] = mapped_column(String(20), nullable=False)

    # Who changed it
    changed_by_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id"),
        nullable=False,
    )
    change_reason: Mapped[str | None] = mapped_column(Text)

    # Foreign keys
    fact_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("extracted_facts.id"),
        nullable=False,
        index=True,
    )

    # Relationships
    fact = relationship("ExtractedFact", back_populates="revisions")
    changed_by_user = relationship("User", back_populates="fact_revisions")


class EvidenceLink(Base, TimestampMixin):
    """
    Maps facts to system meaning.

    Per spec: EvidenceLink connects ExtractedFacts to checklists, readiness, etc.
    """

    __tablename__ = "evidence_links"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    link_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # checklist_item, readiness_dimension, deliverable_section
    target_id: Mapped[str] = mapped_column(String(100), nullable=False)
    contribution_weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)

    # Foreign keys
    fact_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("extracted_facts.id"),
        nullable=False,
        index=True,
    )

    # Relationships
    fact = relationship("ExtractedFact", back_populates="evidence_links")
