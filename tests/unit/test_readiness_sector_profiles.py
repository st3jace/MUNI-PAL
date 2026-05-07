from __future__ import annotations

import pytest

from scripts.seed_demo_scenarios import seed_demo_scenarios
from munipal.services.readiness_service import ReadinessService


LEGACY_UCS_TERMS = (
    "CAB",
    "SLB",
    "Feedstock",
    "feedstock",
    "Nameplate Throughput",
    "Supply Mechanism",
    "Offtake Status",
    "KPI baseline",
)


async def _seeded_project_id(db_session, slug: str) -> str:
    results = await seed_demo_scenarios(db_session)
    await db_session.commit()
    return next(item["project_id"] for item in results if item["slug"] == slug)


async def _sector_readiness_text(db_session, slug: str) -> str:
    project_id = await _seeded_project_id(db_session, slug)
    service = ReadinessService(db_session)
    assessment = await service.compute_assessment(project_id)
    gaps = await service.compute_gaps(project_id)

    parts: list[str] = []
    for score in assessment.dimensions.values():
        parts.append(score.dimension_name)
        parts.append(score.explanation)
        parts.extend(score.improvement_suggestions)
    for gap_list in (gaps.critical_gaps, gaps.material_gaps, gaps.secondary_gaps):
        for gap in gap_list:
            parts.extend(
                [
                    gap.description,
                    gap.short_description,
                    gap.impact,
                    gap.suggested_evidence,
                ]
            )
    parts.extend(gaps.priority_actions)
    return "\n".join(part for part in parts if part)


@pytest.mark.asyncio
async def test_healthcare_readiness_uses_healthcare_sector_language(db_session):
    text = await _sector_readiness_text(db_session, "healthcare-primary")

    assert "Hospital / Healthcare Project Scope" in text
    assert "Audited Financials & Demand" in text
    assert "Revenue Pledge & Coverage" in text
    assert "Disclosure & Advisor Readiness" in text
    assert "tax certificate" in text.lower()
    assert "debt service reserve" in text.lower()
    assert not any(term in text for term in LEGACY_UCS_TERMS)


@pytest.mark.asyncio
async def test_housing_readiness_uses_housing_sector_language(db_session):
    text = await _sector_readiness_text(db_session, "housing-pilot-stage")

    assert "Affordable Housing Project Scope" in text
    assert "Site Control & Diligence" in text
    assert "Affordability & Subsidy Stack" in text
    assert "Housing Finance Readiness" in text
    assert "appraisal" in text.lower()
    assert "tax credit" in text.lower()
    assert "phase one" in text.lower()
    assert not any(term in text for term in LEGACY_UCS_TERMS)
