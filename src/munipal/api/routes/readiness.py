"""
Readiness scoring endpoints.

Per spec: ReadinessDimension represents high-level maturity scoring buckets.
Scores are deterministic (rules-based, not learned) on a 0-5 scale.

Playbook defines 6 dimensions with weighted scoring:
- Issuer Authority (20%)
- Project/Tech (20%)
- Revenue/Feedstock (15%)
- CAB Financial (20%)
- Risk/Security/SLB (15%)
- SLB Verification (10%)
"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from munipal.db.session import get_async_session

router = APIRouter()


@router.get("/")
async def get_readiness_scores(
    project_id: UUID,
    db: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """
    Get readiness scores for all dimensions.

    Per spec scoring ranges:
    - 0.0-3.0: Not Yet Viable
    - 3.0-5.5: Structurally Viable
    - 5.6-7.5: Ready for Selective Engagement
    - 7.6-10.0: Ready for Broad Market
    """
    # TODO: Implement readiness scoring
    return {
        "dimensions": {
            "issuer_authority": {"score": 0.0, "max_score": 5.0, "weight": 0.20},
            "project_tech": {"score": 0.0, "max_score": 5.0, "weight": 0.20},
            "revenue_feedstock": {"score": 0.0, "max_score": 5.0, "weight": 0.15},
            "cab_financial": {"score": 0.0, "max_score": 5.0, "weight": 0.20},
            "risk_security_slb": {"score": 0.0, "max_score": 5.0, "weight": 0.15},
            "slb_verification": {"score": 0.0, "max_score": 5.0, "weight": 0.10},
        },
        "overall_score": 0.0,
        "recommendation": "Not Yet Viable",
    }


@router.get("/{dimension}")
async def get_dimension_detail(
    project_id: UUID,
    dimension: str,
    db: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """
    Get detailed scoring breakdown for a specific dimension.

    Returns the contributing facts, their weights, and scoring rationale.
    """
    valid_dimensions = [
        "issuer_authority",
        "project_tech",
        "revenue_feedstock",
        "cab_financial",
        "risk_security_slb",
        "slb_verification",
    ]

    if dimension not in valid_dimensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid dimension. Must be one of: {valid_dimensions}",
        )

    # TODO: Implement dimension detail
    return {
        "dimension": dimension,
        "score": 0.0,
        "contributing_facts": [],
        "missing_critical_paths": [],
        "explanation": "",
    }


@router.get("/gaps")
async def get_readiness_gaps(
    project_id: UUID,
    db: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """
    Get a prioritized list of gaps that would improve readiness scores.

    Per spec: "Gaps are features, not bugs." This endpoint surfaces
    what evidence is missing to help users understand what to provide.
    """
    # TODO: Implement gap analysis
    return {
        "critical_gaps": [],  # Would block deal progression
        "material_gaps": [],  # Would significantly improve score
        "secondary_gaps": [],  # Nice to have
    }


@router.get("/explanation")
async def get_readiness_explanation(
    project_id: UUID,
    db: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """
    Get a narrative explanation of the readiness assessment.

    Per spec: Uses explanation templates from playbook to generate
    human-readable why-it-matters narratives.
    """
    # TODO: Implement explanation generation
    return {
        "summary": "",
        "dimension_explanations": {},
        "next_steps": [],
    }
