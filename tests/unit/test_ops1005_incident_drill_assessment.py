import json
from pathlib import Path

from scripts.assess_ops1005_incident_drill import assess_ops1005_incident_drill


def _write_alert_routing_report(
    reports_dir: Path,
    *,
    requires_incident: bool,
    highest_severity: str,
    critical_count: int,
) -> Path:
    payload = {
        "summary": {
            "requires_incident": requires_incident,
            "highest_severity": highest_severity,
            "counts_by_severity": {
                "info": 0,
                "warning": 0,
                "critical": critical_count,
            },
        }
    }
    path = reports_dir / "ops1001_telemetry_alert_routing_20260225_170000.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def _write_timeline_report(
    reports_dir: Path,
    *,
    mode: str,
    trigger_at_utc: str,
    detection_at_utc: str,
    mitigation_confirmed_at_utc: str,
    recovery_confirmed_at_utc: str,
    alert_routing_report: str,
) -> Path:
    payload = {
        "drill_id": "OPS-1005-20260225-02",
        "mode": mode,
        "timeline": {
            "trigger_at_utc": trigger_at_utc,
            "detection_at_utc": detection_at_utc,
            "mitigation_confirmed_at_utc": mitigation_confirmed_at_utc,
            "recovery_confirmed_at_utc": recovery_confirmed_at_utc,
            "alert_routing_report": alert_routing_report,
        },
    }
    path = reports_dir / "ops1005_incident_timeline.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def test_assessor_returns_pending_live_run_when_timeline_is_missing(tmp_path: Path) -> None:
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    _write_alert_routing_report(
        reports_dir,
        requires_incident=False,
        highest_severity="warning",
        critical_count=0,
    )

    result = assess_ops1005_incident_drill(
        reports_dir=reports_dir,
        alert_routing_report=None,
        timeline_path=None,
        incident_owner="ops@example.com",
        policy_version="ops1005-incident-drill-v1",
        max_ttd_minutes=5.0,
        max_ttm_minutes=15.0,
        max_ttr_minutes=10.0,
    )

    payload = json.loads(result.report_json_path.read_text(encoding="utf-8"))
    assert result.status == "pending_live_run"
    assert payload["summary"]["drill_executed"] is False
    assert payload["recommendation"]["blockers"] == []
    assert payload["recommendation"]["residual_risks"] == [
        "Live-data OPS-1005 timeline evidence is not captured yet."
    ]


def test_assessor_flags_no_go_when_incident_required_but_timeline_missing(tmp_path: Path) -> None:
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    _write_alert_routing_report(
        reports_dir,
        requires_incident=True,
        highest_severity="critical",
        critical_count=1,
    )

    result = assess_ops1005_incident_drill(
        reports_dir=reports_dir,
        alert_routing_report=None,
        timeline_path=None,
        incident_owner="ops@example.com",
        policy_version="ops1005-incident-drill-v1",
        max_ttd_minutes=5.0,
        max_ttm_minutes=15.0,
        max_ttr_minutes=10.0,
    )

    assert result.status == "no-go"
    assert any("requires incident response" in blocker for blocker in result.blockers)


def test_assessor_returns_go_for_live_timeline_within_thresholds(tmp_path: Path) -> None:
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    alert_path = _write_alert_routing_report(
        reports_dir,
        requires_incident=True,
        highest_severity="critical",
        critical_count=1,
    )
    timeline_path = _write_timeline_report(
        reports_dir,
        mode="live_data",
        trigger_at_utc="2026-02-25T10:00:00+00:00",
        detection_at_utc="2026-02-25T10:01:00+00:00",
        mitigation_confirmed_at_utc="2026-02-25T10:05:00+00:00",
        recovery_confirmed_at_utc="2026-02-25T10:07:00+00:00",
        alert_routing_report=alert_path.name,
    )

    result = assess_ops1005_incident_drill(
        reports_dir=reports_dir,
        alert_routing_report=None,
        timeline_path=timeline_path,
        incident_owner="ops@example.com",
        policy_version="ops1005-incident-drill-v1",
        max_ttd_minutes=5.0,
        max_ttm_minutes=15.0,
        max_ttr_minutes=10.0,
    )

    payload = json.loads(result.report_json_path.read_text(encoding="utf-8"))
    assert result.status == "go"
    assert result.blockers == []
    assert payload["summary"]["live_data_mode"] is True
    assert payload["summary"]["ttd_minutes"] == 1.0
    assert payload["summary"]["ttm_minutes"] == 4.0
    assert payload["summary"]["ttr_minutes"] == 2.0


def test_assessor_returns_no_go_when_timing_thresholds_are_breached(tmp_path: Path) -> None:
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    alert_path = _write_alert_routing_report(
        reports_dir,
        requires_incident=True,
        highest_severity="critical",
        critical_count=1,
    )
    timeline_path = _write_timeline_report(
        reports_dir,
        mode="live_data",
        trigger_at_utc="2026-02-25T10:00:00+00:00",
        detection_at_utc="2026-02-25T10:12:00+00:00",
        mitigation_confirmed_at_utc="2026-02-25T10:40:00+00:00",
        recovery_confirmed_at_utc="2026-02-25T11:15:00+00:00",
        alert_routing_report=alert_path.name,
    )

    result = assess_ops1005_incident_drill(
        reports_dir=reports_dir,
        alert_routing_report=None,
        timeline_path=timeline_path,
        incident_owner="ops@example.com",
        policy_version="ops1005-incident-drill-v1",
        max_ttd_minutes=5.0,
        max_ttm_minutes=15.0,
        max_ttr_minutes=10.0,
    )

    assert result.status == "no-go"
    assert any("TTD" in blocker for blocker in result.blockers)
    assert any("TTM" in blocker for blocker in result.blockers)
    assert any("TTR" in blocker for blocker in result.blockers)
