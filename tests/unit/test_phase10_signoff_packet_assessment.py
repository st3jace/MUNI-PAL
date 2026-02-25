import json
from pathlib import Path

from scripts.assess_phase10_signoff_packet import assess_phase10_signoff_packet


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_signoff_packet_pending_when_live_data_artifacts_are_not_ready(tmp_path: Path) -> None:
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    _write_json(
        reports_dir / "phase10_postlaunch_20260225_200000.json",
        {"overall_status": "pass"},
    )
    _write_json(
        reports_dir / "ops1001_telemetry_trends_20260225_200000.json",
        {
            "summary": {"total_requests": 0},
            "recommendation": {"status": "insufficient_data"},
        },
    )
    _write_json(
        reports_dir / "ops1001_telemetry_alert_routing_20260225_200000.json",
        {
            "summary": {
                "requires_incident": False,
                "counts_by_severity": {"critical": 0},
            }
        },
    )
    _write_json(
        reports_dir / "ops1005_incident_drill_assessment_20260225_200000.json",
        {"recommendation": {"status": "pending_live_run"}},
    )
    _write_json(
        reports_dir / "ops1003_m5_readiness_20260225_200000.json",
        {"recommendation": {"status": "go"}},
    )

    result = assess_phase10_signoff_packet(reports_dir=reports_dir)
    payload = json.loads(result.report_json_path.read_text(encoding="utf-8"))
    assert result.status == "pending_live_data"
    assert payload["recommendation"]["blockers"] == []
    assert any("OPS-1001 telemetry calibration is incomplete" in item for item in result.pending_items)
    assert any("OPS-1005 live-data incident timeline evidence is pending" in item for item in result.pending_items)


def test_signoff_packet_no_go_when_alerts_or_tuning_blockers_present(tmp_path: Path) -> None:
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    _write_json(
        reports_dir / "phase10_postlaunch_20260225_200100.json",
        {"overall_status": "pass"},
    )
    _write_json(
        reports_dir / "ops1001_telemetry_trends_20260225_200100.json",
        {
            "summary": {"total_requests": 500},
            "recommendation": {"status": "tune_now"},
        },
    )
    _write_json(
        reports_dir / "ops1001_telemetry_alert_routing_20260225_200100.json",
        {
            "summary": {
                "requires_incident": True,
                "counts_by_severity": {"critical": 1},
            }
        },
    )
    _write_json(
        reports_dir / "ops1005_incident_drill_assessment_20260225_200100.json",
        {"recommendation": {"status": "go"}},
    )
    _write_json(
        reports_dir / "ops1003_m5_readiness_20260225_200100.json",
        {"recommendation": {"status": "go"}},
    )

    result = assess_phase10_signoff_packet(reports_dir=reports_dir)
    assert result.status == "no-go"
    assert any("tune_now" in blocker for blocker in result.blockers)
    assert any("critical incident requirements" in blocker for blocker in result.blockers)


def test_signoff_packet_go_when_all_gates_are_green(tmp_path: Path) -> None:
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    _write_json(
        reports_dir / "phase10_postlaunch_20260225_200200.json",
        {"overall_status": "pass"},
    )
    _write_json(
        reports_dir / "ops1001_telemetry_trends_20260225_200200.json",
        {
            "summary": {"total_requests": 800},
            "recommendation": {"status": "stable"},
        },
    )
    _write_json(
        reports_dir / "ops1001_telemetry_alert_routing_20260225_200200.json",
        {
            "summary": {
                "requires_incident": False,
                "counts_by_severity": {"critical": 0},
            }
        },
    )
    _write_json(
        reports_dir / "ops1005_incident_drill_assessment_20260225_200200.json",
        {"recommendation": {"status": "go"}},
    )
    _write_json(
        reports_dir / "ops1003_m5_readiness_20260225_200200.json",
        {"recommendation": {"status": "go"}},
    )

    result = assess_phase10_signoff_packet(reports_dir=reports_dir)
    payload = json.loads(result.report_json_path.read_text(encoding="utf-8"))
    assert result.status == "go"
    assert payload["recommendation"]["blockers"] == []
    assert payload["recommendation"]["pending_items"] == []
