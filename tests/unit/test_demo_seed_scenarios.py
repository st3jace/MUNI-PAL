from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import func, select

from munipal.core.models import Artifact, ExtractedFact, Project
from scripts.seed_demo_scenarios import DEMO_SCENARIOS, DEMO_TENANT_ID, seed_demo_scenarios
from munipal.services.project_service import ProjectService


@pytest.mark.asyncio
async def test_seed_demo_scenarios_create_healthcare_and_housing_projects(db_session):
    results = await seed_demo_scenarios(db_session)
    await db_session.commit()

    assert [result["slug"] for result in results] == ["healthcare-primary", "housing-pilot-stage"]
    assert all(result["project_id"] for result in results)
    assert all(result["artifacts"] >= 2 for result in results)
    assert all(result["approved_facts"] >= 5 for result in results)
    assert all(result["missing_evidence_paths"] for result in results)

    projects = (await db_session.execute(select(Project).where(Project.tenant_id == DEMO_TENANT_ID))).scalars().all()
    assert {project.sector for project in projects} == {"healthcare", "housing"}
    assert {project.issuer_name for project in projects} == {
        "Demo Regional Health Authority",
        "Demo Housing Finance Authority",
    }
    assert all("Demo" in project.issuer_name for project in projects)

    artifact_count = (await db_session.execute(select(func.count(Artifact.id)))).scalar_one()
    fact_count = (await db_session.execute(select(func.count(ExtractedFact.id)))).scalar_one()
    assert artifact_count == sum(len(scenario.artifacts) for scenario in DEMO_SCENARIOS)
    assert fact_count == sum(len(scenario.facts) for scenario in DEMO_SCENARIOS)


@pytest.mark.asyncio
async def test_seed_demo_scenarios_are_idempotent_and_dashboard_visible(db_session):
    first = await seed_demo_scenarios(db_session)
    await db_session.commit()
    second = await seed_demo_scenarios(db_session)
    await db_session.commit()

    assert [item["project_id"] for item in first] == [item["project_id"] for item in second]

    service = ProjectService(db_session)
    summaries, total = await service.list(tenant_id=DEMO_TENANT_ID, limit=10)

    assert total == 2
    assert {summary.name for summary in summaries} == {
        "Launch Demo — Healthcare Hospital Revenue Bond",
        "Launch Demo — Affordable Housing Pilot Stage",
    }
    assert all(summary.artifact_count >= 2 for summary in summaries)
    assert all(summary.overall_readiness_score is not None for summary in summaries)
    assert all(summary.overall_readiness_score > 0 for summary in summaries)


@pytest.mark.asyncio
async def test_seed_demo_scenarios_preserve_visible_missing_and_pending_evidence(db_session):
    results = await seed_demo_scenarios(db_session)
    await db_session.commit()

    pending = (
        await db_session.execute(
            select(ExtractedFact).where(ExtractedFact.review_status == "pending")
        )
    ).scalars().all()

    assert {fact.schema_path for fact in pending} >= {
        "disclosure.risk-factors",
        "project.location.sitecontrol",
    }
    assert all(result["missing_evidence_paths"] for result in results)
    assert all("tax_certificate" not in {fact.schema_path for fact in pending} for result in results)


def test_golden_walkthrough_docs_exist_and_match_seed_metadata():
    for scenario in DEMO_SCENARIOS:
        path = Path(scenario.walkthrough_path)
        text = path.read_text(encoding="utf-8")
        assert scenario.name in text
        assert scenario.sector.capitalize() in text or scenario.sector in text
        for missing_path in scenario.missing_evidence_paths:
            assert missing_path in text
        assert "not legal advice" in text.lower() or "not claim" in text.lower()
