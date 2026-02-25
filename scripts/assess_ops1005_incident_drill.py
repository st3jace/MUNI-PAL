"""
Assess OPS-1005 incident drill readiness from telemetry routing + drill timeline evidence.

Usage:
    python scripts/assess_ops1005_incident_drill.py
    python scripts/assess_ops1005_incident_drill.py --timeline-path reports/phase10_postlaunch/ops1005_incident_timeline.json
    python scripts/assess_ops1005_incident_drill.py --fail-on-no-go
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ALERT_ROUTING_PATTERN = "ops1001_telemetry_alert_routing_*.json"
DEFAULT_TIMELINE_FILENAME = "ops1005_incident_timeline.json"
LIVE_DATA_MODES = {"live", "live_data", "production", "prod"}


@dataclass
class DrillAssessmentResult:
    report_json_path: Path
    report_md_path: Path
    status: str
    blockers: list[str]
    residual_risks: list[str]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _default_reports_dir() -> Path:
    return _repo_root() / "reports" / "phase10_postlaunch"


def _timestamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%d_%H%M%S")


def _latest_report(*, reports_dir: Path, pattern: str) -> Path | None:
    matches = sorted(reports_dir.glob(pattern))
    if not matches:
        return None
    return matches[-1]


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _coerce_string(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return text


def _parse_timestamp(value: Any) -> datetime | None:
    text = _coerce_string(value)
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _timeline_block(payload: dict[str, Any]) -> dict[str, Any]:
    timeline = payload.get("timeline")
    if isinstance(timeline, dict):
        return timeline
    return payload


def _minutes_between(start: datetime, end: datetime) -> float:
    return round((end - start).total_seconds() / 60.0, 2)


def _notes_for_status(status: str, *, blockers: list[str], residual_risks: list[str]) -> list[str]:
    if status == "no-go":
        return blockers if blockers else ["Blocking conditions detected in incident drill readiness."]
    if status == "pending_live_run":
        return [
            "Live-data OPS-1005 timeline evidence is not captured yet.",
            f"Create `{DEFAULT_TIMELINE_FILENAME}` and re-run this assessor.",
        ]
    if status == "hold":
        notes = ["Incident drill evidence exists but mode is not `live_data`."]
        if residual_risks:
            notes.append(f"Residual risks recorded: {len(residual_risks)}.")
        return notes
    return ["Live-data drill evidence captured and response timing thresholds are satisfied."]


def _write_markdown(path: Path, payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    recommendation = payload["recommendation"]
    lines = [
        "# OPS-1005 Incident Drill Assessment",
        "",
        f"- Generated (UTC): `{payload['generated_at_utc']}`",
        f"- Recommendation status: `{recommendation['status']}`",
        f"- Source alert routing report: `{payload['source_artifacts']['ops1001_telemetry_alert_routing']}`",
        f"- Source drill timeline file: `{payload['source_artifacts']['ops1005_incident_timeline']}`",
        "",
        "## Drill Summary",
        "",
        f"- Drill executed: `{summary['drill_executed']}`",
        f"- Live-data mode: `{summary['live_data_mode']}`",
        f"- Drill ID: `{summary['drill_id']}`",
        f"- Incident owner: `{summary['incident_owner']}`",
        f"- Routing requires incident: `{summary['routing_requires_incident']}`",
        f"- Routing highest severity: `{summary['routing_highest_severity']}`",
        f"- Routing critical count: `{summary['routing_critical_count']}`",
        "",
        "## Timing (Minutes)",
        "",
        "| Metric | Observed | Threshold |",
        "|---|---:|---:|",
        f"| TTD | {summary['ttd_minutes']} | <= {summary['thresholds_minutes']['ttd']} |",
        f"| TTM | {summary['ttm_minutes']} | <= {summary['thresholds_minutes']['ttm']} |",
        f"| TTR | {summary['ttr_minutes']} | <= {summary['thresholds_minutes']['ttr']} |",
        "",
        "## Blockers",
        "",
    ]

    blockers = recommendation["blockers"]
    if blockers:
        for blocker in blockers:
            lines.append(f"- {blocker}")
    else:
        lines.append("- None.")

    lines.extend(["", "## Residual Risks", ""])
    residual_risks = recommendation["residual_risks"]
    if residual_risks:
        for risk in residual_risks:
            lines.append(f"- {risk}")
    else:
        lines.append("- None.")

    lines.extend(["", "## Notes", ""])
    for note in recommendation["notes"]:
        lines.append(f"- {note}")

    path.write_text("\n".join(lines), encoding="utf-8")


def assess_ops1005_incident_drill(
    *,
    reports_dir: Path,
    alert_routing_report: Path | None,
    timeline_path: Path | None,
    incident_owner: str,
    policy_version: str,
    max_ttd_minutes: float,
    max_ttm_minutes: float,
    max_ttr_minutes: float,
) -> DrillAssessmentResult:
    reports_dir.mkdir(parents=True, exist_ok=True)
    stamp = _timestamp()
    output_json = reports_dir / f"ops1005_incident_drill_assessment_{stamp}.json"
    output_md = reports_dir / f"ops1005_incident_drill_assessment_{stamp}.md"

    blockers: list[str] = []
    residual_risks: list[str] = []

    source_alert = (
        alert_routing_report.resolve()
        if alert_routing_report is not None
        else _latest_report(reports_dir=reports_dir, pattern=ALERT_ROUTING_PATTERN)
    )

    routing_requires_incident = False
    routing_highest_severity = "missing"
    routing_critical_count = 0
    if source_alert is None or not source_alert.exists():
        blockers.append("Missing OPS-1001 telemetry alert-routing artifact.")
    else:
        try:
            alert_payload = _load_json(source_alert)
        except (OSError, json.JSONDecodeError):
            blockers.append("OPS-1001 alert-routing artifact is unreadable or invalid JSON.")
        else:
            summary = alert_payload.get("summary", {})
            if isinstance(summary, dict):
                routing_requires_incident = bool(summary.get("requires_incident", False))
                routing_highest_severity = str(summary.get("highest_severity", "unknown")).strip().lower()
                routing_critical_count = int(summary.get("counts_by_severity", {}).get("critical", 0))

    default_timeline = reports_dir / DEFAULT_TIMELINE_FILENAME
    source_timeline = timeline_path.resolve() if timeline_path is not None else default_timeline
    if not source_timeline.exists():
        source_timeline = None

    drill_executed = source_timeline is not None
    drill_id: str | None = None
    live_data_mode = False
    linked_alert_routing_report: str | None = None
    ttd_minutes: float | None = None
    ttm_minutes: float | None = None
    ttr_minutes: float | None = None

    if source_timeline is None:
        if routing_requires_incident:
            blockers.append(
                "Routing artifact requires incident response, but no OPS-1005 timeline file was provided."
            )
        else:
            residual_risks.append("Live-data OPS-1005 timeline evidence is not captured yet.")
    else:
        try:
            timeline_payload = _load_json(source_timeline)
        except (OSError, json.JSONDecodeError):
            blockers.append("OPS-1005 timeline artifact is unreadable or invalid JSON.")
            timeline_payload = {}
        timeline = _timeline_block(timeline_payload)

        drill_id = _coerce_string(timeline_payload.get("drill_id")) or _coerce_string(timeline.get("drill_id"))
        linked_alert_routing_report = _coerce_string(timeline_payload.get("alert_routing_report")) or _coerce_string(
            timeline.get("alert_routing_report")
        )
        mode = (
            _coerce_string(timeline_payload.get("mode"))
            or _coerce_string(timeline.get("mode"))
            or "unknown"
        )
        live_data_mode = mode.lower() in LIVE_DATA_MODES
        if not live_data_mode:
            residual_risks.append(
                f"Drill mode is `{mode}`; execute one `live_data` drill before Phase 10 sign-off."
            )

        trigger_at = _parse_timestamp(timeline.get("trigger_at_utc"))
        detection_at = _parse_timestamp(timeline.get("detection_at_utc"))
        mitigation_at = _parse_timestamp(timeline.get("mitigation_confirmed_at_utc"))
        recovery_at = _parse_timestamp(timeline.get("recovery_confirmed_at_utc"))

        if trigger_at is None:
            blockers.append("Timeline field `trigger_at_utc` is missing or invalid.")
        if detection_at is None:
            blockers.append("Timeline field `detection_at_utc` is missing or invalid.")
        if mitigation_at is None:
            blockers.append("Timeline field `mitigation_confirmed_at_utc` is missing or invalid.")
        if recovery_at is None:
            blockers.append("Timeline field `recovery_confirmed_at_utc` is missing or invalid.")

        if not blockers and trigger_at and detection_at and mitigation_at and recovery_at:
            ttd_minutes = _minutes_between(trigger_at, detection_at)
            ttm_minutes = _minutes_between(detection_at, mitigation_at)
            ttr_minutes = _minutes_between(mitigation_at, recovery_at)
            if ttd_minutes < 0 or ttm_minutes < 0 or ttr_minutes < 0:
                blockers.append("Timeline ordering is invalid (negative duration detected).")
            if ttd_minutes > max_ttd_minutes:
                blockers.append(
                    f"TTD {ttd_minutes}m exceeds threshold {max_ttd_minutes}m."
                )
            if ttm_minutes > max_ttm_minutes:
                blockers.append(
                    f"TTM {ttm_minutes}m exceeds threshold {max_ttm_minutes}m."
                )
            if ttr_minutes > max_ttr_minutes:
                blockers.append(
                    f"TTR {ttr_minutes}m exceeds threshold {max_ttr_minutes}m."
                )

        if source_alert is not None and linked_alert_routing_report:
            if Path(linked_alert_routing_report).name != source_alert.name:
                residual_risks.append(
                    "Timeline references a different alert-routing report than latest artifact."
                )

    if blockers:
        status = "no-go"
    elif not drill_executed:
        status = "pending_live_run"
    elif not live_data_mode:
        status = "hold"
    else:
        status = "go"

    payload = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "policy_version": policy_version,
        "source_artifacts": {
            "ops1001_telemetry_alert_routing": source_alert.name if source_alert else None,
            "ops1005_incident_timeline": source_timeline.name if source_timeline else None,
        },
        "summary": {
            "drill_executed": drill_executed,
            "live_data_mode": live_data_mode,
            "drill_id": drill_id,
            "incident_owner": incident_owner,
            "routing_requires_incident": routing_requires_incident,
            "routing_highest_severity": routing_highest_severity,
            "routing_critical_count": routing_critical_count,
            "linked_alert_routing_report": linked_alert_routing_report,
            "ttd_minutes": ttd_minutes,
            "ttm_minutes": ttm_minutes,
            "ttr_minutes": ttr_minutes,
            "thresholds_minutes": {
                "ttd": max_ttd_minutes,
                "ttm": max_ttm_minutes,
                "ttr": max_ttr_minutes,
            },
            "blocker_count": len(blockers),
            "residual_risk_count": len(residual_risks),
        },
        "recommendation": {
            "status": status,
            "blockers": blockers,
            "residual_risks": residual_risks,
            "notes": _notes_for_status(status, blockers=blockers, residual_risks=residual_risks),
        },
    }

    output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    _write_markdown(output_md, payload)

    return DrillAssessmentResult(
        report_json_path=output_json,
        report_md_path=output_md,
        status=status,
        blockers=blockers,
        residual_risks=residual_risks,
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Assess OPS-1005 incident drill readiness from latest Phase 10 evidence.",
    )
    parser.add_argument(
        "--reports-dir",
        type=Path,
        default=_default_reports_dir(),
        help="Directory containing Phase 10 artifacts.",
    )
    parser.add_argument(
        "--alert-routing-report",
        type=Path,
        default=None,
        help="Optional explicit OPS-1001 alert-routing JSON artifact.",
    )
    parser.add_argument(
        "--timeline-path",
        type=Path,
        default=None,
        help=(
            "Optional incident timeline JSON path. Defaults to "
            "`reports/phase10_postlaunch/ops1005_incident_timeline.json` when omitted."
        ),
    )
    parser.add_argument(
        "--incident-owner",
        default="unassigned",
        help="Incident owner recorded in report metadata.",
    )
    parser.add_argument(
        "--policy-version",
        default="ops1005-incident-drill-v1",
        help="Policy version stamped in generated assessment output.",
    )
    parser.add_argument(
        "--max-ttd-minutes",
        type=float,
        default=5.0,
        help="Maximum acceptable TTD in minutes.",
    )
    parser.add_argument(
        "--max-ttm-minutes",
        type=float,
        default=15.0,
        help="Maximum acceptable TTM in minutes.",
    )
    parser.add_argument(
        "--max-ttr-minutes",
        type=float,
        default=10.0,
        help="Maximum acceptable TTR in minutes.",
    )
    parser.add_argument(
        "--fail-on-no-go",
        action="store_true",
        help="Exit non-zero when recommendation status is `no-go`.",
    )
    parser.add_argument(
        "--fail-on-pending-live-run",
        action="store_true",
        help="Exit non-zero when recommendation status is `pending_live_run` or `hold`.",
    )
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    result = assess_ops1005_incident_drill(
        reports_dir=args.reports_dir.resolve(),
        alert_routing_report=args.alert_routing_report.resolve() if args.alert_routing_report else None,
        timeline_path=args.timeline_path.resolve() if args.timeline_path else None,
        incident_owner=str(args.incident_owner),
        policy_version=str(args.policy_version),
        max_ttd_minutes=max(float(args.max_ttd_minutes), 0.0),
        max_ttm_minutes=max(float(args.max_ttm_minutes), 0.0),
        max_ttr_minutes=max(float(args.max_ttr_minutes), 0.0),
    )
    print(f"[ops1005-incident-drill] status={result.status}")
    print(f"[ops1005-incident-drill] markdown={result.report_md_path.as_posix()}")
    print(f"[ops1005-incident-drill] json={result.report_json_path.as_posix()}")
    if result.blockers:
        print("[ops1005-incident-drill] blockers:")
        for blocker in result.blockers:
            print(f"- {blocker}")
    if result.residual_risks:
        print("[ops1005-incident-drill] residual_risks:")
        for risk in result.residual_risks:
            print(f"- {risk}")

    if args.fail_on_no_go and result.status == "no-go":
        return 2
    if args.fail_on_pending_live_run and result.status in {"pending_live_run", "hold"}:
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
