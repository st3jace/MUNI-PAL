"""
Readiness scoring endpoints.

Per spec: ReadinessDimension represents high-level maturity scoring buckets.
Scores are deterministic (rules-based, not learned) on a 0-5 scale per dimension.

Playbook defines 6 dimensions with weighted scoring:
- Issuer Authority (20%)
- Project/Tech (20%)
- Revenue/Feedstock (15%)
- CAB Financial (20%)
- Risk/Security/SLB (15%)
- SLB Verification (10%)

Overall scoring ranges (0-10):
- 0.0-3.0: Not Yet Viable
- 3.0-5.5: Structurally Viable
- 5.5-7.5: Ready for Selective Engagement
- 7.5-10.0: Ready for Broad Market
"""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from munipal.core.schemas.base import ReadinessDimension
from munipal.core.schemas.readiness import (
    ReadinessAssessment,
    ReadinessGapReport,
)
from munipal.db.session import get_async_session
from munipal.services.readiness_service import ReadinessService

router = APIRouter()


def get_readiness_service(
    db: AsyncSession = Depends(get_async_session),
) -> ReadinessService:
    """Dependency to get ReadinessService instance."""
    return ReadinessService(db)


# -----------------------------------------------------------------------------
# Overall Assessment
# -----------------------------------------------------------------------------


@router.get("/", response_model=ReadinessAssessment)
async def get_readiness_scores(
    project_id: UUID,
    service: ReadinessService = Depends(get_readiness_service),
) -> ReadinessAssessment:
    """
    Get complete readiness assessment for all dimensions.

    Returns dimension-by-dimension scores with weighted contributions
    to overall score, plus recommendation based on scoring thresholds:

    - 0.0-3.0: Not Yet Viable - Fundamental evidence gaps
    - 3.0-5.5: Structurally Viable - Foundation established, gaps remain
    - 5.5-7.5: Ready for Selective Engagement - Can begin advisor discussions
    - 7.5-10.0: Ready for Broad Market - Substantially documented
    """
    return await service.compute_assessment(project_id)


# -----------------------------------------------------------------------------
# Gap Analysis
# -----------------------------------------------------------------------------


@router.get("/gaps", response_model=ReadinessGapReport)
async def get_readiness_gaps(
    project_id: UUID,
    service: ReadinessService = Depends(get_readiness_service),
) -> ReadinessGapReport:
    """
    Get a prioritized list of gaps that would improve readiness scores.

    Per spec: "Gaps are features, not bugs." This endpoint surfaces
    what evidence is missing to help users understand what to provide.

    Returns gaps organized by criticality:
    - critical_gaps: Block deal progression, highest priority
    - material_gaps: Significantly affect scoring
    - secondary_gaps: Nice to have, lower priority

    Also includes priority_actions - top recommended steps.
    """
    return await service.compute_gaps(project_id)


# -----------------------------------------------------------------------------
# Dimension Details
# -----------------------------------------------------------------------------


@router.get("/dimension/{dimension}", response_model=dict)
async def get_dimension_detail(
    project_id: UUID,
    dimension: ReadinessDimension,
    service: ReadinessService = Depends(get_readiness_service),
) -> dict:
    """
    Get detailed scoring breakdown for a specific dimension.

    Returns:
    - Score and weighted contribution
    - Contributing facts with confidence scores
    - Missing paths with suggested evidence
    - Improvement suggestions

    Available dimensions:
    - issuer_authority: Issuer Authorization & Entity Formation
    - project_tech: Project & Technology Definition
    - revenue_feedstock: Revenue Model & Feedstock Supply
    - cab_financial: CAB Financial Structure & DSCR
    - risk_security_slb: Risk Assessment & Security Package
    - slb_verification: SLB KPIs & Verification Plan
    """
    return await service.get_dimension_detail(project_id, dimension)


@router.get("/dimension/{dimension}/summary", response_model=dict)
async def get_dimension_summary(
    project_id: UUID,
    dimension: ReadinessDimension,
    service: ReadinessService = Depends(get_readiness_service),
) -> dict:
    """
    Get quick summary for a dimension without full fact listing.
    """
    detail = await service.get_dimension_detail(project_id, dimension)
    return {
        "dimension": detail["dimension"],
        "dimension_name": detail["dimension_name"],
        "score": detail["score"],
        "max_score": detail["max_score"],
        "weight": detail["weight"],
        "critical_coverage": detail["critical_coverage"],
        "explanation": detail["explanation"],
    }


# -----------------------------------------------------------------------------
# Explanation
# -----------------------------------------------------------------------------


@router.get("/explanation", response_model=dict)
async def get_readiness_explanation(
    project_id: UUID,
    service: ReadinessService = Depends(get_readiness_service),
) -> dict:
    """
    Get a narrative explanation of the readiness assessment.

    Returns human-readable explanations for each dimension
    and overall recommendation rationale.
    """
    assessment = await service.compute_assessment(project_id)

    dimension_explanations = {
        dim.value: {
            "name": score.dimension_name,
            "score": score.score,
            "explanation": score.explanation,
            "suggestions": score.improvement_suggestions,
        }
        for dim, score in assessment.dimensions.items()
    }

    # Generate summary narrative
    if assessment.overall_score < 3.0:
        summary = (
            f"Project readiness score is {assessment.overall_score:.1f}/10 (Not Yet Viable). "
            f"There are {assessment.critical_gaps_count} critical gaps that need to be addressed "
            "before engaging bond counsel or underwriters."
        )
    elif assessment.overall_score < 5.5:
        summary = (
            f"Project readiness score is {assessment.overall_score:.1f}/10 (Structurally Viable). "
            f"The foundation is in place but {assessment.critical_gaps_count + assessment.material_gaps_count} "
            "gaps should be addressed to strengthen the package."
        )
    elif assessment.overall_score < 7.5:
        summary = (
            f"Project readiness score is {assessment.overall_score:.1f}/10 (Ready for Selective Engagement). "
            "Documentation supports preliminary advisor discussions. "
            "Remaining gaps can be addressed in parallel with engagement."
        )
    else:
        summary = (
            f"Project readiness score is {assessment.overall_score:.1f}/10 (Ready for Broad Market). "
            "The evidence base is substantially complete. "
            "Project is ready for formal underwriter selection process."
        )

    # Generate next steps
    gap_report = await service.compute_gaps(project_id)
    next_steps = gap_report.priority_actions

    return {
        "summary": summary,
        "overall_score": assessment.overall_score,
        "recommendation": assessment.recommendation,
        "recommendation_rationale": assessment.recommendation_rationale,
        "dimension_explanations": dimension_explanations,
        "next_steps": next_steps,
        "metrics": {
            "total_facts_approved": assessment.total_facts_approved,
            "total_facts_pending": assessment.total_facts_pending,
            "critical_gaps": assessment.critical_gaps_count,
            "material_gaps": assessment.material_gaps_count,
        },
    }
