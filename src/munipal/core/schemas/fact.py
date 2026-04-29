"""
ExtractedFact and FactRevision schemas.

Per spec:
- ExtractedFact: THE CORE PRIMITIVE - structured, reviewable claim with provenance
- FactRevision: Immutable audit log of fact changes

Facts have a review lifecycle: pending -> approved/rejected/needs_revision
"""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import Field

from munipal.core.schemas.base import (
    BaseSchema,
    ChunkReference,
    SourceReference,
    CriticalityTier,
    ReviewStatus,
    SourceType,
    TimestampSchema,
    UUIDSchema,
)


# -----------------------------------------------------------------------------
# ExtractedFact Schemas
# -----------------------------------------------------------------------------


class FactDuplicateClassification(str, Enum):
    """Dedup classification assigned during canonicalization."""

    UNIQUE = "unique"
    DUPLICATE_EXACT = "duplicate_exact"
    DUPLICATE_SEMANTIC = "duplicate_semantic"
    CANDIDATE_CONFLICT = "candidate_conflict"


class FactLifecycleState(str, Enum):
    """Lifecycle state for active/archive workflows."""

    ACTIVE = "active"
    ARCHIVED = "archived"
    REJECTED = "rejected"
    PENDING_REVIEW = "pending_review"


class ExtractedFactBase(BaseSchema):
    """
    Base extracted fact fields.

    Per spec: Facts are structured claims that map to canonical schema paths.
    Supports both AI-extracted and manually-entered facts.
    """

    # Schema mapping
    schema_path: str = Field(
        ...,
        description="Canonical path from playbook (e.g., 'cab.accretionrate', 'project.name')",
    )
    criticality: CriticalityTier = Field(
        CriticalityTier.SECONDARY,
        description="Importance tier from playbook",
    )

    # Source type: extracted (AI) or manual (user-entered)
    source_type: SourceType = Field(
        SourceType.EXTRACTED,
        description="Whether fact was AI-extracted or manually entered",
    )

    # Extracted value
    value: Any = Field(..., description="The extracted value (string, number, date, etc.)")
    value_type: str = Field(
        "string",
        description="Type hint for value (string, number, date, boolean, currency, percentage)",
    )
    unit: str | None = Field(None, description="Unit if applicable (USD, MW, tpd, etc.)")

    # Confidence
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="AI confidence in extraction (0.0-1.0), or 1.0 for manual facts",
    )
    confidence_rationale: str | None = Field(
        None,
        max_length=500,
        description="Why the AI assigned this confidence, or note for manual facts",
    )


class ExtractedFactCreate(ExtractedFactBase):
    """Schema for creating a fact (from extraction job)."""

    project_id: UUID
    extraction_job_id: UUID

    # Provenance - required for extracted facts
    source_chunks: list[ChunkReference] = Field(
        ...,
        min_length=1,
        description="At least one chunk must be cited as evidence",
    )


class ManualFactCreate(BaseSchema):
    """
    Schema for creating a manually-entered fact.

    Unlike ExtractedFactCreate, this doesn't require an extraction job
    or source chunks since the user is the source.
    """

    project_id: UUID
    schema_path: str = Field(
        ...,
        description="Canonical path from playbook (e.g., 'project.name')",
    )
    value: Any = Field(..., description="The fact value")
    value_type: str = Field(
        "string",
        description="Type hint for value (string, number, date, boolean, currency, percentage)",
    )
    unit: str | None = Field(None, description="Unit if applicable (USD, MW, tpd, etc.)")
    note: str | None = Field(
        None,
        max_length=1000,
        description="Optional note explaining the source or context of this fact",
    )


class ExtractedFactRead(ExtractedFactBase, UUIDSchema, TimestampSchema):
    """Schema for reading a fact (extracted or manual)."""

    project_id: UUID
    # Optional for manual facts which don't have an extraction job
    extraction_job_id: UUID | None = None

    # Review status
    review_status: ReviewStatus = ReviewStatus.PENDING
    reviewed_by: UUID | None = None
    reviewed_at: datetime | None = None
    review_note: str | None = None

    # Provenance - empty list for manual facts
    source_chunks: list[ChunkReference] = Field(default_factory=list)
    source_refs: list[SourceReference] = Field(
        default_factory=list,
        description=(
            "Advisor-facing stable source references: Artifact -> Chunk -> "
            "Page/Sheet -> source file."
        ),
    )
    provenance_fingerprint: str | None = Field(
        None,
        description="Deterministic SHA-256 fingerprint of ordered source_refs.",
    )

    # If corrected during review
    original_value: Any | None = Field(
        None,
        description="Original AI-extracted value if human corrected it",
    )

    # Dedup/canonicalization metadata
    fingerprint: str | None = None
    duplicate_classification: FactDuplicateClassification = FactDuplicateClassification.UNIQUE
    source_trust_score: float = Field(0.5, ge=0.0, le=1.0)
    canonical_score: float = Field(0.0, ge=0.0, le=1.0)
    is_canonical: bool = False
    lifecycle_state: FactLifecycleState = FactLifecycleState.ACTIVE
    review_lifecycle_stage: str = Field(
        "proposed",
        description=(
            "Human-review lifecycle stage: proposed, accepted, rejected, "
            "needs_revision, or archived."
        ),
    )
    can_drive_outputs: bool = Field(
        False,
        description="True only for active, human-accepted facts eligible for readiness/export outputs.",
    )
    archive_reason_code: str | None = None
    archive_note: str | None = None
    archived_by: UUID | None = None
    archived_at: datetime | None = None


class ExtractedFactSummary(UUIDSchema):
    """Minimal fact summary for listings."""

    schema_path: str
    value: Any
    confidence_score: float
    review_status: ReviewStatus
    criticality: CriticalityTier
    source_type: SourceType = SourceType.EXTRACTED
    duplicate_classification: FactDuplicateClassification = FactDuplicateClassification.UNIQUE
    is_canonical: bool = False
    lifecycle_state: FactLifecycleState = FactLifecycleState.ACTIVE


class MissingPathInfo(BaseSchema):
    """
    Information about a schema path that doesn't have an approved fact yet.

    Used for displaying outstanding items that need manual entry.
    """

    schema_path: str = Field(..., description="The canonical schema path")
    display_name: str = Field(..., description="Human-readable name for the path")
    criticality: CriticalityTier = Field(..., description="Importance tier")
    value_type: str = Field("string", description="Expected value type")
    phase: str = Field(..., description="Which checklist phase needs this")
    item_code: str = Field(..., description="Which checklist item needs this")
    item_title: str = Field(..., description="Title of the checklist item")


class FactReviewRequest(BaseSchema):
    """Schema for submitting a fact review."""

    action: ReviewStatus = Field(..., description="approve, reject, or needs_revision")
    corrected_value: Any | None = Field(None, description="Corrected value if approving with changes")
    note: str | None = Field(None, max_length=1000, description="Review note or rejection reason")


class FactArchiveRequest(BaseSchema):
    """Archive a superseded/redundant fact with mandatory reason."""

    reason_code: str = Field(..., min_length=1, max_length=64)
    note: str = Field(..., min_length=1, max_length=1000)


class FactUnarchiveRequest(BaseSchema):
    """Restore an archived fact to active lifecycle state."""

    note: str | None = Field(None, max_length=1000)


# -----------------------------------------------------------------------------
# FactRevision Schemas
# -----------------------------------------------------------------------------


class FactRevisionRead(UUIDSchema, TimestampSchema):
    """
    Schema for reading a fact revision.

    Per spec: FactRevision is an IMMUTABLE audit log.
    """

    fact_id: UUID
    revision_number: int = Field(..., ge=1)

    # What changed
    previous_value: Any | None
    new_value: Any
    previous_status: ReviewStatus | None
    new_status: ReviewStatus

    # Who changed it
    changed_by: UUID
    change_reason: str | None = Field(None, max_length=500)


# -----------------------------------------------------------------------------
# Evidence Link Schemas
# -----------------------------------------------------------------------------


class EvidenceLinkBase(BaseSchema):
    """
    Maps facts to system meaning.

    Per spec: EvidenceLink connects ExtractedFacts to checklists, readiness, etc.
    """

    fact_id: UUID
    link_type: str = Field(
        ...,
        description="Type of link: checklist_item, readiness_dimension, deliverable_section",
    )
    target_id: str = Field(
        ...,
        description="ID or path of linked entity (checklist item ID, dimension name, etc.)",
    )
    contribution_weight: float = Field(
        1.0,
        ge=0.0,
        le=1.0,
        description="How much this fact contributes to the target",
    )


class EvidenceLinkRead(EvidenceLinkBase, UUIDSchema, TimestampSchema):
    """Schema for reading an evidence link."""

    pass
