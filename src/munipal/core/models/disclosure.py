"""
Disclosure Document models for WP7 - Disclosure Synthesis Engine.

Per spec: WP7 transforms the skeletal "Disclosure Outline" into a substantive
disclosure document by synthesizing extracted facts into coherent, disclosure-ready prose.
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from munipal.db.base import Base, TimestampMixin, UUIDType


class DisclosureDocument(Base, TimestampMixin):
    """
    Synthesized disclosure document from extracted facts.

    Per WP7 spec: The primary external deliverable for municipal advisory engagement.
    Every sentence traces to ExtractedFact(s) or is a templated qualifier.
    """

    __tablename__ = "disclosure_documents"

    id: Mapped[str] = mapped_column(
        UUIDType,
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    # Version tracking
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Completeness metrics
    completeness_score: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )  # 0.0-1.0

    # Generation status
    is_complete: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    generation_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    generation_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Playbook reference
    playbook_version: Mapped[str | None] = mapped_column(String(50))

    # Foreign keys
    project_id: Mapped[str] = mapped_column(
        UUIDType,
        ForeignKey("projects.id"),
        nullable=False,
        index=True,
    )

    # Relationships
    project = relationship("Project", back_populates="disclosure_documents")
    sections = relationship(
        "DisclosureSection",
        back_populates="disclosure_document",
        cascade="all, delete-orphan",
        order_by="DisclosureSection.section_order",
    )
    tbd_items = relationship(
        "TBDMarker",
        back_populates="disclosure_document",
        cascade="all, delete-orphan",
    )


class DisclosureSection(Base, TimestampMixin):
    """
    Individual section within a disclosure document.

    Per WP7 spec: Each section is populated with synthesized prose from templates
    and extracted facts. Missing information is marked with TBD markers.
    """

    __tablename__ = "disclosure_sections"

    id: Mapped[str] = mapped_column(
        UUIDType,
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    # Section identification
    section_id: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # e.g., "introduction", "issuer", "project.technology"
    section_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    title: Mapped[str] = mapped_column(String(255), nullable=False)

    # Parent section for nested sections
    parent_section_id: Mapped[str | None] = mapped_column(
        UUIDType,
        ForeignKey("disclosure_sections.id"),
        nullable=True,
    )

    # Synthesized content
    content_md: Mapped[str] = mapped_column(Text, nullable=False, default="")

    # Confidence and metrics
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)  # 0.0-1.0
    required_fact_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    present_fact_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tbd_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Supporting facts (JSON array of fact IDs)
    supporting_fact_ids: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    # Conditional rendering
    conditional_on: Mapped[str | None] = mapped_column(
        String(255)
    )  # e.g., "slb.enabled == True"
    is_rendered: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Foreign keys
    disclosure_document_id: Mapped[str] = mapped_column(
        UUIDType,
        ForeignKey("disclosure_documents.id"),
        nullable=False,
        index=True,
    )

    # Relationships
    disclosure_document = relationship("DisclosureDocument", back_populates="sections")
    parent_section = relationship(
        "DisclosureSection",
        remote_side="DisclosureSection.id",
        backref="subsections",
    )
    tbd_markers = relationship(
        "TBDMarker",
        back_populates="section",
        cascade="all, delete-orphan",
    )


class TBDMarker(Base, TimestampMixin):
    """
    Marker for missing information in disclosure sections.

    Per WP7 spec: When evidence is insufficient, insert [TBD: {reason}] marker
    and track in tbd_items array.
    """

    __tablename__ = "tbd_markers"

    id: Mapped[str] = mapped_column(
        UUIDType,
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    # Location within content
    location: Mapped[str] = mapped_column(String(255), nullable=False)

    # What's missing
    missing_fact_paths: Mapped[list] = mapped_column(
        JSON, nullable=False, default=list
    )  # List of schema paths

    # Context
    reason: Mapped[str] = mapped_column(Text, nullable=False)

    # Severity classification
    severity: Mapped[str] = mapped_column(
        String(20), nullable=False, default="medium"
    )  # low, medium, high, critical

    # Resolution tracking
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolved_by_fact_id: Mapped[str | None] = mapped_column(
        UUIDType,
        ForeignKey("extracted_facts.id"),
        nullable=True,
    )

    # Foreign keys
    disclosure_document_id: Mapped[str] = mapped_column(
        UUIDType,
        ForeignKey("disclosure_documents.id"),
        nullable=False,
        index=True,
    )
    section_id: Mapped[str | None] = mapped_column(
        UUIDType,
        ForeignKey("disclosure_sections.id"),
        nullable=True,
        index=True,
    )

    # Relationships
    disclosure_document = relationship("DisclosureDocument", back_populates="tbd_items")
    section = relationship("DisclosureSection", back_populates="tbd_markers")
    resolved_by_fact = relationship("ExtractedFact")
