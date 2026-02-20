"""
DeliverablePack schemas.

Per spec: DeliverablePack is the generated advisor-ready output bundle.
This is the "warm handoff pack" that packages everything for professional review.
"""

from datetime import datetime
from uuid import UUID

from pydantic import Field

from munipal.core.schemas.base import BaseSchema, TimestampSchema, UUIDSchema


class DeliverableSection(BaseSchema):
    """
    A section of the deliverable pack.

    Per playbook Section 8, the pack has 9 sections:
    1. Cover
    2. Deal Overview Memo
    3. Readiness & Gap Report
    4. Checklist Status
    5. Evidence Index
    6. Assumption Register
    7. Financial Model Outputs
    8. SLB KPI Brief
    9. Disclosure Outline
    """

    section_number: int = Field(..., ge=1, le=9)
    section_name: str
    content: str = Field(..., description="Markdown content for this section")
    is_complete: bool = True
    warnings: list[str] = Field(
        default_factory=list,
        description="Any warnings about this section (e.g., missing data)",
    )


class DeliverablePackBase(BaseSchema):
    """Base deliverable pack fields."""

    title: str = Field(..., max_length=255)
    generated_for: str = Field(
        ...,
        max_length=255,
        description="Intended recipient (e.g., 'Bond Counsel Review')",
    )


class DeliverablePackCreate(DeliverablePackBase):
    """Schema for requesting pack generation."""

    project_id: UUID
    include_sections: list[int] = Field(
        default_factory=lambda: [1, 2, 3, 4, 5, 6, 7, 8, 9],
        description="Section numbers to include (1-9)",
    )
    include_appendices: bool = True


class DeliverablePackRead(DeliverablePackBase, UUIDSchema, TimestampSchema):
    """Schema for reading a deliverable pack."""

    project_id: UUID

    # Generation status
    is_complete: bool = False
    generation_started_at: datetime | None = None
    generation_completed_at: datetime | None = None

    # Content
    sections: list[DeliverableSection] = Field(default_factory=list)

    # Metadata
    facts_included_count: int = 0
    readiness_score_at_generation: float | None = None

    # Warnings and disclaimers
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = Field(
        default=(
            "DISCLAIMER: This document is provided for informational purposes only and does not "
            "constitute investment advice, a recommendation to purchase or sell securities, or an "
            "offer or solicitation of an offer to buy or sell any securities. The information "
            "contained herein has been prepared from sources believed to be reliable but is not "
            "guaranteed as to accuracy or completeness. All facts and figures are subject to "
            "verification by qualified professionals. This document does not represent approval "
            "of any transaction and should not be relied upon as such."
        ),
        description="Mandatory standardized disclaimer per playbook",
    )


class DeliverablePackSummary(UUIDSchema):
    """Minimal pack summary for listings."""

    title: str
    generated_for: str
    is_complete: bool
    created_at: datetime
    generation_completed_at: datetime | None = None
    readiness_score_at_generation: float | None
