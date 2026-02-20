"""
Readiness scoring schemas.

Per spec: ReadinessDimension represents high-level maturity scoring buckets.
Scores are DETERMINISTIC (rules-based, not learned) on a 0-5 scale.

Playbook defines 6 dimensions with weighted scoring.
"""

from pydantic import Field

from munipal.core.schemas.base import BaseSchema, ReadinessDimension, UUIDSchema


# Dimension weights per playbook
DIMENSION_WEIGHTS: dict[ReadinessDimension, float] = {
    ReadinessDimension.ISSUER_AUTHORITY: 0.20,
    ReadinessDimension.PROJECT_TECH: 0.20,
    ReadinessDimension.REVENUE_FEEDSTOCK: 0.15,
    ReadinessDimension.CAB_FINANCIAL: 0.20,
    ReadinessDimension.RISK_SECURITY_SLB: 0.15,
    ReadinessDimension.SLB_VERIFICATION: 0.10,
}

DIMENSION_NAMES: dict[ReadinessDimension, str] = {
    ReadinessDimension.ISSUER_AUTHORITY: "Issuer Authority",
    ReadinessDimension.PROJECT_TECH: "Project & Technology",
    ReadinessDimension.REVENUE_FEEDSTOCK: "Revenue & Feedstock",
    ReadinessDimension.CAB_FINANCIAL: "CAB Financial Structure",
    ReadinessDimension.RISK_SECURITY_SLB: "Risk, Security & SLB",
    ReadinessDimension.SLB_VERIFICATION: "SLB Verification",
}


class DimensionScore(BaseSchema):
    """Score for a single readiness dimension."""

    dimension: ReadinessDimension
    dimension_name: str
    score: float = Field(..., ge=0.0, le=5.0, description="Score on 0-5 scale")
    max_score: float = 5.0
    weight: float = Field(..., ge=0.0, le=1.0)
    weighted_contribution: float = Field(
        ...,
        description="This dimension's contribution to overall score",
    )

    # Scoring breakdown
    critical_paths_covered: int = 0
    critical_paths_total: int = 0
    material_paths_covered: int = 0
    material_paths_total: int = 0

    # Explanation
    explanation: str = Field(..., description="Why-it-matters narrative from playbook")
    improvement_suggestions: list[str] = Field(
        default_factory=list,
        description="Specific actions to improve this dimension",
    )


class ReadinessAssessment(BaseSchema):
    """
    Complete readiness assessment for a project.

    Per spec scoring ranges:
    - 0.0-3.0: Not Yet Viable
    - 3.0-5.5: Structurally Viable
    - 5.6-7.5: Ready for Selective Engagement
    - 7.6-10.0: Ready for Broad Market
    """

    project_id: str

    # Dimension scores
    dimensions: dict[ReadinessDimension, DimensionScore]

    # Overall assessment
    overall_score: float = Field(
        ...,
        ge=0.0,
        le=10.0,
        description="Weighted average on 0-10 scale",
    )
    recommendation: str = Field(
        ...,
        description="One of: Not Yet Viable, Structurally Viable, Ready for Selective Engagement, Ready for Broad Market",
    )
    recommendation_rationale: str = Field(
        ...,
        description="Explanation of the recommendation",
    )

    # Summary metrics
    total_facts_approved: int = 0
    total_facts_pending: int = 0
    critical_gaps_count: int = 0
    material_gaps_count: int = 0


class ReadinessGap(BaseSchema):
    """A specific gap in readiness evidence."""

    schema_path: str
    dimension: ReadinessDimension
    criticality: str  # critical, material, secondary
    description: str
    short_description: str = Field(
        default="",
        description="Brief one-sentence explanation of what this data point is",
    )
    impact: str = Field(..., description="How this gap affects the assessment")
    suggested_evidence: str = Field(
        ...,
        description="What type of document or data would fill this gap",
    )


class ReadinessGapReport(BaseSchema):
    """Prioritized report of all readiness gaps."""

    project_id: str
    overall_score: float

    critical_gaps: list[ReadinessGap] = Field(
        default_factory=list,
        description="Gaps that block deal progression",
    )
    material_gaps: list[ReadinessGap] = Field(
        default_factory=list,
        description="Gaps that significantly affect scoring",
    )
    secondary_gaps: list[ReadinessGap] = Field(
        default_factory=list,
        description="Nice-to-have evidence",
    )

    # Recommendations
    priority_actions: list[str] = Field(
        default_factory=list,
        description="Top 3-5 actions to improve readiness",
    )
