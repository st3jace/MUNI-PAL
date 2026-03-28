import pytest


@pytest.fixture(autouse=True)
def use_jwt_auth_headers(test_client, auth_headers):
    test_client.headers.update(auth_headers)
    yield
    test_client.headers.pop("Authorization", None)


@pytest.mark.asyncio
async def test_revenue_diversification_endpoint_returns_typed_visualization_payload(
    test_client,
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
        ("revenue.commodities.electricity", 4_043_900),
        ("revenue.commodities.tipping", 525_000),
        ("revenue.commodities.carbon", 750_000),
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

    response = await test_client.get(
        "/api/v1/risk/revenue-diversification",
        params={"project_id": project["id"]},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["contract_version"] == "revenue-diversification-v1"
    assert data["project_id"] == project["id"]
    assert data["debt_service_annual"] > 0
    assert data["covenant_trigger_dscr"] == pytest.approx(1.35)
    assert len(data["stream_definitions"]) == 5
    assert [scenario["scenario_id"] for scenario in data["revenue_scenarios"]] == [
        "current_state",
        "base_case",
        "full_diversification",
    ]

    full = data["revenue_scenarios"][2]
    assert any(stream["stream_id"] == "carbon" for stream in full["revenue_streams"])
    assert full["breach_weeks"] >= 0
    assert full["dscr_mean"] >= data["revenue_scenarios"][1]["dscr_mean"]


@pytest.mark.asyncio
async def test_revenue_diversification_endpoint_applies_caldor_packet_overlay(
    test_client,
    factory,
    db_session,
) -> None:
    playbook = await factory.create_playbook()
    project = await factory.create_project(playbook["id"], name="UCS Caldor 2026")
    await db_session.commit()

    response = await test_client.get(
        "/api/v1/risk/revenue-diversification",
        params={"project_id": project["id"]},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["debt_service_annual"] == pytest.approx(3_661_000.0)
    assert data["non_diesel_combined_coverage_dscr"] == pytest.approx(1.84)
    assert data["risk_proof"]["title"] == "Diversification Proof (S06 vs S08)"
    assert data["revenue_scenarios"][0]["label"] == "Diesel + Biochar"
    assert data["revenue_scenarios"][0]["dscr_mean"] == pytest.approx(1.52)
    assert data["revenue_scenarios"][0]["breach_weeks"] == 25
    assert data["revenue_scenarios"][1]["dscr_mean"] == pytest.approx(2.04)
    assert data["revenue_scenarios"][1]["dscr_minimum"] == pytest.approx(1.76)
    assert data["revenue_scenarios"][1]["dscr_parity_diesel_price"] == pytest.approx(2.25)
    assert data["revenue_scenarios"][2]["dscr_mean"] == pytest.approx(3.14)
    assert data["revenue_scenarios"][2]["dscr_minimum"] == pytest.approx(2.80)
    assert data["revenue_scenarios"][2]["breach_weeks"] == 0
    assert data["revenue_scenarios"][2]["covenant_trigger_diesel_price"] == pytest.approx(1.44)


@pytest.mark.asyncio
async def test_revenue_diversification_endpoint_can_return_native_view_for_caldor_project(
    test_client,
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

    response = await test_client.get(
        "/api/v1/risk/revenue-diversification",
        params={"project_id": project["id"], "mode": "native"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["risk_proof"] is None
    assert data["revenue_scenarios"][0]["label"] == "Current State"
    assert data["revenue_scenarios"][1]["dscr_parity_diesel_price"] is None
