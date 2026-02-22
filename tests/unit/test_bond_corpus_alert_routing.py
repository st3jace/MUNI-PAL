from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType


def _load_alert_router_module() -> ModuleType:
    script_path = Path(__file__).resolve().parents[2] / "scripts" / "route_bond_corpus_drift_alerts.py"
    spec = importlib.util.spec_from_file_location("route_bond_corpus_drift_alerts", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _base_drift_payload() -> dict[str, object]:
    return {
        "generated_at_utc": "2026-02-21T18:34:50.886964+00:00",
        "drift_status": "stable",
        "baseline_report": "bond_corpus_calibration_prev.json",
        "current_report": "bond_corpus_calibration_curr.json",
        "recommendation_transition": {"previous": "go", "current": "go"},
        "cdr5_metric_coverage": {
            "reliability_band_change": "evaluated via sample-size proxy transitions",
            "overall_posture_score_delta_gt_0_10": "evaluated via posture_score_proxy series",
            "conflict_rate_spike_gt_0_20": "evaluated via conflict_rate_proxy series",
            "evidence_count_drop_gt_30pct": "evaluated",
        },
        "sectors": {
            "waste": {
                "current_present": True,
                "previous_present": True,
                "overall_posture_score_proxy_delta": 0.0,
                "cdr3_deltas": {
                    "all": {"pair_complete_delta": 0, "medium_plus_delta": 0},
                },
                "dimension_drift": {
                    "risk.feedstock": {
                        "pair_complete_transition": "1->1",
                        "sample_reliability_band_previous": "medium",
                        "sample_reliability_band_current": "medium",
                        "exposure_drop_pct": 0.0,
                        "mitigant_drop_pct": 0.0,
                        "distinct_documents_drop_pct": 0.0,
                        "conflict_rate_proxy_delta": 0.0,
                    }
                },
                "unmapped_category_delta": 0,
            }
        },
        "alerts": [],
    }


def test_alert_router_generates_no_events_for_stable_payload(tmp_path: Path):
    router = _load_alert_router_module()
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    drift_path = reports_dir / "bond_corpus_drift_20260221_183450.json"
    drift_path.write_text(json.dumps(_base_drift_payload(), indent=2), encoding="utf-8")

    result = router.route_bond_corpus_drift_alerts(
        reports_dir=reports_dir,
        drift_report=drift_path,
        on_call_owner="ops@example.com",
        policy_version="cdr5-alert-routing-v1",
    )

    routed_payload = json.loads(result.report_json_path.read_text(encoding="utf-8"))
    assert routed_payload["summary"]["alert_count"] == 0
    assert routed_payload["summary"]["highest_severity"] == "none"
    assert routed_payload["summary"]["requires_incident"] is False
    assert result.critical_count == 0
    assert result.requires_incident is False


def test_alert_router_flags_critical_regression(tmp_path: Path):
    router = _load_alert_router_module()
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    payload = _base_drift_payload()
    payload["recommendation_transition"] = {"previous": "go", "current": "no-go"}
    payload["sectors"]["waste"]["dimension_drift"]["risk.feedstock"]["pair_complete_transition"] = "1->0"
    payload["sectors"]["waste"]["dimension_drift"]["risk.feedstock"]["exposure_drop_pct"] = 41.0
    drift_path = reports_dir / "bond_corpus_drift_20260221_183500.json"
    drift_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    result = router.route_bond_corpus_drift_alerts(
        reports_dir=reports_dir,
        drift_report=drift_path,
        on_call_owner="ops@example.com",
        policy_version="cdr5-alert-routing-v1",
    )

    routed_payload = json.loads(result.report_json_path.read_text(encoding="utf-8"))
    assert routed_payload["summary"]["requires_incident"] is True
    assert routed_payload["summary"]["hold_advisory_generation"] is True
    assert routed_payload["summary"]["counts_by_severity"]["critical"] >= 2
    assert result.critical_count >= 2
    assert result.requires_incident is True


def test_alert_router_flags_posture_and_conflict_thresholds(tmp_path: Path):
    router = _load_alert_router_module()
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    payload = _base_drift_payload()
    payload["sectors"]["waste"]["overall_posture_score_proxy_delta"] = -0.12
    payload["sectors"]["waste"]["dimension_drift"]["risk.feedstock"]["conflict_rate_proxy_delta"] = 0.26
    drift_path = reports_dir / "bond_corpus_drift_20260221_183600.json"
    drift_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    result = router.route_bond_corpus_drift_alerts(
        reports_dir=reports_dir,
        drift_report=drift_path,
        on_call_owner="ops@example.com",
        policy_version="cdr5-alert-routing-v1",
    )

    routed_payload = json.loads(result.report_json_path.read_text(encoding="utf-8"))
    by_rule = {event["rule"]: event for event in routed_payload["events"]}
    assert "cdr5_overall_posture_proxy_delta" in by_rule
    assert "cdr5_conflict_rate_proxy_spike" in by_rule
    assert by_rule["cdr5_overall_posture_proxy_delta"]["severity"] == "warning"
    assert by_rule["cdr5_conflict_rate_proxy_spike"]["severity"] == "critical"
    assert routed_payload["summary"]["requires_incident"] is True
    assert result.critical_count >= 1
