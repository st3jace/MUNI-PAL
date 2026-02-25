"""
Route OPS-1001 telemetry trend findings into an incident/escalation artifact.

Usage:
    python scripts/route_ops1001_telemetry_alerts.py
    python scripts/route_ops1001_telemetry_alerts.py --fail-on-critical
    python scripts/route_ops1001_telemetry_alerts.py --telemetry-report reports/phase10_postlaunch/ops1001_telemetry_trends_*.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

SEVERITY_RANK = {"info": 0, "warning": 1, "critical": 2}


@dataclass
class AlertRoutingResult:
    report_json_path: Path
    report_md_path: Path
    highest_severity: str
    critical_count: int
    requires_incident: bool


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _default_reports_dir() -> Path:
    return _repo_root() / "reports" / "phase10_postlaunch"


def _timestamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%d_%H%M%S")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _latest_telemetry_report(reports_dir: Path) -> Path | None:
    reports = sorted(reports_dir.glob("ops1001_telemetry_trends_*.json"))
    if not reports:
        return None
    return reports[-1]


def _event(
    *,
    rule: str,
    severity: str,
    message: str,
    metric: str | None = None,
    observed: Any = None,
    threshold: str | None = None,
) -> dict[str, Any]:
    digest = hashlib.sha1(f"{rule}|{metric}|{message}".encode()).hexdigest()[:10]
    payload: dict[str, Any] = {
        "id": f"{rule}-{digest}",
        "rule": rule,
        "severity": severity,
        "message": message,
    }
    if metric:
        payload["metric"] = metric
    if observed is not None:
        payload["observed"] = observed
    if threshold:
        payload["threshold"] = threshold
    return payload


def _highest_severity(events: list[dict[str, Any]]) -> str:
    if not events:
        return "none"
    return max(events, key=lambda event: SEVERITY_RANK.get(str(event.get("severity")), -1)).get(
        "severity", "none"
    )


def _summary(events: list[dict[str, Any]]) -> dict[str, Any]:
    counts = {"info": 0, "warning": 0, "critical": 0}
    for event in events:
        severity = str(event.get("severity", "info"))
        if severity in counts:
            counts[severity] += 1
    highest = _highest_severity(events)
    critical_count = counts["critical"]
    requires_incident = critical_count > 0
    return {
        "counts_by_severity": counts,
        "highest_severity": highest,
        "requires_incident": requires_incident,
        "hold_feature_rollout": requires_incident,
        "alert_count": len(events),
    }


def _next_actions(*, summary: dict[str, Any], on_call_owner: str) -> list[str]:
    if summary["requires_incident"]:
        return [
            f"Open incident immediately and assign owner `{on_call_owner}`.",
            "Escalate to security/operations response channel and capture timeline.",
            "Investigate rate spikes and validate tenant/isolation controls on affected paths.",
            "Re-run Phase 10 bundle after mitigation and document residual risk.",
        ]
    if summary["counts_by_severity"]["warning"] > 0:
        return [
            f"Create follow-up task for owner `{on_call_owner}` within 24h.",
            "Review warning-level OPS-1001 telemetry events and tune thresholds or controls as needed.",
            "Track next run for recurrence or escalation to incident.",
        ]
    return [
        "No incident action required; continue weekly monitoring cadence.",
        "Archive OPS-1001 telemetry routing artifact in weekly evidence packet.",
    ]


def _rate_and_threshold(metric_payload: dict[str, Any]) -> tuple[float, float, int]:
    rate_per_1k = float(metric_payload.get("rate_per_1k", 0.0) or 0.0)
    threshold_per_1k = float(metric_payload.get("threshold_per_1k", 0.0) or 0.0)
    breach_count = int(metric_payload.get("breach_count", 0) or 0)
    return rate_per_1k, threshold_per_1k, breach_count


def _severity_for_metric_breach(
    *,
    metric_name: str,
    rate_per_1k: float,
    threshold_per_1k: float,
) -> str:
    if threshold_per_1k <= 0:
        return "warning"
    ratio = rate_per_1k / threshold_per_1k
    if metric_name == "cross_tenant_denied" and ratio >= 1.0:
        return "critical"
    if ratio >= 2.0:
        return "critical"
    return "warning"


def _build_events(telemetry_payload: dict[str, Any]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    recommendation = telemetry_payload.get("recommendation", {})
    status = str(recommendation.get("status", "unknown")).strip().lower()
    reasons = recommendation.get("reasons", [])
    first_reason = str(reasons[0]).strip() if isinstance(reasons, list) and reasons else ""

    if status == "insufficient_data":
        events.append(
            _event(
                rule="ops1001_insufficient_data",
                severity="warning",
                message=first_reason or "OPS-1001 telemetry assessment reported insufficient data.",
                metric="ops1001.telemetry_input",
            )
        )
    elif status == "hold":
        events.append(
            _event(
                rule="ops1001_low_volume_hold",
                severity="warning",
                message=first_reason or "OPS-1001 telemetry assessment is on hold pending sample floor.",
                metric="ops1001.request_volume",
            )
        )

    metrics = telemetry_payload.get("metrics", {})
    for metric_name in ("unauthorized_401", "forbidden_403", "cross_tenant_denied"):
        metric_payload = metrics.get(metric_name, {})
        if not isinstance(metric_payload, dict):
            continue
        rate_per_1k, threshold_per_1k, breach_count = _rate_and_threshold(metric_payload)
        if rate_per_1k > threshold_per_1k:
            severity = _severity_for_metric_breach(
                metric_name=metric_name,
                rate_per_1k=rate_per_1k,
                threshold_per_1k=threshold_per_1k,
            )
            events.append(
                _event(
                    rule="ops1001_metric_rate_threshold_breach",
                    severity=severity,
                    metric=metric_name,
                    message=(
                        f"{metric_name} rate {rate_per_1k}/1k exceeds threshold "
                        f"{threshold_per_1k}/1k."
                    ),
                    observed=rate_per_1k,
                    threshold=f"> {threshold_per_1k}/1k",
                )
            )
        elif breach_count > 0:
            events.append(
                _event(
                    rule="ops1001_metric_daily_breach_days",
                    severity="warning",
                    metric=metric_name,
                    message=f"{metric_name} exceeded threshold on {breach_count} day(s) in window.",
                    observed=breach_count,
                    threshold="0 breach days",
                )
            )

    threshold_updates = recommendation.get("threshold_updates", [])
    if isinstance(threshold_updates, list):
        for update in threshold_updates:
            if not isinstance(update, dict):
                continue
            metric = str(update.get("metric", "")).strip()
            current = update.get("current_threshold_per_1k")
            suggested = update.get("suggested_threshold_per_1k")
            if not metric:
                continue
            events.append(
                _event(
                    rule="ops1001_threshold_update_suggested",
                    severity="warning",
                    metric=metric,
                    message=f"Threshold update suggested for {metric}: {current} -> {suggested}.",
                    observed=suggested,
                    threshold=str(current),
                )
            )

    if status == "tune_now" and not any(
        event.get("rule") in {"ops1001_metric_rate_threshold_breach", "ops1001_metric_daily_breach_days"}
        for event in events
    ):
        events.append(
            _event(
                rule="ops1001_manual_tuning_required",
                severity="warning",
                metric="ops1001.thresholds",
                message="Telemetry assessor requested tuning without explicit metric breach details.",
            )
        )

    return events


def _write_markdown(path: Path, payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# OPS-1001 Telemetry Alert Routing",
        "",
        f"- Generated (UTC): `{payload['generated_at_utc']}`",
        f"- Source telemetry report: `{payload['source_telemetry_report']}`",
        f"- Recommendation status: `{payload['telemetry_recommendation_status']}`",
        f"- Highest severity: `{summary['highest_severity']}`",
        f"- Requires incident: `{summary['requires_incident']}`",
        "",
        "## Alert Summary",
        "",
        f"- Info: `{summary['counts_by_severity']['info']}`",
        f"- Warning: `{summary['counts_by_severity']['warning']}`",
        f"- Critical: `{summary['counts_by_severity']['critical']}`",
        "",
        "## Threshold Profile (/1k)",
        "",
    ]
    for key, value in payload.get("threshold_profile_per_1k", {}).items():
        lines.append(f"- `{key}`: `{value}`")

    lines.extend(["", "## Routed Events", ""])
    lines.extend(["| Severity | Rule | Metric | Message |", "|---|---|---|---|"])

    events = payload.get("events", [])
    if events:
        for event in events:
            lines.append(
                f"| {event.get('severity', '')} | {event.get('rule', '')} | "
                f"{event.get('metric', '-')} | {str(event.get('message', '')).replace('|', '/')} |"
            )
    else:
        lines.append("| none | - | - | No routed alert events. |")

    lines.extend(["", "## Escalation Actions", ""])
    for action in payload.get("next_actions", []):
        lines.append(f"- {action}")

    path.write_text("\n".join(lines), encoding="utf-8")


def route_ops1001_telemetry_alerts(
    *,
    reports_dir: Path,
    telemetry_report: Path | None,
    on_call_owner: str,
    policy_version: str,
) -> AlertRoutingResult:
    reports_dir.mkdir(parents=True, exist_ok=True)
    stamp = _timestamp()
    output_json = reports_dir / f"ops1001_telemetry_alert_routing_{stamp}.json"
    output_md = reports_dir / f"ops1001_telemetry_alert_routing_{stamp}.md"

    source_report = telemetry_report.resolve() if telemetry_report else _latest_telemetry_report(reports_dir)
    if source_report is None or not source_report.exists():
        payload = {
            "generated_at_utc": datetime.now(UTC).isoformat(),
            "source_telemetry_report": None,
            "telemetry_recommendation_status": "missing",
            "policy_version": policy_version,
            "on_call_owner": on_call_owner,
            "threshold_profile_per_1k": {},
            "events": [
                _event(
                    rule="ops1001_missing_telemetry_report",
                    severity="warning",
                    message="No OPS-1001 telemetry trend report was found to route.",
                )
            ],
        }
        payload["summary"] = _summary(payload["events"])
        payload["next_actions"] = _next_actions(summary=payload["summary"], on_call_owner=on_call_owner)
        output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        _write_markdown(output_md, payload)
        return AlertRoutingResult(
            report_json_path=output_json,
            report_md_path=output_md,
            highest_severity=payload["summary"]["highest_severity"],
            critical_count=int(payload["summary"]["counts_by_severity"]["critical"]),
            requires_incident=bool(payload["summary"]["requires_incident"]),
        )

    telemetry_payload = _load_json(source_report)
    recommendation = telemetry_payload.get("recommendation", {})
    telemetry_status = str(recommendation.get("status", "unknown")).strip().lower()
    events = _build_events(telemetry_payload)
    summary = _summary(events)

    payload = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "source_telemetry_report": source_report.name,
        "telemetry_recommendation_status": telemetry_status,
        "policy_version": policy_version,
        "on_call_owner": on_call_owner,
        "threshold_profile_per_1k": telemetry_payload.get("threshold_config", {}),
        "events": events,
        "summary": summary,
        "next_actions": _next_actions(summary=summary, on_call_owner=on_call_owner),
    }
    output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    _write_markdown(output_md, payload)
    return AlertRoutingResult(
        report_json_path=output_json,
        report_md_path=output_md,
        highest_severity=summary["highest_severity"],
        critical_count=int(summary["counts_by_severity"]["critical"]),
        requires_incident=bool(summary["requires_incident"]),
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Route OPS-1001 telemetry findings into escalation artifacts.")
    parser.add_argument(
        "--reports-dir",
        type=Path,
        default=_default_reports_dir(),
        help="Directory containing ops1001_telemetry_trends_<timestamp>.json reports.",
    )
    parser.add_argument(
        "--telemetry-report",
        type=Path,
        default=None,
        help="Optional explicit telemetry trend report JSON path. If omitted, latest report is used.",
    )
    parser.add_argument(
        "--on-call-owner",
        default="unassigned",
        help="Owner to stamp into escalation actions.",
    )
    parser.add_argument(
        "--policy-version",
        default="ops1001-alert-routing-v1",
        help="Policy version recorded in routing artifacts.",
    )
    parser.add_argument(
        "--fail-on-critical",
        action="store_true",
        help="Exit non-zero when critical routed alerts are present.",
    )
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    result = route_ops1001_telemetry_alerts(
        reports_dir=args.reports_dir.resolve(),
        telemetry_report=args.telemetry_report.resolve() if args.telemetry_report else None,
        on_call_owner=str(args.on_call_owner),
        policy_version=str(args.policy_version),
    )
    print(f"[ops1001-alert-routing] highest_severity={result.highest_severity}")
    print(f"[ops1001-alert-routing] requires_incident={result.requires_incident}")
    print(f"[ops1001-alert-routing] critical_count={result.critical_count}")
    print(f"[ops1001-alert-routing] markdown={result.report_md_path.as_posix()}")
    print(f"[ops1001-alert-routing] json={result.report_json_path.as_posix()}")
    if args.fail_on_critical and result.critical_count > 0:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
