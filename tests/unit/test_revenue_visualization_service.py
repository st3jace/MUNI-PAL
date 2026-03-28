from uuid import UUID

import pytest

from munipal.services.revenue_visualization_service import RevenueVisualizationService


@pytest.mark.asyncio
async def test_revenue_visualization_service_infers_future_streams_from_core_revenue(
    factory,
    db_session,
) -> None:
    playbook = await factory.create_playbook()
    project = await factory.create_project(playbook["id"])
    artifact = await factory.create_artifact(project["id"])
    job = await factory.create_extraction_job(project["id"], artifact["id"])

    facts = [
        ("revenue.commodities.renewable-diesel", 10_121_436),
        ("revenue.commodities.biochar", 175_500),
        ("revenue.gross.annual", 14_865_836),
        ("finmodel.outputs.dscrbase", 2.8),
        ("finmodel.outputs.dscrstress", 2.1),
        ("finmodel.inputs.dscr.minimum", 1.35),
    ]
    for schema_path, value in facts:
        await factory.create_fact(
            project_id=project["id"],
            extraction_job_id=job["id"],
            schema_path=schema_path,
            value=value,
            review_status="approved",
            confidence_score=0.95,
            criticality="material",
        )
    await db_session.commit()

    service = RevenueVisualizationService(db_session)
    payload = await service.build_visualization(UUID(project["id"]))

    assert payload.project_id == UUID(project["id"])
    assert [scenario.scenario_id for scenario in payload.revenue_scenarios] == [
        "current_state",
        "base_case",
        "full_diversification",
    ]
    current, base_case, full = payload.revenue_scenarios

    assert {stream.stream_id for stream in current.revenue_streams} == {"diesel", "biochar"}
    assert any(stream.stream_id == "electricity" for stream in base_case.revenue_streams)
    assert any(stream.stream_id == "tipping" for stream in base_case.revenue_streams)
    assert any(stream.stream_id == "carbon" for stream in full.revenue_streams)
    assert any(stream.is_inferred for stream in base_case.revenue_streams if stream.stream_id == "electricity")
    assert base_case.total_revenue > current.total_revenue
    assert full.total_revenue > base_case.total_revenue
    assert full.dscr_mean > base_case.dscr_mean > current.dscr_mean
    assert payload.debt_service_annual > 0
    assert payload.covenant_trigger_dscr == pytest.approx(1.35)
    assert payload.data_quality_notes


@pytest.mark.asyncio
async def test_revenue_visualization_service_applies_caldor_packet_override(
    factory,
    db_session,
) -> None:
    playbook = await factory.create_playbook()
    project = await factory.create_project(playbook["id"], name="UCS Caldor 2026")
    await db_session.commit()

    service = RevenueVisualizationService(db_session)
    payload = await service.build_visualization(UUID(project["id"]))

    assert payload.project_name == "UCS Caldor 2026"
    assert payload.debt_service_annual == pytest.approx(3_661_000.0)
    assert payload.non_diesel_combined_coverage_dscr == pytest.approx(1.84)
    assert payload.non_diesel_senior_coverage_dscr == pytest.approx(4.32)
    assert payload.risk_proof is not None
    assert payload.risk_proof.title == "Diversification Proof (S06 vs S08)"
    assert [scenario.label for scenario in payload.revenue_scenarios] == [
        "Diesel + Biochar",
        "+ Electricity PPA",
        "Full Diversification",
    ]
    assert payload.revenue_scenarios[0].dscr_mean == pytest.approx(1.52)
    assert payload.revenue_scenarios[0].breach_weeks == 25
    assert payload.revenue_scenarios[1].dscr_mean == pytest.approx(2.04)
    assert payload.revenue_scenarios[1].dscr_minimum == pytest.approx(1.76)
    assert payload.revenue_scenarios[1].dscr_parity_diesel_price == pytest.approx(2.25)
    assert payload.revenue_scenarios[2].dscr_mean == pytest.approx(3.14)
    assert payload.revenue_scenarios[2].dscr_minimum == pytest.approx(2.80)
    assert payload.revenue_scenarios[2].breach_weeks == 0
    assert payload.revenue_scenarios[2].total_revenue == pytest.approx(16_862_310.0)


@pytest.mark.asyncio
async def test_revenue_visualization_service_can_bypass_caldor_packet_override_in_native_mode(
    factory,
    db_session,
) -> None:
    playbook = await factory.create_playbook()
    project = await factory.create_project(playbook["id"], name="UCS Caldor 2026")
    artifact = await factory.create_artifact(project["id"])
    job = await factory.create_extraction_job(project["id"], artifact["id"])

    for schema_path, value in [
        ("revenue.commodities.renewable-diesel", 10_121_436),
        ("revenue.commodities.biochar", 175_500),
        ("revenue.gross.annual", 14_865_836),
        ("finmodel.outputs.dscrbase", 2.8),
        ("finmodel.outputs.dscrstress", 2.1),
        ("finmodel.inputs.dscr.minimum", 1.35),
    ]:
        await factory.create_fact(
            project_id=project["id"],
            extraction_job_id=job["id"],
            schema_path=schema_path,
            value=value,
            review_status="approved",
            confidence_score=0.95,
            criticality="material",
        )
    await db_session.commit()

    service = RevenueVisualizationService(db_session)
    payload = await service.build_visualization(UUID(project["id"]), mode="native")

    assert payload.risk_proof is None
    assert payload.non_diesel_combined_coverage_dscr is None
    assert [scenario.label for scenario in payload.revenue_scenarios] == [
        "Current State",
        "Base Case",
        "Full Diversification",
    ]
