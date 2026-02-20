"""
Unit tests for risk reporting foundation service.
"""

from types import SimpleNamespace
from uuid import uuid4

import pytest
from pydantic import ValidationError
from sqlalchemy import select

from munipal.config import get_settings
from munipal.core.schemas.risk_reporting import (
    RiskActionItem,
    RiskActionPriority,
    RiskBenchmarkCohort,
    RiskBenchmarkPosition,
    RiskBenchmarkStats,
    RiskConfidence,
    RiskDiagnosticsResponse,
    RiskExternalBriefResponse,
    RiskGapSeverity,
    RiskGuardrailCheck,
    RiskGuardrailStatus,
    RiskGuardrailThreshold,
    RiskInternalReportResponse,
    RiskOverallPosture,
    RiskReliabilityBand,
)
from munipal.core.models.information_request import InformationRequest
from munipal.core.schemas.information_request import RequestStatus
from munipal.services.risk_reporting_service import ADVANCED_ANALYTICS_PATHS, RiskReportingService


def test_risk_schema_roundtrip_serialization():
    payload = RiskDiagnosticsResponse(
        project_id=uuid4(),
        cohort=RiskBenchmarkCohort(
            sector="waste_to_energy",
            issuer_size_band="mid",
            deal_type="revenue",
            recency_window="5y",
            sample_size=42,
        ),
        dimensions=[],
        overall_posture=RiskOverallPosture(
            benchmark_position=RiskBenchmarkPosition.AT,
            posture_score=0.5,
            explanation="Baseline posture",
        ),
        guardrails=[
            RiskGuardrailCheck(
                guardrail_id="guardrail.test",
                metric_name="Test guardrail",
                status=RiskGuardrailStatus.PASS,
                violation=False,
                observed_value=1.0,
                unit="x",
                benchmark_percentile_band="p50-p75",
                threshold=RiskGuardrailThreshold(target_min=0.8, tolerance_min=0.7),
                evidence_paths=["finmodel.outputs.dscrbase"],
                rationale="Test rationale",
            )
        ],
        actions=[
            RiskActionItem(
                action_id="action.test",
                priority=RiskActionPriority.MEDIUM,
                owner="Test Owner",
                title="Test action",
                rationale="Test rationale",
                evidence_required=["risk.technology.description"],
                target_date_hint="14 days",
                expected_impact="Improves test posture",
                source_refs=["risk.technology"],
            )
        ],
    )

    serialized = payload.model_dump()
    reparsed = RiskDiagnosticsResponse.model_validate(serialized)

    assert reparsed.project_id == payload.project_id
    assert reparsed.cohort.sample_size == 42


def test_cohort_validator_requires_positive_sample_size():
    with pytest.raises(ValidationError):
        RiskBenchmarkCohort(
            sector="waste_to_energy",
            issuer_size_band="mid",
            deal_type="revenue",
            recency_window="5y",
            sample_size=0,
        )


@pytest.mark.asyncio
async def test_reliability_low_when_sample_size_below_threshold(db_session):
    service = RiskReportingService(db_session)

    confidence = service._compute_confidence(
        sample_size=10,
        evidence_count=2,
        conflict_count=0,
    )

    assert confidence.reliability_band == RiskReliabilityBand.LOW
    assert confidence.uncertainty_note is not None
    assert "sample size below reliability threshold" in confidence.uncertainty_note.lower()


@pytest.mark.asyncio
async def test_reliability_downgrades_with_high_conflict_rate(db_session):
    service = RiskReportingService(db_session)

    confidence = service._compute_confidence(
        sample_size=80,
        evidence_count=2,
        conflict_count=1,  # conflict rate 0.5
    )

    assert confidence.reliability_band != RiskReliabilityBand.HIGH
    assert confidence.uncertainty_note is not None
    assert "high conflict rate" in confidence.uncertainty_note.lower()


@pytest.mark.asyncio
async def test_reliability_marks_missing_source_quality_inputs(db_session):
    service = RiskReportingService(db_session)

    confidence = service._compute_confidence(
        sample_size=80,
        evidence_count=0,
        conflict_count=0,
    )

    assert confidence.uncertainty_note is not None
    assert "source quality inputs missing" in confidence.uncertainty_note.lower()


@pytest.mark.asyncio
async def test_position_from_delta_uses_neutral_band(db_session):
    service = RiskReportingService(db_session)

    assert (
        service._position_from_delta(delta=0.25, neutral_band=0.18)
        == RiskBenchmarkPosition.ABOVE
    )
    assert (
        service._position_from_delta(delta=-0.25, neutral_band=0.18)
        == RiskBenchmarkPosition.BELOW
    )
    assert (
        service._position_from_delta(delta=0.10, neutral_band=0.18)
        == RiskBenchmarkPosition.AT
    )


@pytest.mark.asyncio
async def test_dimension_posture_scoring_produces_explainer_and_position(db_session):
    service = RiskReportingService(db_session)
    benchmark_stats = RiskBenchmarkStats(
        n_issuances=50,
        n_disclosures=100,
        mitigation_rate=0.70,
        severity_distribution={"high": 0.25, "medium": 0.50, "low": 0.25},
    )
    confidence = RiskConfidence(
        score=0.80,
        reliability_band=RiskReliabilityBand.HIGH,
        uncertainty_note=None,
    )

    position, posture_score, explainer = service._score_dimension_posture(
        gap_severity=RiskGapSeverity.HIGH,
        benchmark_stats=benchmark_stats,
        confidence=confidence,
        evidence_count=4,
        conflict_count=0,
    )

    assert position == RiskBenchmarkPosition.ABOVE
    assert posture_score > 0.70
    assert "cohort baseline risk" in explainer.lower()


@pytest.mark.asyncio
async def test_dimension_posture_scoring_can_return_below_corpus(db_session):
    service = RiskReportingService(db_session)
    benchmark_stats = RiskBenchmarkStats(
        n_issuances=50,
        n_disclosures=100,
        mitigation_rate=0.55,
        severity_distribution={"high": 0.30, "medium": 0.45, "low": 0.25},
    )
    confidence = RiskConfidence(
        score=0.80,
        reliability_band=RiskReliabilityBand.HIGH,
        uncertainty_note=None,
    )

    position, posture_score, _ = service._score_dimension_posture(
        gap_severity=RiskGapSeverity.LOW,
        benchmark_stats=benchmark_stats,
        confidence=confidence,
        evidence_count=4,
        conflict_count=0,
    )

    assert position == RiskBenchmarkPosition.BELOW
    assert posture_score < 0.30


@pytest.mark.asyncio
async def test_numeric_coercion_supports_string_with_suffix(db_session):
    service = RiskReportingService(db_session)

    assert service._coerce_numeric_value("1.37x") == 1.37
    assert service._coerce_numeric_value("65%") == 65.0


@pytest.mark.asyncio
async def test_guardrail_status_minimum_thresholds(db_session):
    service = RiskReportingService(db_session)

    assert (
        service._status_for_minimum(observed_value=0.16, target_min=0.15, tolerance_min=0.05)
        == RiskGuardrailStatus.PASS
    )
    assert (
        service._status_for_minimum(observed_value=0.10, target_min=0.15, tolerance_min=0.05)
        == RiskGuardrailStatus.WATCH
    )
    assert (
        service._status_for_minimum(observed_value=0.01, target_min=0.15, tolerance_min=0.05)
        == RiskGuardrailStatus.BREACH
    )


@pytest.mark.asyncio
async def test_synthesize_actions_deduplicates_dscr_guardrails(db_session):
    service = RiskReportingService(db_session)
    guardrails = [
        RiskGuardrailCheck(
            guardrail_id="guardrail.dscr.headroom",
            metric_name="DSCR covenant headroom",
            status=RiskGuardrailStatus.BREACH,
            violation=True,
            observed_value=-0.05,
            unit="x",
            benchmark_percentile_band="p0-p25",
            threshold=RiskGuardrailThreshold(target_min=0.15, tolerance_min=0.05),
            evidence_paths=["finmodel.outputs.dscrbase", "finmodel.inputs.dscr.minimum"],
            rationale="Headroom below tolerance.",
        ),
        RiskGuardrailCheck(
            guardrail_id="guardrail.dscr.stress_floor",
            metric_name="Stress DSCR floor",
            status=RiskGuardrailStatus.WATCH,
            violation=False,
            observed_value=1.20,
            unit="x",
            benchmark_percentile_band="p25-p50",
            threshold=RiskGuardrailThreshold(target_min=1.25, tolerance_min=1.15),
            evidence_paths=["finmodel.outputs.dscrstress", "finmodel.inputs.dscr.minimum"],
            rationale="Stress DSCR below target.",
        ),
    ]

    actions = service._synthesize_actions(dimensions=[], guardrails=guardrails)
    dscr_actions = [a for a in actions if a.action_id == "action.dscr.coverage"]

    assert len(dscr_actions) == 1
    dscr_action = dscr_actions[0]
    assert dscr_action.priority == RiskActionPriority.HIGH
    assert "guardrail.dscr.headroom" in dscr_action.source_refs
    assert "guardrail.dscr.stress_floor" in dscr_action.source_refs
    assert "finmodel.outputs.dscrbase" in dscr_action.evidence_required
    assert "finmodel.outputs.dscrstress" in dscr_action.evidence_required


@pytest.mark.asyncio
async def test_build_internal_report_returns_contract(db_session):
    service = RiskReportingService(db_session)
    cohort = RiskBenchmarkCohort(
        sector="waste_to_energy",
        issuer_size_band="mid",
        deal_type="revenue",
        recency_window="5y",
        sample_size=42,
    )

    report = await service.build_internal_report(project_id=uuid4(), cohort=cohort)

    assert isinstance(report, RiskInternalReportResponse)
    assert report.contract_version == "risk-internal-v1"
    assert report.diagnostics.project_id == report.project_id
    assert len(report.diagnostics.dimensions) == 5
    assert len(report.markdown_report) > 0


@pytest.mark.asyncio
async def test_build_external_brief_returns_sanitized_contract(db_session):
    service = RiskReportingService(db_session)
    cohort = RiskBenchmarkCohort(
        sector="waste_to_energy",
        issuer_size_band="mid",
        deal_type="revenue",
        recency_window="5y",
        sample_size=42,
    )

    brief = await service.build_external_brief(project_id=uuid4(), cohort=cohort)

    assert isinstance(brief, RiskExternalBriefResponse)
    assert brief.contract_version == "risk-external-v1"
    serialized = brief.model_dump()
    assert "diagnostics" not in serialized
    assert "readiness_input" not in serialized
    assert "advisory_input" not in serialized
    assert all("conflict" not in statement.statement.lower() for statement in brief.material_risk_statements)
    assert len(brief.markdown_brief) > 0


@pytest.mark.asyncio
async def test_sync_actions_to_information_requests_creates_and_updates(db_session):
    service = RiskReportingService(db_session)
    project_id = uuid4()
    actions = [
        RiskActionItem(
            action_id="action.dscr.coverage",
            priority=RiskActionPriority.HIGH,
            owner="Financial Advisor / Sponsor",
            title="Strengthen DSCR coverage and covenant cushion",
            rationale="DSCR guardrail is breached.",
            evidence_required=["finmodel.outputs.dscrbase", "finmodel.inputs.dscr.minimum"],
            target_date_hint="7 days",
            expected_impact="Improves debt-service resilience.",
            source_refs=["guardrail.dscr.headroom"],
        )
    ]

    first = await service.sync_actions_to_information_requests(project_id=project_id, actions=actions)
    assert first.total_actions == 1
    assert first.created_count == 1
    assert first.updated_count == 0

    actions[0] = RiskActionItem(
        action_id="action.dscr.coverage",
        priority=RiskActionPriority.MEDIUM,
        owner="Financial Advisor / Sponsor",
        title="Refresh DSCR coverage package",
        rationale="DSCR remains within watch band.",
        evidence_required=["finmodel.outputs.dscrstress"],
        target_date_hint="14 days",
        expected_impact="Sustains covenant resilience visibility.",
        source_refs=["guardrail.dscr.stress_floor"],
    )
    second = await service.sync_actions_to_information_requests(project_id=project_id, actions=actions)
    assert second.created_count == 0
    assert second.updated_count == 1

    result = await db_session.execute(
        select(InformationRequest).where(InformationRequest.project_id == str(project_id))
    )
    requests = list(result.scalars().all())
    assert len(requests) == 1
    assert requests[0].title == "Refresh DSCR coverage package"
    assert requests[0].priority in {"medium", "critical", "high"}


@pytest.mark.asyncio
async def test_sync_actions_to_information_requests_skips_resolved(db_session):
    service = RiskReportingService(db_session)
    project_id = uuid4()
    action = RiskActionItem(
        action_id="action.risk_technology.coverage",
        priority=RiskActionPriority.HIGH,
        owner="Independent Engineer / Sponsor",
        title="Close evidence coverage for risk.technology",
        rationale="Dimension status is missing with high gap severity.",
        evidence_required=["risk.technology.description", "risk.technology.mitigants"],
        target_date_hint="7 days",
        expected_impact="Improves benchmark posture stability.",
        source_refs=["risk.technology"],
    )

    first = await service.sync_actions_to_information_requests(project_id=project_id, actions=[action])
    assert first.created_count == 1

    request_id = first.synced_requests[0].request_id
    assert request_id is not None
    record = await db_session.get(InformationRequest, str(request_id))
    assert record is not None
    record.status = RequestStatus.RESOLVED.value
    await db_session.flush()

    second = await service.sync_actions_to_information_requests(project_id=project_id, actions=[action])
    assert second.created_count == 0
    assert second.updated_count == 0
    assert second.skipped_count == 1


@pytest.mark.asyncio
async def test_advanced_analytics_bridge_applies_when_enabled_and_reliable(
    db_session,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("RISK_REPORTING_V2_ADVANCED_ANALYTICS", "true")
    monkeypatch.setenv("RISK_REPORTING_V2_ADVANCED_MIN_RELIABILITY", "high")
    get_settings.cache_clear()
    service = RiskReportingService(db_session)

    paths = ADVANCED_ANALYTICS_PATHS["risk.technology"]
    approved_by_path = {
        paths["spectral_omega"]: [SimpleNamespace(value=1.20)],
        paths["wavelet_omega"]: [SimpleNamespace(value=1.15)],
        paths["dynamic_omega"]: [SimpleNamespace(value=1.10)],
    }
    confidence = RiskConfidence(
        score=0.92,
        reliability_band=RiskReliabilityBand.HIGH,
        uncertainty_note=None,
    )
    benchmark_stats = RiskBenchmarkStats(
        n_issuances=40,
        n_disclosures=80,
        mitigation_rate=0.70,
        severity_distribution={"high": 0.2, "medium": 0.5, "low": 0.3},
    )

    (
        position,
        score,
        explainer,
        metrics,
        applied,
        note,
    ) = service._apply_advanced_analytics(
        settings=get_settings(),
        dimension_id="risk.technology",
        approved_by_path=approved_by_path,
        confidence=confidence,
        benchmark_stats=benchmark_stats,
        benchmark_position=RiskBenchmarkPosition.AT,
        posture_score=0.52,
        posture_explainer="Baseline explainer.",
    )

    assert applied is True
    assert len(metrics) == 3
    assert score < 0.52
    assert isinstance(position, RiskBenchmarkPosition)
    assert "advanced analytics adjustment" in explainer.lower()
    assert note is not None and "applied advanced analytics bridge" in note.lower()
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_advanced_analytics_bridge_blocks_when_reliability_below_gate(
    db_session,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("RISK_REPORTING_V2_ADVANCED_ANALYTICS", "true")
    monkeypatch.setenv("RISK_REPORTING_V2_ADVANCED_MIN_RELIABILITY", "high")
    get_settings.cache_clear()
    service = RiskReportingService(db_session)

    paths = ADVANCED_ANALYTICS_PATHS["risk.technology"]
    approved_by_path = {
        paths["spectral_omega"]: [SimpleNamespace(value=1.20)],
        paths["wavelet_omega"]: [SimpleNamespace(value=1.15)],
    }
    confidence = RiskConfidence(
        score=0.40,
        reliability_band=RiskReliabilityBand.LOW,
        uncertainty_note="low confidence",
    )
    benchmark_stats = RiskBenchmarkStats(
        n_issuances=10,
        n_disclosures=20,
        mitigation_rate=0.60,
        severity_distribution={"high": 0.3, "medium": 0.4, "low": 0.3},
    )

    (
        _position,
        score,
        _explainer,
        metrics,
        applied,
        note,
    ) = service._apply_advanced_analytics(
        settings=get_settings(),
        dimension_id="risk.technology",
        approved_by_path=approved_by_path,
        confidence=confidence,
        benchmark_stats=benchmark_stats,
        benchmark_position=RiskBenchmarkPosition.ABOVE,
        posture_score=0.78,
        posture_explainer="Baseline explainer.",
    )

    assert applied is False
    assert metrics == {}
    assert score == 0.78
    assert note is not None and "below required high" in note.lower()
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_advanced_analytics_bridge_disabled_by_default(db_session, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("RISK_REPORTING_V2_ADVANCED_ANALYTICS", raising=False)
    get_settings.cache_clear()
    service = RiskReportingService(db_session)

    confidence = RiskConfidence(
        score=0.90,
        reliability_band=RiskReliabilityBand.HIGH,
        uncertainty_note=None,
    )
    benchmark_stats = RiskBenchmarkStats(
        n_issuances=40,
        n_disclosures=80,
        mitigation_rate=0.70,
        severity_distribution={"high": 0.2, "medium": 0.5, "low": 0.3},
    )

    (
        _position,
        score,
        _explainer,
        metrics,
        applied,
        note,
    ) = service._apply_advanced_analytics(
        settings=get_settings(),
        dimension_id="risk.technology",
        approved_by_path={},
        confidence=confidence,
        benchmark_stats=benchmark_stats,
        benchmark_position=RiskBenchmarkPosition.AT,
        posture_score=0.52,
        posture_explainer="Baseline explainer.",
    )

    assert applied is False
    assert metrics == {}
    assert score == 0.52
    assert note is not None and "disabled" in note.lower()
    get_settings.cache_clear()
