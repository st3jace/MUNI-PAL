"""
ChecklistItem schemas.

Per spec: ChecklistItem represents operational bond diligence requirements.
Status is COMPUTED from linked facts, not stored directly.

Playbook defines P1-P6 phases with specific items per phase.
"""

from uuid import UUID

from pydantic import Field

from munipal.core.schemas.base import (
    BaseSchema,
    ChecklistPhase,
    ChecklistStatus,
    CriticalityTier,
    TimestampSchema,
    UUIDSchema,
)


class ChecklistItemDefinition(BaseSchema):
    """
    Definition of a checklist item from playbook.

    This is the template; actual status is computed per-project.
    """

    item_code: str = Field(..., description="Unique code (e.g., 'P1.1', 'P2.3')")
    phase: ChecklistPhase
    title: str = Field(..., max_length=255)
    description: str = Field(..., max_length=2000)

    # Requirements
    required_schema_paths: list[str] = Field(
        ...,
        description="Schema paths that must have approved facts for this item to be 'ready'",
    )
    optional_schema_paths: list[str] = Field(
        default_factory=list,
        description="Schema paths that contribute but aren't required",
    )

    # Criticality
    criticality: CriticalityTier = CriticalityTier.MATERIAL
    blocks_phase_completion: bool = Field(
        True,
        description="If True, phase cannot complete until this item is ready",
    )

    # Explanation templates (from playbook)
    in_progress_explanation: str | None = None
    blocked_explanation: str | None = None
    ready_explanation: str | None = None


class ChecklistItemStatus(BaseSchema):
    """
    Computed status for a checklist item in a specific project.

    Per spec: Status is deterministic (rules-based, not learned).
    """

    item_code: str
    phase: ChecklistPhase
    title: str

    # Computed status
    status: ChecklistStatus
    status_reason: str = Field(
        ...,
        description="Human-readable explanation of why this status",
    )

    # Coverage metrics
    required_paths_count: int
    covered_paths_count: int
    coverage_percentage: float = Field(..., ge=0.0, le=100.0)

    # Linked facts
    linked_fact_ids: list[UUID] = Field(default_factory=list)

    # Gaps
    missing_paths: list[str] = Field(
        default_factory=list,
        description="Required paths without approved facts",
    )
    low_confidence_paths: list[str] = Field(
        default_factory=list,
        description="Paths with facts below confidence threshold",
    )


class ChecklistItemRead(UUIDSchema, TimestampSchema):
    """Full checklist item with definition and computed status."""

    project_id: UUID
    definition: ChecklistItemDefinition
    status: ChecklistItemStatus


class ChecklistPhaseSummary(BaseSchema):
    """Summary of checklist completion for a phase."""

    phase: ChecklistPhase
    phase_name: str
    total_items: int
    ready_count: int
    in_progress_count: int
    blocked_count: int
    not_started_count: int
    completion_percentage: float = Field(..., ge=0.0, le=100.0)
    can_proceed_to_next: bool = Field(
        ...,
        description="True if all blocking items are ready",
    )
