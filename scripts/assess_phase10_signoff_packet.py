"""
Assess Phase 10 sign-off packet readiness from latest post-launch artifacts.

Usage:
    python scripts/assess_phase10_signoff_packet.py
    python scripts/assess_phase10_signoff_packet.py --fail-on-no-go
    python scripts/assess_phase10_signoff_packet.py --fail-on-pending-live-data
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ARTIFACT_PATTERNS: dict[str, str] = {
    "phase10_bundle": "phase10_postlaunch_*.json",
    "ops1001_telemetry_trends": "ops1001_telemetry_trends_*.json",
    "ops1001_telemetry_alert_routing": "ops1001_telemetry_alert_routing_*.json",
    "ops1005_incident_drill_assessment": "ops1005_incident_drill_assessment_*.json",
    "ops1003_m5_readiness": "ops1003_m5_readiness_*.json",
}


@dataclass
class SignoffPacketResult:
    report_json_path: Path
    report_md_path: Path
    status: str
    blockers: list[str]
    pending_items: list[str]


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


def _notes_for_status(status: str, *, blockers: list[str], pending_items: list[str]) -> list[str]:
    if status == "no-go":
        return blockers if blockers else ["Blocking sign-off conditions detected."]
    if status == "pending_live_data":
        notes = [
            "Sign-off remains pending until live telemetry calibration and live incident timeline evidence are available."
        ]
        notes.extend(pending_items)
        return notes
    return ["All machine-checkable Phase 10 sign-off criteria are satisfied."]


def _write_markdown(path: Path, payload: dict[str, Any]) -> None:
    recommendation = payload["recommendation"]
    summary = payload["summary"]
    lines = [
        "# Phase 10 Sign-off Packet Readiness",
        "",
        f"- Generated (UTC): `{payload['generated_at_utc']}`",
        f"- Recommendation status: `{recommendation['status']}`",
        "",
        "## Source Artifacts",
        "",
        "| Artifact | File | Present |",
        "|---|---|---|",
    ]

    for artifact_name, artifact_value in payload["source_artifacts"].items():
        present = artifact_value is not None
        lines.append(f"| {artifact_name} | {artifact_value} | {present} |")

    lines.extend(
        [
            "",
            "## Gate Summary",
            "",
            f"- Latest Phase 10 bundle overall status: `{summary['phase10_bundle_overall_status']}`",
            f"- OPS-1001 telemetry trend status: `{summary['ops1001_telemetry_status']}`",
            f"- OPS-1001 telemetry total requests: `{summary['ops1001_total_requests']}`",
            f"- OPS-1001 alert routing requires incident: `{summary['ops1001_requires_incident']}`",
            f"- OPS-1001 alert routing critical count: `{summary['ops1001_critical_count']}`",
            f"- OPS-1005 drill assessment status: `{summary['ops1005_status']}`",
            f"- OPS-1003 M5 readiness status: `{summary['ops1003_m5_status']}`",
            f"- Blocker count: `{summary['blocker_count']}`",
            f"- Pending item count: `{summary['pending_item_count']}`",
            "",
            "## Blockers",
            "",
        ]
    )

    blockers = recommendation["blockers"]
    if blockers:
        for blocker in blockers:
            lines.append(f"- {blocker}")
    else:
        lines.append("- None.")

    lines.extend(["", "## Pending Live-Data Items", ""])
    pending_items = recommendation["pending_items"]
    if pending_items:
        for item in pending_items:
            lines.append(f"- {item}")
    else:
        lines.append("- None.")

    lines.extend(["", "## Notes", ""])
    for note in recommendation["notes"]:
        lines.append(f"- {note}")

    path.write_text("\n".join(lines), encoding="utf-8")


def assess_phase10_signoff_packet(*, reports_dir: Path) -> SignoffPacketResult:
    reports_dir.mkdir(parents=True, exist_ok=True)
    stamp = _timestamp()
    output_json = reports_dir / f"phase10_signoff_packet_{stamp}.json"
    output_md = reports_dir / f"phase10_signoff_packet_{stamp}.md"

    source_artifacts: dict[str, str | None] = {}
    loaded_payloads: dict[str, dict[str, Any]] = {}
    pending_items: list[str] = []
    blockers: list[str] = []

    for artifact_name, pattern in ARTIFACT_PATTERNS.items():
        latest = _latest_report(reports_dir=reports_dir, pattern=pattern)
        source_artifacts[artifact_name] = latest.name if latest else None
        if latest is None:
            pending_items.append(f"Missing required artifact: {artifact_name}.")
            continue
        try:
            loaded_payloads[artifact_name] = _load_json(latest)
        except (OSError, json.JSONDecodeError):
            blockers.append(f"Artifact `{artifact_name}` is unreadable or invalid JSON.")

    phase10_bundle_payload = loaded_payloads.get("phase10_bundle", {})
    phase10_bundle_overall = str(phase10_bundle_payload.get("overall_status", "unknown")).strip().lower()
    if source_artifacts["phase10_bundle"] is not None and phase10_bundle_overall != "pass":
        blockers.append(
            f"Latest Phase 10 bundle status is `{phase10_bundle_overall}` (expected `pass`)."
        )

    telemetry_payload = loaded_payloads.get("ops1001_telemetry_trends", {})
    telemetry_recommendation = telemetry_payload.get("recommendation", {})
    ops1001_telemetry_status = str(telemetry_recommendation.get("status", "missing")).strip().lower()
    ops1001_total_requests = int(telemetry_payload.get("summary", {}).get("total_requests", 0) or 0)
    if source_artifacts["ops1001_telemetry_trends"] is not None:
        if ops1001_telemetry_status in {"insufficient_data", "hold"}:
            pending_items.append(
                "OPS-1001 telemetry calibration is incomplete; ingest live 7-day telemetry export and rerun."
            )
        elif ops1001_telemetry_status == "tune_now":
            blockers.append(
                "OPS-1001 telemetry status is `tune_now`; apply threshold tuning before sign-off."
            )

    routing_payload = loaded_payloads.get("ops1001_telemetry_alert_routing", {})
    routing_summary = routing_payload.get("summary", {})
    ops1001_requires_incident = bool(routing_summary.get("requires_incident", False))
    ops1001_critical_count = int(routing_summary.get("counts_by_severity", {}).get("critical", 0) or 0)
    if source_artifacts["ops1001_telemetry_alert_routing"] is not None:
        if ops1001_requires_incident or ops1001_critical_count > 0:
            blockers.append(
                "OPS-1001 alert routing indicates critical incident requirements; resolve alerts before sign-off."
            )

    drill_payload = loaded_payloads.get("ops1005_incident_drill_assessment", {})
    drill_status = str(drill_payload.get("recommendation", {}).get("status", "missing")).strip().lower()
    if source_artifacts["ops1005_incident_drill_assessment"] is not None:
        if drill_status in {"pending_live_run", "hold"}:
            pending_items.append(
                "OPS-1005 live-data incident timeline evidence is pending; execute one live drill and rerun."
            )
        elif drill_status == "no-go":
            blockers.append("OPS-1005 incident drill assessment is `no-go`.")

    m5_payload = loaded_payloads.get("ops1003_m5_readiness", {})
    ops1003_m5_status = str(m5_payload.get("recommendation", {}).get("status", "missing")).strip().lower()
    if source_artifacts["ops1003_m5_readiness"] is not None and ops1003_m5_status != "go":
        blockers.append(
            f"OPS-1003 M5 readiness is `{ops1003_m5_status}` (expected `go`)."
        )

    if blockers:
        status = "no-go"
    elif pending_items:
        status = "pending_live_data"
    else:
        status = "go"

    payload = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "source_artifacts": source_artifacts,
        "summary": {
            "phase10_bundle_overall_status": phase10_bundle_overall,
            "ops1001_telemetry_status": ops1001_telemetry_status,
            "ops1001_total_requests": ops1001_total_requests,
            "ops1001_requires_incident": ops1001_requires_incident,
            "ops1001_critical_count": ops1001_critical_count,
            "ops1005_status": drill_status,
            "ops1003_m5_status": ops1003_m5_status,
            "blocker_count": len(blockers),
            "pending_item_count": len(pending_items),
        },
        "recommendation": {
            "status": status,
            "blockers": blockers,
            "pending_items": pending_items,
            "notes": _notes_for_status(status, blockers=blockers, pending_items=pending_items),
        },
    }
    output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    _write_markdown(output_md, payload)

    return SignoffPacketResult(
        report_json_path=output_json,
        report_md_path=output_md,
        status=status,
        blockers=blockers,
        pending_items=pending_items,
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Assess machine-checkable Phase 10 sign-off packet readiness.",
    )
    parser.add_argument(
        "--reports-dir",
        type=Path,
        default=_default_reports_dir(),
        help="Directory containing Phase 10 artifacts.",
    )
    parser.add_argument(
        "--fail-on-no-go",
        action="store_true",
        help="Exit non-zero when recommendation status is `no-go`.",
    )
    parser.add_argument(
        "--fail-on-pending-live-data",
        action="store_true",
        help="Exit non-zero when recommendation status is `pending_live_data`.",
    )
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    result = assess_phase10_signoff_packet(
        reports_dir=args.reports_dir.resolve(),
    )
    print(f"[phase10-signoff-packet] status={result.status}")
    print(f"[phase10-signoff-packet] markdown={result.report_md_path.as_posix()}")
    print(f"[phase10-signoff-packet] json={result.report_json_path.as_posix()}")
    if result.blockers:
        print("[phase10-signoff-packet] blockers:")
        for blocker in result.blockers:
            print(f"- {blocker}")
    if result.pending_items:
        print("[phase10-signoff-packet] pending_items:")
        for item in result.pending_items:
            print(f"- {item}")

    if args.fail_on_no_go and result.status == "no-go":
        return 2
    if args.fail_on_pending_live_data and result.status == "pending_live_data":
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
