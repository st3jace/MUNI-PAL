"""
Information Request models for WP8 - Information Request System.

Per spec: WP8 transforms gap analysis from binary indicators into actionable
information requests that guide the team toward producing/procuring specific evidence.
"""

from datetime import date, datetime
from uuid import uuid4

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from munipal.db.base import Base, TimestampMixin, UUIDType


class InformationRequest(Base, TimestampMixin):
    """
    Actionable information request generated from gap analysis.

    Per WP8 spec: Every gap produces a structured request with:
    - What's missing
    - Why it matters (bond-domain context)
    - How to fill it (guidance, examples, acceptable sources)
    - Assignment (priority, owner, deadline)
    """

    __tablename__ = "information_requests"

    id: Mapped[str] = mapped_column(
        UUIDType,
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    # Request identification
    request_code: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True
    )  # e.g., "IR-550E8400E29B41D4A716446655440000-P2.3-001"

    # Human-readable title
    title: Mapped[str] = mapped_column(String(255), nullable=False)

    # ===== WHAT'S MISSING =====
    # Link to gap (schema paths that are missing)
    missing_fact_paths: Mapped[list] = mapped_column(
        JSON, nullable=False, default=list
    )  # List of schema paths

    # Current evidence state
    current_evidence_state: Mapped[str] = mapped_column(
        String(20), nullable=False, default="none"
    )  # none, partial, conflicting, weak

    # Linked gap ID (if tracked separately)
    gap_id: Mapped[str | None] = mapped_column(String(100))

    # ===== WHY IT MATTERS (Bond Domain Context) =====
    why_it_matters: Mapped[str] = mapped_column(Text, nullable=False)
    who_needs_it: Mapped[list] = mapped_column(
        JSON, nullable=False, default=list
    )  # e.g., ["Municipal Advisor", "Rating Agency"]
    when_needed: Mapped[str | None] = mapped_column(String(255))  # e.g., "Before P3 close"
    consequences: Mapped[str] = mapped_column(Text, nullable=False)
    related_requirements: Mapped[list] = mapped_column(
        JSON, nullable=False, default=list
    )  # Other items this unlocks
    regulatory_reference: Mapped[str | None] = mapped_column(String(255))

    # ===== AFFECTED ITEMS =====
    affected_checklist_items: Mapped[list] = mapped_column(
        JSON, nullable=False, default=list
    )  # e.g., ["P2.3", "P3.1"]
    affected_dimensions: Mapped[list] = mapped_column(
        JSON, nullable=False, default=list
    )  # e.g., ["revenue_feedstock"]

    # ===== HOW TO FILL IT (Guidance) =====
    guidance_overview: Mapped[str] = mapped_column(Text, nullable=False)
    specific_questions: Mapped[list] = mapped_column(
        JSON, nullable=False, default=list
    )  # List of questions to answer
    data_points_needed: Mapped[list] = mapped_column(
        JSON, nullable=False, default=list
    )  # Specific values required
    suggested_approach: Mapped[str | None] = mapped_column(Text)
    common_pitfalls: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    time_estimate: Mapped[str | None] = mapped_column(String(100))

    # Examples of acceptable evidence (JSON array of example objects)
    examples: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    # Acceptable sources
    acceptable_sources: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    # Quality requirements
    minimum_confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.80)
    expected_format: Mapped[str | None] = mapped_column(String(255))

    # ===== ASSIGNMENT =====
    priority: Mapped[str] = mapped_column(
        String(20), nullable=False, default="medium"
    )  # low, medium, high, critical
    suggested_owner: Mapped[str | None] = mapped_column(String(255))
    target_date: Mapped[date | None] = mapped_column(Date)

    # ===== LIFECYCLE =====
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="open", index=True
    )  # open, in_progress, submitted, resolved, deferred

    # Status tracking
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    acknowledged_by: Mapped[str | None] = mapped_column(UUIDType, ForeignKey("users.id"))
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deferred_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deferred_reason: Mapped[str | None] = mapped_column(Text)
    deferred_review_date: Mapped[date | None] = mapped_column(Date)

    # Resolution tracking
    resolution_notes: Mapped[str | None] = mapped_column(Text)
    resolved_by_fact_ids: Mapped[list] = mapped_column(
        JSON, nullable=False, default=list
    )  # Fact IDs that resolved this

    # Linked evidence (artifact submitted to fulfill request)
    linked_artifact_id: Mapped[str | None] = mapped_column(
        UUIDType,
        ForeignKey("artifacts.id"),
        nullable=True,
    )

    # ===== ESCALATION =====
    escalation_level: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_escalated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Foreign keys
    project_id: Mapped[str] = mapped_column(
        UUIDType,
        ForeignKey("projects.id"),
        nullable=False,
        index=True,
    )

    # Relationships
    project = relationship("Project", back_populates="information_requests")
    linked_artifact = relationship("Artifact")
    acknowledger = relationship("User", foreign_keys=[acknowledged_by])


class InformationRequestNote(Base, TimestampMixin):
    """
    Notes and updates on information requests.

    Supports tracking progress, communications, and blockers.
    """

    __tablename__ = "information_request_notes"

    id: Mapped[str] = mapped_column(
        UUIDType,
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    # Note content
    content: Mapped[str] = mapped_column(Text, nullable=False)
    note_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="update"
    )  # update, blocker, question, resolution

    # Foreign keys
    request_id: Mapped[str] = mapped_column(
        UUIDType,
        ForeignKey("information_requests.id"),
        nullable=False,
        index=True,
    )
    created_by_id: Mapped[str] = mapped_column(
        UUIDType,
        ForeignKey("users.id"),
        nullable=False,
    )

    # Relationships
    request = relationship("InformationRequest", backref="notes")
    created_by = relationship("User")
