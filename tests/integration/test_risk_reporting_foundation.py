"""
Integration tests for Phase 5 Sprint 1 risk foundation diagnostics endpoint.
"""

import pytest

from munipal.config import get_settings


@pytest.fixture(autouse=True)
def clear_settings_cache():
    """Ensure env var changes are reflected per test."""
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def cohort_params() -> dict[str, str | int]:
    return {
        "sector": "waste_to_energy",
        "issuer_size_band": "mid",
        "deal_type": "revenue",
        "recency_window": "5y",
        "sample_size": 50,
    }


@pytest.fixture(autouse=True)
def use_jwt_auth_headers(test_client, auth_headers):
    """Run this suite against JWT-enforced auth without per-request boilerplate."""
    test_client.headers.update(auth_headers)
    yield
    test_client.headers.pop("Authorization", None)


@pytest.fixture
async def project_with_risk_job(factory, db_session):
    playbook = await factory.create_playbook()
    project = await factory.create_project(playbook["id"])
    artifact = await factory.create_artifact(project["id"])
    job = await factory.create_extraction_job(project["id"], artifact["id"])
    await db_session.commit()
    return {
        "project": project,
        "job": job,
    }


def _risk_fact_paths() -> list[tuple[str, str]]:
    return [
        ("risk.technology.description", "Technology risk"),
        ("risk.technology.mitigants", "Technology mitigant"),
        ("risk.construction.description", "Construction risk"),
        ("risk.construction.mitigants", "Construction mitigant"),
        ("risk.market.description", "Market risk"),
        ("risk.market.mitigants", "Market mitigant"),
        ("risk.regulatory.description", "Regulatory risk"),
        ("risk.regulatory.mitigants", "Regulatory mitigant"),
        ("risk.feedstock.description", "Feedstock risk"),
        ("risk.feedstock.mitigants", "Feedstock mitigant"),
    ]


@pytest.mark.asyncio
async def test_risk_diagnostics_complete_project_returns_all_dimensions(
    monkeypatch: pytest.MonkeyPatch,
    test_client,
    factory,
    db_session,
    project_with_risk_job,
    cohort_params,
):
    monkeypatch.setenv("RISK_REPORTING_V2_FOUNDATION", "true")

    project = project_with_risk_job["project"]
    job_id = project_with_risk_job["job"]["id"]

    for schema_path, value in _risk_fact_paths():
        await factory.create_fact(
            project_id=project["id"],
            extraction_job_id=job_id,
            schema_path=schema_path,
            value=value,
            review_status="approved",
            confidence_score=0.90,
            criticality="material",
        )
    await db_session.commit()

    response = await test_client.get(
        "/api/v1/risk/diagnostics",
        params={"project_id": project["id"], **cohort_params},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["cohort"]["sector"] == "waste_to_energy"
    assert data["cohort"]["sample_size"] == 50
    assert len(data["dimensions"]) == 5
    assert "overall_posture" in data
    assert "benchmark_position" in data["overall_posture"]
    assert "posture_score" in data["overall_posture"]
    assert "explanation" in data["overall_posture"]
    assert "guardrails" in data
    assert len(data["guardrails"]) >= 3
    for guardrail in data["guardrails"]:
        assert "guardrail_id" in guardrail
        assert "status" in guardrail
        assert "violation" in guardrail
        assert "threshold" in guardrail
        assert "evidence_paths" in guardrail
    assert "actions" in data
    assert len(data["actions"]) >= 1
    for action in data["actions"]:
        assert "action_id" in action
        assert "priority" in action
        assert "owner" in action
        assert "evidence_required" in action
        assert "source_refs" in action
    for dimension in data["dimensions"]:
        assert "dimension_id" in dimension
        assert "project_status" in dimension
        assert "gap_severity" in dimension
        assert "benchmark_position" in dimension
        assert "posture_score" in dimension
        assert "posture_explainer" in dimension
        assert "benchmark_stats" in dimension
        assert "confidence" in dimension


@pytest.mark.asyncio
async def test_risk_diagnostics_partial_project_returns_mixed_statuses(
    monkeypatch: pytest.MonkeyPatch,
    test_client,
    factory,
    db_session,
    project_with_risk_job,
    cohort_params,
):
    monkeypatch.setenv("RISK_REPORTING_V2_FOUNDATION", "true")

    project = project_with_risk_job["project"]
    job_id = project_with_risk_job["job"]["id"]

    await factory.create_fact(
        project_id=project["id"],
        extraction_job_id=job_id,
        schema_path="risk.technology.description",
        value="Technology risk exists",
        review_status="approved",
        confidence_score=0.95,
        criticality="material",
    )
    await db_session.commit()

    response = await test_client.get(
        "/api/v1/risk/diagnostics",
        params={"project_id": project["id"], **cohort_params},
    )

    assert response.status_code == 200
    data = response.json()
    statuses = {item["dimension_id"]: item["project_status"] for item in data["dimensions"]}
    assert statuses["risk.technology"] == "partial"
    assert any(status == "missing" for status in statuses.values())


@pytest.mark.asyncio
async def test_risk_diagnostics_low_sample_cohort_forces_low_reliability(
    monkeypatch: pytest.MonkeyPatch,
    test_client,
    project_with_risk_job,
):
    monkeypatch.setenv("RISK_REPORTING_V2_FOUNDATION", "true")

    project = project_with_risk_job["project"]
    response = await test_client.get(
        "/api/v1/risk/diagnostics",
        params={
            "project_id": project["id"],
            "sector": "waste_to_energy",
            "issuer_size_band": "mid",
            "deal_type": "revenue",
            "recency_window": "5y",
            "sample_size": 5,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert all(
        dimension["confidence"]["reliability_band"] == "low"
        for dimension in data["dimensions"]
    )
    assert any(
        dimension["confidence"]["uncertainty_note"]
        and "sample size below reliability threshold"
        in dimension["confidence"]["uncertainty_note"].lower()
        for dimension in data["dimensions"]
    )


@pytest.mark.asyncio
async def test_risk_diagnostics_hidden_when_feature_flag_disabled(
    monkeypatch: pytest.MonkeyPatch,
    test_client,
    project_with_risk_job,
    cohort_params,
):
    monkeypatch.setenv("RISK_REPORTING_V2_FOUNDATION", "false")

    project = project_with_risk_job["project"]
    response = await test_client.get(
        "/api/v1/risk/diagnostics",
        params={"project_id": project["id"], **cohort_params},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_risk_diagnostics_is_deterministic_for_same_inputs(
    monkeypatch: pytest.MonkeyPatch,
    test_client,
    factory,
    db_session,
    project_with_risk_job,
    cohort_params,
):
    monkeypatch.setenv("RISK_REPORTING_V2_FOUNDATION", "true")

    project = project_with_risk_job["project"]
    job_id = project_with_risk_job["job"]["id"]
    for schema_path, value in _risk_fact_paths():
        await factory.create_fact(
            project_id=project["id"],
            extraction_job_id=job_id,
            schema_path=schema_path,
            value=value,
            review_status="approved",
            confidence_score=0.90,
            criticality="material",
        )
    await db_session.commit()

    first = await test_client.get(
        "/api/v1/risk/diagnostics",
        params={"project_id": project["id"], **cohort_params},
    )
    second = await test_client.get(
        "/api/v1/risk/diagnostics",
        params={"project_id": project["id"], **cohort_params},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == second.json()


@pytest.mark.asyncio
async def test_risk_diagnostics_guardrails_expose_explicit_breaches(
    monkeypatch: pytest.MonkeyPatch,
    test_client,
    factory,
    db_session,
    project_with_risk_job,
    cohort_params,
):
    monkeypatch.setenv("RISK_REPORTING_V2_FOUNDATION", "true")

    project = project_with_risk_job["project"]
    job_id = project_with_risk_job["job"]["id"]
    for schema_path, value in _risk_fact_paths():
        await factory.create_fact(
            project_id=project["id"],
            extraction_job_id=job_id,
            schema_path=schema_path,
            value=value,
            review_status="approved",
            confidence_score=0.90,
            criticality="material",
        )

    quantitative_facts = [
        ("finmodel.inputs.dscr.minimum", 1.35),
        ("finmodel.outputs.dscrbase", 1.30),
        ("finmodel.outputs.dscrstress", 1.05),
        ("capital.equipment-cost", 80_000_000),
        ("capital.project-cost", 100_000_000),
    ]
    for schema_path, value in quantitative_facts:
        await factory.create_fact(
            project_id=project["id"],
            extraction_job_id=job_id,
            schema_path=schema_path,
            value=value,
            review_status="approved",
            confidence_score=0.95,
            criticality="critical",
        )
    await db_session.commit()

    response = await test_client.get(
        "/api/v1/risk/diagnostics",
        params={"project_id": project["id"], **cohort_params},
    )

    assert response.status_code == 200
    data = response.json()
    guardrails = {item["guardrail_id"]: item for item in data["guardrails"]}

    headroom = guardrails["guardrail.dscr.headroom"]
    assert headroom["status"] == "breach"
    assert headroom["violation"] is True
    assert headroom["benchmark_percentile_band"] is not None
    assert "finmodel.outputs.dscrbase" in headroom["evidence_paths"]
    assert "finmodel.inputs.dscr.minimum" in headroom["evidence_paths"]

    equipment_concentration = guardrails["guardrail.capital.equipment_concentration"]
    assert equipment_concentration["status"] == "breach"
    assert equipment_concentration["violation"] is True
    assert equipment_concentration["threshold"]["target_max"] == 0.65
    assert equipment_concentration["threshold"]["tolerance_max"] == 0.7
    assert guardrails["guardrail.dscr.scenario_sensitivity"]["status"] == "pass"
    assert guardrails["guardrail.dscr.ratio_consistency"]["status"] == "breach"

    actions = {item["action_id"]: item for item in data["actions"]}
    assert "action.dscr.coverage" in actions
    assert actions["action.dscr.coverage"]["priority"] == "high"
    assert "guardrail.dscr.headroom" in actions["action.dscr.coverage"]["source_refs"]
    assert "guardrail.dscr.stress_floor" in actions["action.dscr.coverage"]["source_refs"]
    assert "guardrail.dscr.ratio_consistency" in actions["action.dscr.coverage"]["source_refs"]


@pytest.mark.asyncio
async def test_risk_internal_report_contract_returns_json_and_markdown(
    monkeypatch: pytest.MonkeyPatch,
    test_client,
    factory,
    db_session,
    project_with_risk_job,
    cohort_params,
):
    monkeypatch.setenv("RISK_REPORTING_V2_FOUNDATION", "true")

    project = project_with_risk_job["project"]
    job_id = project_with_risk_job["job"]["id"]

    for schema_path, value in _risk_fact_paths():
        await factory.create_fact(
            project_id=project["id"],
            extraction_job_id=job_id,
            schema_path=schema_path,
            value=value,
            review_status="approved",
            confidence_score=0.90,
            criticality="material",
        )
    await db_session.commit()

    response = await test_client.get(
        "/api/v1/risk/internal-report",
        params={"project_id": project["id"], **cohort_params},
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["contract_version"] == "risk-internal-v1"
    assert payload["project_id"] == project["id"]
    assert "generated_at" in payload
    assert "executive_summary" in payload
    assert "diagnostics" in payload
    assert "readiness_input" in payload
    assert "advisory_input" in payload
    assert "markdown_report" in payload
    assert "Internal Risk Report" in payload["markdown_report"]
    assert "Guardrail Checks" in payload["markdown_report"]
    assert len(payload["diagnostics"]["dimensions"]) == 5


@pytest.mark.asyncio
async def test_risk_internal_report_hidden_when_feature_flag_disabled(
    monkeypatch: pytest.MonkeyPatch,
    test_client,
    project_with_risk_job,
    cohort_params,
):
    monkeypatch.setenv("RISK_REPORTING_V2_FOUNDATION", "false")

    project = project_with_risk_job["project"]
    response = await test_client.get(
        "/api/v1/risk/internal-report",
        params={"project_id": project["id"], **cohort_params},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_risk_external_brief_contract_suppresses_internal_fields(
    monkeypatch: pytest.MonkeyPatch,
    test_client,
    factory,
    db_session,
    project_with_risk_job,
    cohort_params,
):
    monkeypatch.setenv("RISK_REPORTING_V2_FOUNDATION", "true")

    project = project_with_risk_job["project"]
    job_id = project_with_risk_job["job"]["id"]
    for schema_path, value in _risk_fact_paths():
        await factory.create_fact(
            project_id=project["id"],
            extraction_job_id=job_id,
            schema_path=schema_path,
            value=value,
            review_status="approved",
            confidence_score=0.90,
            criticality="material",
        )
    await db_session.commit()

    response = await test_client.get(
        "/api/v1/risk/external-brief",
        params={"project_id": project["id"], **cohort_params},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["contract_version"] == "risk-external-v1"
    assert payload["interpretation_guide_version"] == "risk-consumer-guide-v1"
    assert payload["scoring_profile_version"].startswith("risk-scoring-profile-")
    assert payload["scoring_profile_checksum"] != "unknown"
    assert "diagnostics" not in payload
    assert "readiness_input" not in payload
    assert "advisory_input" not in payload
    assert "compliance_checks" in payload
    assert "consumer_interpretation_guide" in payload
    assert len(payload["consumer_interpretation_guide"]) >= 3
    assert all("[ref:" in assumption.lower() for assumption in payload["key_assumptions"])
    assert "markdown_brief" in payload
    assert "conflict_count" not in payload["markdown_brief"]


@pytest.mark.asyncio
async def test_risk_bfms_integration_contract_returns_full_mode_when_reliable(
    monkeypatch: pytest.MonkeyPatch,
    test_client,
    factory,
    db_session,
    project_with_risk_job,
    cohort_params,
):
    monkeypatch.setenv("RISK_REPORTING_V2_FOUNDATION", "true")

    project = project_with_risk_job["project"]
    job_id = project_with_risk_job["job"]["id"]
    for schema_path, value in _risk_fact_paths():
        await factory.create_fact(
            project_id=project["id"],
            extraction_job_id=job_id,
            schema_path=schema_path,
            value=value,
            review_status="approved",
            confidence_score=0.95,
            criticality="material",
        )
    await db_session.commit()

    response = await test_client.get(
        "/api/v1/risk/bfms-integration",
        params={"project_id": project["id"], **cohort_params},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["contract_version"] == "risk-bfms-integration-v1"
    assert payload["interpretation_guide_version"] == "risk-consumer-guide-v1"
    assert payload["scoring_profile_version"].startswith("risk-scoring-profile-")
    assert payload["scoring_profile_checksum"] != "unknown"
    assert payload["integration_mode"] == "full"
    assert payload["fallback_reasons"] == []
    assert payload["directional_guidance_only"] is False
    assert payload["internal_report_contract_version"] == "risk-internal-v1"
    assert payload["external_brief_contract_version"] == "risk-external-v1"
    assert len(payload["consumer_interpretation_guide"]) >= 3
    assert "overall_benchmark_position" in payload
    assert "overall_posture_score" in payload


@pytest.mark.asyncio
async def test_risk_bfms_integration_contract_falls_back_for_low_reliability(
    monkeypatch: pytest.MonkeyPatch,
    test_client,
    project_with_risk_job,
):
    monkeypatch.setenv("RISK_REPORTING_V2_FOUNDATION", "true")

    project = project_with_risk_job["project"]
    response = await test_client.get(
        "/api/v1/risk/bfms-integration",
        params={
            "project_id": project["id"],
            "sector": "waste_to_energy",
            "issuer_size_band": "mid",
            "deal_type": "revenue",
            "recency_window": "5y",
            "sample_size": 5,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["interpretation_guide_version"] == "risk-consumer-guide-v1"
    assert payload["integration_mode"] == "fallback"
    assert payload["directional_guidance_only"] is True
    assert payload["reliability_low_dimensions"] >= 1
    assert len(payload["fallback_reasons"]) >= 1
    assert any("fallback" in item.lower() for item in payload["consumer_interpretation_guide"])


@pytest.mark.asyncio
async def test_risk_bfms_integration_hidden_when_feature_flag_disabled(
    monkeypatch: pytest.MonkeyPatch,
    test_client,
    project_with_risk_job,
    cohort_params,
):
    monkeypatch.setenv("RISK_REPORTING_V2_FOUNDATION", "false")

    project = project_with_risk_job["project"]
    response = await test_client.get(
        "/api/v1/risk/bfms-integration",
        params={"project_id": project["id"], **cohort_params},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_risk_sync_information_requests_creates_and_refreshes_requests(
    monkeypatch: pytest.MonkeyPatch,
    test_client,
    project_with_risk_job,
    cohort_params,
):
    monkeypatch.setenv("RISK_REPORTING_V2_FOUNDATION", "true")

    project = project_with_risk_job["project"]
    first = await test_client.post(
        "/api/v1/risk/sync-information-requests",
        params={"project_id": project["id"], **cohort_params},
    )
    assert first.status_code == 200
    first_payload = first.json()
    assert first_payload["created_count"] >= 1
    assert first_payload["total_actions"] >= 1

    second = await test_client.post(
        "/api/v1/risk/sync-information-requests",
        params={"project_id": project["id"], **cohort_params},
    )
    assert second.status_code == 200
    second_payload = second.json()
    assert second_payload["created_count"] == 0
    assert second_payload["updated_count"] >= 1

    requests_response = await test_client.get(
        "/api/v1/information-requests/",
        params={"project_id": project["id"], "limit": 200},
    )
    assert requests_response.status_code == 200
    requests_payload = requests_response.json()
    assert requests_payload["total"] >= first_payload["created_count"]
    assert any(
        request["title"] and "risk" in request["title"].lower()
        for request in requests_payload["requests"]
    )


@pytest.mark.asyncio
async def test_risk_override_and_action_acceptance_endpoints(
    monkeypatch: pytest.MonkeyPatch,
    test_client,
    project_with_risk_job,
):
    monkeypatch.setenv("RISK_REPORTING_V2_FOUNDATION", "true")
    project = project_with_risk_job["project"]

    override_response = await test_client.post(
        "/api/v1/risk/overrides",
        json={
            "project_id": project["id"],
            "target_ref": "risk.technology",
            "reason": "Reviewed with engineering lead and updated risk posture.",
            "previous_value": "above",
            "override_value": "at",
            "notes": "Pending final vendor package.",
        },
    )
    assert override_response.status_code == 200
    override_payload = override_response.json()
    assert override_payload["project_id"] == project["id"]
    assert override_payload["target_ref"] == "risk.technology"
    assert "decision_id" in override_payload
    assert "recorded_at" in override_payload

    acceptance_response = await test_client.post(
        "/api/v1/risk/actions/action.dscr.coverage/accept",
        json={
            "project_id": project["id"],
            "reason": "Execution owner confirmed and evidence plan approved.",
            "notes": "Kickoff this week.",
        },
    )
    assert acceptance_response.status_code == 200
    acceptance_payload = acceptance_response.json()
    assert acceptance_payload["project_id"] == project["id"]
    assert acceptance_payload["action_id"] == "action.dscr.coverage"
    assert "accepted_at" in acceptance_payload


@pytest.mark.asyncio
async def test_risk_validation_corpus_drift_guard_sparse_profile(
    monkeypatch: pytest.MonkeyPatch,
    test_client,
    project_with_risk_job,
):
    monkeypatch.setenv("RISK_REPORTING_V2_FOUNDATION", "true")
    project = project_with_risk_job["project"]

    response = await test_client.get(
        "/api/v1/risk/diagnostics",
        params={
            "project_id": project["id"],
            "sector": "waste_to_energy",
            "issuer_size_band": "mid",
            "deal_type": "revenue",
            "recency_window": "5y",
            "sample_size": 50,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    observed = payload["overall_posture"]["posture_score"]
    expected = 0.78
    tolerance = 0.01
    assert abs(observed - expected) <= tolerance, (
        f"sparse corpus drift: expected {expected}, got {observed}"
    )


@pytest.mark.asyncio
async def test_risk_validation_corpus_drift_guard_complete_profile(
    monkeypatch: pytest.MonkeyPatch,
    test_client,
    factory,
    db_session,
    project_with_risk_job,
):
    monkeypatch.setenv("RISK_REPORTING_V2_FOUNDATION", "true")
    project = project_with_risk_job["project"]
    job_id = project_with_risk_job["job"]["id"]

    for schema_path, value in _risk_fact_paths():
        await factory.create_fact(
            project_id=project["id"],
            extraction_job_id=job_id,
            schema_path=schema_path,
            value=value,
            review_status="approved",
            confidence_score=0.95,
            criticality="material",
        )
    await db_session.commit()

    response = await test_client.get(
        "/api/v1/risk/diagnostics",
        params={
            "project_id": project["id"],
            "sector": "waste_to_energy",
            "issuer_size_band": "mid",
            "deal_type": "revenue",
            "recency_window": "5y",
            "sample_size": 50,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    observed = payload["overall_posture"]["posture_score"]
    expected = 0.25
    tolerance = 0.01
    assert abs(observed - expected) <= tolerance, (
        f"complete corpus drift: expected {expected}, got {observed}"
    )


@pytest.mark.asyncio
async def test_risk_diagnostics_applies_advanced_analytics_when_gate_passes(
    monkeypatch: pytest.MonkeyPatch,
    test_client,
    factory,
    db_session,
    project_with_risk_job,
):
    monkeypatch.setenv("RISK_REPORTING_V2_FOUNDATION", "true")
    monkeypatch.setenv("RISK_REPORTING_V2_ADVANCED_ANALYTICS", "true")
    monkeypatch.setenv("RISK_REPORTING_V2_ADVANCED_MIN_RELIABILITY", "high")

    project = project_with_risk_job["project"]
    job_id = project_with_risk_job["job"]["id"]

    for schema_path, value in _risk_fact_paths():
        await factory.create_fact(
            project_id=project["id"],
            extraction_job_id=job_id,
            schema_path=schema_path,
            value=value,
            review_status="approved",
            confidence_score=0.95,
            criticality="material",
        )

    advanced_fact_rows = [
        ("analytics.extended_risk.technology.spectral_omega", 1.20),
        ("analytics.extended_risk.technology.wavelet_omega", 1.15),
        ("analytics.extended_risk.technology.dynamic_omega", 1.10),
    ]
    for schema_path, value in advanced_fact_rows:
        await factory.create_fact(
            project_id=project["id"],
            extraction_job_id=job_id,
            schema_path=schema_path,
            value=value,
            review_status="approved",
            confidence_score=0.95,
            criticality="material",
        )
    await db_session.commit()

    response = await test_client.get(
        "/api/v1/risk/diagnostics",
        params={
            "project_id": project["id"],
            "sector": "waste_to_energy",
            "issuer_size_band": "mid",
            "deal_type": "revenue",
            "recency_window": "5y",
            "sample_size": 50,
        },
    )
    assert response.status_code == 200
    payload = response.json()

    dimensions = {d["dimension_id"]: d for d in payload["dimensions"]}
    technology = dimensions["risk.technology"]
    assert technology["advanced_analytics_applied"] is True
    assert technology["advanced_metrics"]["spectral_omega"] == 1.2
    assert "applied advanced analytics bridge" in (
        technology["advanced_analytics_note"] or ""
    ).lower()
