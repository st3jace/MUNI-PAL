"""
Playbook schemas.

Per spec: Playbook is a versioned configuration defining "bond-ready" criteria.
The playbook encodes domain knowledge about what bond professionals expect.
"""

from datetime import datetime
from uuid import UUID

from pydantic import Field

from munipal.core.schemas.base import BaseSchema, CriticalityTier, TimestampSchema, UUIDSchema
from munipal.core.schemas.checklist import ChecklistItemDefinition


class SchemaPathDefinition(BaseSchema):
    """
    Definition of a canonical schema path.

    Per playbook: Strict allowlist of valid extraction targets.
    """

    path: str = Field(..., description="Dot-notation path (e.g., 'cab.accretionrate')")
    display_name: str = Field(..., max_length=100)
    description: str = Field(..., max_length=500)
    value_type: str = Field(
        ...,
        description="Expected type: string, number, date, boolean, currency, percentage",
    )
    unit: str | None = Field(None, description="Expected unit if applicable")
    criticality: CriticalityTier

    # Validation rules
    min_confidence: float = Field(
        0.65,
        ge=0.0,
        le=1.0,
        description="Minimum confidence required for auto-approval consideration",
    )
    validation_regex: str | None = Field(
        None,
        description="Optional regex for value validation",
    )
    allowed_values: list[str] | None = Field(
        None,
        description="Optional enumeration of valid values",
    )

    # Extraction hints
    extraction_hints: list[str] = Field(
        default_factory=list,
        description="Keywords or patterns to look for when extracting",
    )


class ExtractorDefinition(BaseSchema):
    """
    Definition of an AI extractor from playbook.

    Per playbook: 8 concrete extractors with prompt templates.
    """

    extractor_id: str = Field(..., description="Unique extractor identifier")
    name: str = Field(..., max_length=100)
    description: str = Field(..., max_length=500)

    # Target paths
    target_schema_paths: list[str] = Field(
        ...,
        description="Schema paths this extractor targets",
    )

    # Prompt configuration
    system_prompt: str = Field(..., description="System prompt for the LLM")
    extraction_prompt_template: str = Field(
        ...,
        description="User prompt template with {content} placeholder",
    )

    # Behavior
    requires_full_document: bool = Field(
        False,
        description="If True, needs full artifact; if False, works per-chunk",
    )
    idempotent: bool = Field(
        True,
        description="If True, re-running produces identical results",
    )


class PlaybookBase(BaseSchema):
    """Base playbook fields."""

    name: str = Field(..., min_length=1, max_length=100)
    version: str = Field(..., description="Semantic version (e.g., '0.2.0')")
    description: str = Field(..., max_length=2000)

    # Bond archetype this playbook covers
    bond_archetype: str = Field(
        ...,
        description="e.g., 'UCS CAB+SLB Waste-to-Energy Revenue Bond'",
    )


class PlaybookCreate(PlaybookBase):
    """Schema for creating a playbook (admin only)."""

    schema_paths: list[SchemaPathDefinition]
    extractors: list[ExtractorDefinition]
    checklist_items: list[ChecklistItemDefinition]


class PlaybookRead(PlaybookBase, UUIDSchema, TimestampSchema):
    """Schema for reading a playbook."""

    is_active: bool = True
    is_default: bool = False

    # Counts for overview
    schema_path_count: int = 0
    extractor_count: int = 0
    checklist_item_count: int = 0


class PlaybookDetail(PlaybookRead):
    """Full playbook with all definitions."""

    schema_paths: list[SchemaPathDefinition]
    extractors: list[ExtractorDefinition]
    checklist_items: list[ChecklistItemDefinition]
