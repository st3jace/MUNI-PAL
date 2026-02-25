from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from scripts.assess_ops1001_telemetry_trends import assess_ops1001_telemetry_trends


def _write_events(path: Path, events: list[dict[str, object]]) -> None:
    lines = [json.dumps(event, separators=(",", ":")) for event in events]
    path.write_text("\n".join(lines), encoding="utf-8")


def test_ops1001_assessment_handles_missing_events_file(tmp_path: Path) -> None:
    output_dir = tmp_path / "reports"
    missing_events = tmp_path / "missing.jsonl"

    result = assess_ops1001_telemetry_trends(
        events_path=missing_events,
        output_dir=output_dir,
        window_days=7,
        min_total_requests=100,
        threshold_401_per_1k=40.0,
        threshold_403_per_1k=20.0,
        threshold_cross_tenant_per_1k=10.0,
    )

    payload = json.loads(result.report_json_path.read_text(encoding="utf-8"))
    assert result.status == "insufficient_data"
    assert payload["recommendation"]["status"] == "insufficient_data"
    assert any(
        "No telemetry events file found" in reason
        for reason in payload["recommendation"]["reasons"]
    )


def test_ops1001_assessment_reports_stable_when_rates_within_thresholds(tmp_path: Path) -> None:
    output_dir = tmp_path / "reports"
    events_path = tmp_path / "events.jsonl"
    now = datetime.now(UTC)
    events: list[dict[str, object]] = []

    for index in range(500):
        status_code = 200
        if index < 5:
            status_code = 401
        elif index < 8:
            status_code = 403

        event: dict[str, object] = {
            "timestamp": (now - timedelta(hours=1)).isoformat(),
            "status_code": status_code,
            "message": "request completed",
        }
        if index == 7:
            event["detail"] = "Forbidden: cross-tenant access denied"
        events.append(event)

    _write_events(events_path, events)

    result = assess_ops1001_telemetry_trends(
        events_path=events_path,
        output_dir=output_dir,
        window_days=7,
        min_total_requests=100,
        threshold_401_per_1k=40.0,
        threshold_403_per_1k=20.0,
        threshold_cross_tenant_per_1k=10.0,
    )

    payload = json.loads(result.report_json_path.read_text(encoding="utf-8"))
    assert result.status == "stable"
    assert payload["recommendation"]["status"] == "stable"
    assert payload["metrics"]["unauthorized_401"]["rate_per_1k"] == 10.0
    assert payload["metrics"]["forbidden_403"]["rate_per_1k"] == 6.0
    assert payload["metrics"]["cross_tenant_denied"]["rate_per_1k"] == 2.0
    assert payload["recommendation"]["threshold_updates"] == []


def test_ops1001_assessment_flags_tuning_when_thresholds_are_breached(tmp_path: Path) -> None:
    output_dir = tmp_path / "reports"
    events_path = tmp_path / "events.jsonl"
    now = datetime.now(UTC)
    events: list[dict[str, object]] = []

    for index in range(200):
        status_code = 200
        if index < 20:
            status_code = 401
        elif index < 35:
            status_code = 403

        event: dict[str, object] = {
            "timestamp": (now - timedelta(hours=index % 24)).isoformat(),
            "status_code": status_code,
        }
        if index < 12:
            event["detail"] = "Forbidden: cross-tenant access denied"
        events.append(event)

    _write_events(events_path, events)

    result = assess_ops1001_telemetry_trends(
        events_path=events_path,
        output_dir=output_dir,
        window_days=7,
        min_total_requests=100,
        threshold_401_per_1k=40.0,
        threshold_403_per_1k=20.0,
        threshold_cross_tenant_per_1k=10.0,
    )

    payload = json.loads(result.report_json_path.read_text(encoding="utf-8"))
    assert result.status == "tune_now"
    assert payload["recommendation"]["status"] == "tune_now"
    updates = payload["recommendation"]["threshold_updates"]
    updated_metrics = {entry["metric"] for entry in updates}
    assert "unauthorized_401" in updated_metrics
    assert "forbidden_403" in updated_metrics
    assert "cross_tenant_denied" in updated_metrics
