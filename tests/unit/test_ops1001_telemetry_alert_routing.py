from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType


def _load_alert_router_module() -> ModuleType:
    script_path = Path(__file__).resolve().parents[2] / "scripts" / "route_ops1001_telemetry_alerts.py"
    spec = importlib.util.spec_from_file_location("route_ops1001_telemetry_alerts", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _stable_telemetry_payload() -> dict[str, object]:
    return {
        "generated_at_utc": "2026-02-25T14:20:50.780543+00:00",
        "source_events_file": "reports/phase10_postlaunch/ops1001_telemetry_events.jsonl",
        "summary": {
            "window_start_utc": "2026-02-18T14:20:50.780543+00:00",
            "window_end_utc": "2026-02-25T14:20:50.780543+00:00",
            "window_days": 7,
            "events_in_window": 200,
            "total_requests": 200,
            "days_observed": 7,
            "min_total_requests_for_calibration": 100,
        },
        "threshold_config": {
            "unauthorized_401_per_1k": 40.0,
            "forbidden_403_per_1k": 20.0,
            "cross_tenant_denied_per_1k": 10.0,
        },
        "metrics": {
            "unauthorized_401": {
                "name": "unauthorized_401",
                "count": 3,
                "rate_per_1k": 15.0,
                "threshold_per_1k": 40.0,
                "max_daily_count": 1,
                "max_daily_rate_per_1k": 20.0,
                "breach_days": [],
                "breach_count": 0,
                "suggested_threshold_per_1k": 40.0,
                "window_days": 7,
            },
            "forbidden_403": {
                "name": "forbidden_403",
                "count": 2,
                "rate_per_1k": 10.0,
                "threshold_per_1k": 20.0,
                "max_daily_count": 1,
                "max_daily_rate_per_1k": 15.0,
                "breach_days": [],
                "breach_count": 0,
                "suggested_threshold_per_1k": 20.0,
                "window_days": 7,
            },
            "cross_tenant_denied": {
                "name": "cross_tenant_denied",
                "count": 1,
                "rate_per_1k": 5.0,
                "threshold_per_1k": 10.0,
                "max_daily_count": 1,
                "max_daily_rate_per_1k": 8.0,
                "breach_days": [],
                "breach_count": 0,
                "suggested_threshold_per_1k": 10.0,
                "window_days": 7,
            },
        },
        "daily_counts": {},
        "recommendation": {
            "status": "stable",
            "reasons": ["All monitored OPS-1001 rates are within configured thresholds."],
            "threshold_updates": [],
        },
    }


def test_alert_router_handles_missing_telemetry_report(tmp_path: Path):
    router = _load_alert_router_module()
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    result = router.route_ops1001_telemetry_alerts(
        reports_dir=reports_dir,
        telemetry_report=None,
        on_call_owner="ops@example.com",
        policy_version="ops1001-alert-routing-v1",
    )

    payload = json.loads(result.report_json_path.read_text(encoding="utf-8"))
    assert payload["summary"]["highest_severity"] == "warning"
    assert payload["summary"]["requires_incident"] is False
    assert payload["events"][0]["rule"] == "ops1001_missing_telemetry_report"
    assert result.critical_count == 0


def test_alert_router_generates_no_events_for_stable_telemetry_payload(tmp_path: Path):
    router = _load_alert_router_module()
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    telemetry_path = reports_dir / "ops1001_telemetry_trends_20260225_150000.json"
    telemetry_path.write_text(json.dumps(_stable_telemetry_payload(), indent=2), encoding="utf-8")

    result = router.route_ops1001_telemetry_alerts(
        reports_dir=reports_dir,
        telemetry_report=telemetry_path,
        on_call_owner="ops@example.com",
        policy_version="ops1001-alert-routing-v1",
    )

    payload = json.loads(result.report_json_path.read_text(encoding="utf-8"))
    assert payload["summary"]["alert_count"] == 0
    assert payload["summary"]["highest_severity"] == "none"
    assert payload["summary"]["requires_incident"] is False
    assert result.critical_count == 0


def test_alert_router_flags_critical_cross_tenant_breach(tmp_path: Path):
    router = _load_alert_router_module()
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    payload = _stable_telemetry_payload()
    payload["recommendation"] = {
        "status": "tune_now",
        "reasons": ["Threshold breach detected for: cross_tenant_denied."],
        "threshold_updates": [
            {
                "metric": "cross_tenant_denied",
                "current_threshold_per_1k": 10.0,
                "suggested_threshold_per_1k": 12.0,
                "reason": "Observed rates exceed current threshold envelope.",
            }
        ],
    }
    payload["metrics"]["cross_tenant_denied"]["rate_per_1k"] = 15.0
    payload["metrics"]["cross_tenant_denied"]["breach_count"] = 3
    telemetry_path = reports_dir / "ops1001_telemetry_trends_20260225_150100.json"
    telemetry_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    result = router.route_ops1001_telemetry_alerts(
        reports_dir=reports_dir,
        telemetry_report=telemetry_path,
        on_call_owner="ops@example.com",
        policy_version="ops1001-alert-routing-v1",
    )

    routed_payload = json.loads(result.report_json_path.read_text(encoding="utf-8"))
    by_rule = {event["rule"]: event for event in routed_payload["events"]}
    assert "ops1001_metric_rate_threshold_breach" in by_rule
    assert by_rule["ops1001_metric_rate_threshold_breach"]["severity"] == "critical"
    assert routed_payload["summary"]["requires_incident"] is True
    assert result.critical_count >= 1
