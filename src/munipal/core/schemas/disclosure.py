"""
Disclosure Document schemas for WP7 - Disclosure Synthesis Engine.

Per spec: WP7 transforms the skeletal "Disclosure Outline" into a substantive
disclosure document by synthesizing extracted facts into coherent, disclosure-ready prose.
"""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import Field

from munipal.core.schemas.base import BaseSchema, TimestampSchema, UUIDSchema


# -----------------------------------------------------------------------------
# Enums
# -----------------------------------------------------------------------------


class TBDSeverity(str, Enum):
    """Severity levels for TBD markers."""

    LOW = "low"  # Nice to have, doesn't block progress
    MEDIUM = "medium"  # Should address before advisor engagement
    HIGH = "high"  # Material gap, affects credibility
    CRITICAL = "critical"  # Deal-blocking, requires immediate attention


class DisclosureSectionType(str, Enum):
    """Standard disclosure section types."""

    INTRODUCTION = "introduction"
    ISSUER = "issuer"
    PROJECT = "project"
    PROJECT_TECHNOLOGY = "project.technology"
    PROJECT_OPERATING = "project.operating"
    PROJECT_CONSTRUCTION = "project.construction"
    PROJECT_PERMITTING = "project.permitting"
    SECURITY = "security"
    SECURITY_REVENUE = "security.revenue"
    SECURITY_COLLATERAL = "security.collateral"
    SECURITY_RESERVES = "security.reserves"
    FINANCIAL = "financial"
    FINANCIAL_PROJECTIONS = "financial.projections"
    FINANCIAL_DSCR = "financial.dscr"
    FINANCIAL_SENSITIVITY = "financial.sensitivity"
    RISK_FACTORS = "risk_factors"
    RISK_TECHNOLOGY = "risk.technology"
    RISK_CONSTRUCTION = "risk.construction"
    RISK_MARKET = "risk.market"
    RISK_REGULATORY = "risk.regulatory"
    RISK_ENVIRONMENTAL = "risk.environmental"
    SLB_FEATURES = "slb_features"
    SLB_KPIS = "slb.kpis"
    SLB_SPTS = "slb.spts"
    SLB_VERIFICATION = "slb.verification"
    SLB_PENALTIES = "slb.penalties"


# -----------------------------------------------------------------------------
# TBD Marker Schemas
# -----------------------------------------------------------------------------


class TBDMarkerBase(BaseSchema):
    """Base schema for TBD markers."""

    location: str = Field(..., description="Location within the section content")
    missing_fact_paths: list[str] = Field(
        ..., description="Schema paths that are missing"
    )
    reason: str = Field(..., description="Human-readable reason for the TBD")
    severity: TBDSeverity = TBDSeverity.MEDIUM


class TBDMarkerCreate(TBDMarkerBase):
    """Schema for creating a TBD marker."""

    disclosure_document_id: UUID
    section_id: UUID | None = None


class TBDMarkerRead(TBDMarkerBase, UUIDSchema, TimestampSchema):
    """Schema for reading a TBD marker."""

    disclosure_document_id: UUID
    section_id: UUID | None = None
    is_resolved: bool = False
    resolved_at: datetime | None = None
    resolved_by_fact_id: UUID | None = None


# -----------------------------------------------------------------------------
# Disclosure Section Schemas
# -----------------------------------------------------------------------------


class DisclosureSectionBase(BaseSchema):
    """Base schema for disclosure sections."""

    section_id: str = Field(..., description="Section identifier (e.g., 'introduction', 'issuer')")
    title: str = Field(..., description="Section title")
    section_order: int = Field(0, description="Order within document")
    parent_section_id: UUID | None = Field(None, description="Parent section for nested sections")


class DisclosureSectionCreate(DisclosureSectionBase):
    """Schema for creating a disclosure section."""

    disclosure_document_id: UUID
    content_md: str = ""
    conditional_on: str | None = None


class DisclosureSectionRead(DisclosureSectionBase, UUIDSchema, TimestampSchema):
    """Schema for reading a disclosure section."""

    disclosure_document_id: UUID
    content_md: str = ""

    # Metrics
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    required_fact_count: int = 0
    present_fact_count: int = 0
    tbd_count: int = 0

    # Supporting evidence
    supporting_fact_ids: list[UUID] = Field(default_factory=list)

    # Conditional rendering
    conditional_on: str | None = None
    is_rendered: bool = True

    # Nested TBD markers
    tbd_markers: list[TBDMarkerRead] = Field(default_factory=list)

    # Nested subsections
    subsections: list["DisclosureSectionRead"] = Field(default_factory=list)


class DisclosureSectionPreview(BaseSchema):
    """Preview of a disclosure section before full generation."""

    section_id: str
    title: str
    can_generate: bool = Field(
        ..., description="Whether there's enough evidence to generate this section"
    )
    required_facts: list[str] = Field(
        ..., description="Schema paths required for this section"
    )
    available_facts: list[str] = Field(
        ..., description="Schema paths that have approved facts"
    )
    missing_facts: list[str] = Field(
        ..., description="Schema paths without approved facts"
    )
    estimated_confidence: float = Field(
        0.0, ge=0.0, le=1.0, description="Estimated section confidence"
    )


# -----------------------------------------------------------------------------
# Disclosure Document Schemas
# -----------------------------------------------------------------------------


class DisclosureDocumentBase(BaseSchema):
    """Base schema for disclosure documents."""

    version: int = 1
    playbook_version: str | None = None


class DisclosureDocumentCreate(DisclosureDocumentBase):
    """Schema for creating a disclosure document."""

    project_id: UUID


class DisclosureDocumentRead(DisclosureDocumentBase, UUIDSchema, TimestampSchema):
    """Schema for reading a disclosure document."""

    project_id: UUID
    completeness_score: float = Field(0.0, ge=0.0, le=1.0)

    # Generation status
    is_complete: bool = False
    generation_started_at: datetime | None = None
    generation_completed_at: datetime | None = None

    # Sections
    sections: list[DisclosureSectionRead] = Field(default_factory=list)

    # TBD summary
    tbd_items: list[TBDMarkerRead] = Field(default_factory=list)
    tbd_summary: dict[TBDSeverity, int] = Field(default_factory=dict)


class DisclosureDocumentSummary(UUIDSchema):
    """Summary of a disclosure document for listings."""

    project_id: UUID
    version: int
    completeness_score: float
    is_complete: bool
    section_count: int
    tbd_count: int
    created_at: datetime


# -----------------------------------------------------------------------------
# Generation Schemas
# -----------------------------------------------------------------------------


class GenerateDisclosureRequest(BaseSchema):
    """Request to generate a disclosure document."""

    project_id: UUID
    sections: list[str] | None = Field(
        None, description="Specific sections to generate (None = all)"
    )
    force_regenerate: bool = Field(
        False, description="Regenerate even if document exists"
    )


class GenerateDisclosureResponse(BaseSchema):
    """Response from disclosure generation."""

    document_id: UUID
    status: str = Field(..., description="queued, running, completed, failed")
    message: str | None = None
    celery_task_id: str | None = None


# -----------------------------------------------------------------------------
# Template Schemas (for playbook configuration)
# -----------------------------------------------------------------------------


class FactSlot(BaseSchema):
    """A slot in a template that gets filled from facts."""

    schema_path: str = Field(..., description="Path to the fact value")
    format: str | None = Field(None, description="Format type: currency, percent, date, etc.")
    default: Any = Field(None, description="Default value if fact is missing")
    tbd_reason: str | None = Field(None, description="Reason to show if TBD")


class ConditionalBlock(BaseSchema):
    """A conditional block in a template."""

    condition: str = Field(..., description="Condition expression (e.g., 'slb.enabled == True')")
    content: str = Field(..., description="Content to include if condition is true")
    else_content: str | None = Field(None, description="Content if condition is false")


class DisclosureSectionTemplate(BaseSchema):
    """Template definition for a disclosure section."""

    section_id: str
    title: str
    section_order: int = 0

    # Required and optional facts
    required_fact_paths: list[str] = Field(
        default_factory=list, description="Facts that must be present for meaningful content"
    )
    optional_fact_paths: list[str] = Field(
        default_factory=list, description="Facts that enhance if present"
    )

    # Confidence threshold
    minimum_confidence: float = Field(
        0.70, ge=0.0, le=1.0, description="Minimum confidence to generate section"
    )

    # Template content
    template: str = Field(..., description="Template with fact slots and conditionals")

    # Conditional rendering
    conditional_on: str | None = Field(
        None, description="Condition for rendering (e.g., 'slb.enabled == True')"
    )

    # Nested templates
    subsection_templates: list["DisclosureSectionTemplate"] = Field(default_factory=list)


# Enable forward references
DisclosureSectionRead.model_rebuild()
DisclosureSectionTemplate.model_rebuild()
