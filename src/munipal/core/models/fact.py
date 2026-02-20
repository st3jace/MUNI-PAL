"""
ExtractedFact and related models.

Per spec: ExtractedFact is THE CORE PRIMITIVE - structured, reviewable claim
with full provenance tracing.
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from munipal.db.base import Base, TimestampMixin, UUIDType


class ExtractedFact(Base, TimestampMixin):
    """
    THE CORE PRIMITIVE.

    A structured, reviewable claim about the project with full provenance.
    Supports both AI-extracted facts and manually-entered facts.
    """

    __tablename__ = "extracted_facts"

    id: Mapped[str] = mapped_column(
        UUIDType,
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    # Schema mapping
    schema_path: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    criticality: Mapped[str] = mapped_column(
        String(20), nullable=False, default="secondary"
    )  # critical, material, secondary

    # Source type: extracted (from AI) or manual (user-entered)
    source_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="extracted", index=True
    )  # extracted, manual

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
    reviewed_by: Mapped[str | None] = mapped_column(UUIDType, ForeignKey("users.id"))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    review_note: Mapped[str | None] = mapped_column(Text)

    # Original value if corrected during review
    original_value: Mapped[dict | None] = mapped_column(JSON)

    # Dedup/canonicalization metadata
    fingerprint: Mapped[str | None] = mapped_column(String(128), index=True)
    duplicate_classification: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="unique",
        index=True,
    )  # unique, duplicate_exact, duplicate_semantic, candidate_conflict
    source_trust_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    canonical_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    is_canonical: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)

    # Lifecycle state and archive controls
    lifecycle_state: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active",
        index=True,
    )  # active, archived, rejected, pending_review
    archive_reason_code: Mapped[str | None] = mapped_column(String(64))
    archive_note: Mapped[str | None] = mapped_column(Text)
    archived_by: Mapped[str | None] = mapped_column(UUIDType, ForeignKey("users.id"))
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Foreign keys
    project_id: Mapped[str] = mapped_column(
        UUIDType,
        ForeignKey("projects.id"),
        nullable=False,
        index=True,
    )
    # Nullable for manual facts which don't have an extraction job
    extraction_job_id: Mapped[str | None] = mapped_column(
        UUIDType,
        ForeignKey("extraction_jobs.id"),
        nullable=True,
    )

    # Relationships
    project = relationship("Project", back_populates="extracted_facts")
    extraction_job = relationship("ExtractionJob", back_populates="facts")
    reviewer = relationship("User", foreign_keys=[reviewed_by])
    archived_by_user = relationship("User", foreign_keys=[archived_by])
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
        UUIDType,
        ForeignKey("extracted_facts.id"),
        primary_key=True,
    )
    chunk_id: Mapped[str] = mapped_column(
        UUIDType,
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
        UUIDType,
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
        UUIDType,
        ForeignKey("users.id"),
        nullable=False,
    )
    change_reason: Mapped[str | None] = mapped_column(Text)

    # Foreign keys
    fact_id: Mapped[str] = mapped_column(
        UUIDType,
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
        UUIDType,
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
        UUIDType,
        ForeignKey("extracted_facts.id"),
        nullable=False,
        index=True,
    )

    # Relationships
    fact = relationship("ExtractedFact", back_populates="evidence_links")
