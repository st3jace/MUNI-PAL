"""
Information Request schemas for WP8 - Information Request System.

Per spec: WP8 transforms gap analysis from binary indicators into actionable
information requests that guide the team toward producing/procuring specific evidence.
"""

from datetime import date, datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import Field

from munipal.core.schemas.base import BaseSchema, TimestampSchema, UUIDSchema


# -----------------------------------------------------------------------------
# Enums
# -----------------------------------------------------------------------------


class EvidenceState(str, Enum):
    """Current state of evidence for a gap."""

    NONE = "none"  # No evidence exists
    PARTIAL = "partial"  # Some evidence, incomplete
    CONFLICTING = "conflicting"  # Multiple contradictory facts
    WEAK = "weak"  # Evidence exists but low confidence


class RequestPriority(str, Enum):
    """Priority levels for information requests."""

    LOW = "low"  # Nice to have, doesn't block progress
    MEDIUM = "medium"  # Material gap, should address before advisor engagement
    HIGH = "high"  # Critical path, blocks next phase
    CRITICAL = "critical"  # Deal-blocking, requires immediate escalation


class RequestStatus(str, Enum):
    """Lifecycle status for information requests."""

    OPEN = "open"  # Not yet started
    IN_PROGRESS = "in_progress"  # Owner acknowledged and working
    SUBMITTED = "submitted"  # Evidence submitted, pending review
    RESOLVED = "resolved"  # Facts accepted, request closed
    DEFERRED = "deferred"  # Explicitly deferred with reason


# -----------------------------------------------------------------------------
# Supporting Schemas
# -----------------------------------------------------------------------------


class BondDomainContext(BaseSchema):
    """Bond-domain context explaining why information matters."""

    why_it_matters: str = Field(
        ..., description="2-3 sentences explaining bond relevance"
    )
    who_needs_it: list[str] = Field(
        ..., description="Parties who need this (e.g., Municipal Advisor, Rating Agency)"
    )
    when_needed: str = Field(
        ..., description="When this is needed (e.g., 'Before P3 close')"
    )
    consequences: str = Field(
        ..., description="What happens if not provided"
    )
    related_requirements: list[str] = Field(
        default_factory=list, description="Other items this unlocks"
    )
    regulatory_reference: str | None = Field(
        None, description="SEC, MSRB, ICMA reference if applicable"
    )


class RequestGuidance(BaseSchema):
    """Guidance on how to fulfill an information request."""

    overview: str = Field(..., description="What we're asking for")
    specific_questions: list[str] = Field(
        ..., description="Concrete questions to answer"
    )
    data_points_needed: list[str] = Field(
        ..., description="Specific values required"
    )
    suggested_approach: str | None = Field(
        None, description="How to gather this"
    )
    common_pitfalls: list[str] = Field(
        default_factory=list, description="What to avoid"
    )
    time_estimate: str | None = Field(
        None, description="Expected effort"
    )


class EvidenceExample(BaseSchema):
    """Example of acceptable evidence."""

    description: str = Field(..., description="What this example shows")
    content_preview: str = Field(..., description="Excerpt or summary")
    why_acceptable: str = Field(..., description="Why this meets the standard")
    source_type: str = Field(
        ..., description="e.g., 'Feasibility Study', 'LOI', 'Engineering Report'"
    )


class AffectedItems(BaseSchema):
    """Items affected by an information gap."""

    checklist_items: list[str] = Field(
        default_factory=list, description="e.g., ['P2.3', 'P3.1']"
    )
    dimensions: list[str] = Field(
        default_factory=list, description="e.g., ['revenue_feedstock']"
    )
    disclosure_sections: list[str] = Field(
        default_factory=list, description="Disclosure sections affected"
    )


# -----------------------------------------------------------------------------
# Information Request Schemas
# -----------------------------------------------------------------------------


class InformationRequestBase(BaseSchema):
    """Base schema for information requests."""

    request_code: str = Field(
        ..., description="Unique code (e.g., 'IR-<PROJECT_TOKEN>-P2.3-001')"
    )
    title: str = Field(..., description="Human-readable title")

    # What's missing
    missing_fact_paths: list[str] = Field(
        ..., description="Schema paths that are missing"
    )
    current_evidence_state: EvidenceState = EvidenceState.NONE
    gap_id: str | None = Field(None, description="Link to gap record if tracked separately")

    # Priority and assignment
    priority: RequestPriority = RequestPriority.MEDIUM
    suggested_owner: str | None = Field(None, description="Suggested responsible party")
    target_date: date | None = Field(None, description="Target completion date")


class InformationRequestCreate(InformationRequestBase):
    """Schema for creating an information request."""

    project_id: UUID

    # Bond domain context
    why_it_matters: str
    who_needs_it: list[str] = Field(default_factory=list)
    when_needed: str | None = None
    consequences: str
    related_requirements: list[str] = Field(default_factory=list)
    regulatory_reference: str | None = None

    # Affected items
    affected_checklist_items: list[str] = Field(default_factory=list)
    affected_dimensions: list[str] = Field(default_factory=list)

    # Guidance
    guidance_overview: str
    specific_questions: list[str] = Field(default_factory=list)
    data_points_needed: list[str] = Field(default_factory=list)
    suggested_approach: str | None = None
    common_pitfalls: list[str] = Field(default_factory=list)
    time_estimate: str | None = None

    # Examples and sources
    examples: list[EvidenceExample] = Field(default_factory=list)
    acceptable_sources: list[str] = Field(default_factory=list)

    # Quality requirements
    minimum_confidence: float = Field(0.80, ge=0.0, le=1.0)
    expected_format: str | None = None


class InformationRequestRead(InformationRequestBase, UUIDSchema, TimestampSchema):
    """Schema for reading an information request."""

    project_id: UUID
    status: RequestStatus = RequestStatus.OPEN

    # Bond domain context
    why_it_matters: str
    who_needs_it: list[str] = Field(default_factory=list)
    when_needed: str | None = None
    consequences: str
    related_requirements: list[str] = Field(default_factory=list)
    regulatory_reference: str | None = None

    # Affected items
    affected_checklist_items: list[str] = Field(default_factory=list)
    affected_dimensions: list[str] = Field(default_factory=list)

    # Guidance
    guidance_overview: str
    specific_questions: list[str] = Field(default_factory=list)
    data_points_needed: list[str] = Field(default_factory=list)
    suggested_approach: str | None = None
    common_pitfalls: list[str] = Field(default_factory=list)
    time_estimate: str | None = None

    # Examples and sources
    examples: list[EvidenceExample] = Field(default_factory=list)
    acceptable_sources: list[str] = Field(default_factory=list)

    # Quality requirements
    minimum_confidence: float = 0.80
    expected_format: str | None = None

    # Status tracking
    acknowledged_at: datetime | None = None
    acknowledged_by: UUID | None = None
    submitted_at: datetime | None = None
    resolved_at: datetime | None = None
    deferred_at: datetime | None = None
    deferred_reason: str | None = None
    deferred_review_date: date | None = None

    # Resolution
    resolution_notes: str | None = None
    resolved_by_fact_ids: list[UUID] = Field(default_factory=list)

    # Linked evidence
    linked_artifact_id: UUID | None = None

    # Escalation
    escalation_level: int = 0
    last_escalated_at: datetime | None = None

    # Computed fields
    is_overdue: bool = False
    days_overdue: int = 0


class InformationRequestSummary(UUIDSchema):
    """Summary of an information request for listings."""

    request_code: str
    title: str
    priority: RequestPriority
    status: RequestStatus
    suggested_owner: str | None
    target_date: date | None
    is_overdue: bool = False
    days_overdue: int = 0
    created_at: datetime


class InformationRequestUpdate(BaseSchema):
    """Schema for updating an information request."""

    status: RequestStatus | None = None
    suggested_owner: str | None = None
    target_date: date | None = None
    notes: str | None = Field(None, description="Update notes")
    deferred_reason: str | None = None
    deferred_review_date: date | None = None


class LinkEvidenceRequest(BaseSchema):
    """Request to link evidence to an information request."""

    artifact_id: UUID
    notes: str | None = None


class ResolveRequestInput(BaseSchema):
    """Input for resolving an information request."""

    resolution_notes: str | None = None
    fact_ids: list[UUID] = Field(
        ..., description="Fact IDs that resolved this request"
    )


# -----------------------------------------------------------------------------
# Information Request Note Schemas
# -----------------------------------------------------------------------------


class RequestNoteCreate(BaseSchema):
    """Schema for creating a note on an information request."""

    request_id: UUID
    content: str = Field(..., min_length=1)
    note_type: str = Field(
        "update", description="Type: update, blocker, question, resolution"
    )


class RequestNoteRead(UUIDSchema, TimestampSchema):
    """Schema for reading a request note."""

    request_id: UUID
    content: str
    note_type: str
    created_by_id: UUID


# -----------------------------------------------------------------------------
# Aggregation Schemas
# -----------------------------------------------------------------------------


class RequestsByOwner(BaseSchema):
    """Information requests grouped by owner."""

    owner: str
    open_count: int = 0
    in_progress_count: int = 0
    overdue_count: int = 0
    requests: list[InformationRequestSummary] = Field(default_factory=list)


class RequestsByPriority(BaseSchema):
    """Information requests grouped by priority."""

    critical: list[InformationRequestSummary] = Field(default_factory=list)
    high: list[InformationRequestSummary] = Field(default_factory=list)
    medium: list[InformationRequestSummary] = Field(default_factory=list)
    low: list[InformationRequestSummary] = Field(default_factory=list)


class InformationRequestReport(BaseSchema):
    """Summary report of information requests for a project."""

    project_id: UUID

    # Counts by status
    open_count: int = 0
    in_progress_count: int = 0
    submitted_count: int = 0
    resolved_count: int = 0
    deferred_count: int = 0

    # Counts by priority
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0

    # Overdue
    overdue_count: int = 0
    overdue_requests: list[InformationRequestSummary] = Field(default_factory=list)

    # By owner
    by_owner: list[RequestsByOwner] = Field(default_factory=list)


# -----------------------------------------------------------------------------
# Template Schemas (for playbook configuration)
# -----------------------------------------------------------------------------


class InformationRequestTemplate(BaseSchema):
    """Template for generating information requests from gaps."""

    template_id: str = Field(..., description="Unique template identifier")
    title_template: str = Field(..., description="Title with placeholders")

    # Trigger conditions
    trigger_fact_paths: list[str] = Field(
        ..., description="Missing paths that trigger this template"
    )
    trigger_phase: str | None = Field(None, description="Phase that triggers this")

    # Bond domain context
    why_it_matters: str
    who_needs_it: list[str]
    when_needed: str
    consequences: str
    regulatory_reference: str | None = None

    # Guidance
    guidance_overview: str
    specific_questions: list[str]
    data_points_needed: list[str]
    suggested_approach: str
    common_pitfalls: list[str]
    time_estimate: str | None = None

    # Examples
    examples: list[EvidenceExample]

    # Sources and quality
    acceptable_sources: list[str]
    minimum_confidence: float = 0.80
    expected_format: str | None = None

    # Assignment
    default_priority: RequestPriority = RequestPriority.MEDIUM
    default_owner: str | None = None
