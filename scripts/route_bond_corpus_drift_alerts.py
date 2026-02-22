"""
Route bond corpus drift alerts into an operational escalation artifact.

Usage:
    python scripts/route_bond_corpus_drift_alerts.py
    python scripts/route_bond_corpus_drift_alerts.py --fail-on-critical
    python scripts/route_bond_corpus_drift_alerts.py --drift-report reports/phase10_postlaunch/bond_corpus_drift_*.json
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


def _latest_drift_report(reports_dir: Path) -> Path | None:
    reports = sorted(reports_dir.glob("bond_corpus_drift_*.json"))
    if not reports:
        return None
    return reports[-1]


def _band_rank(value: str) -> int:
    return {"low": 0, "medium": 1, "high": 2}.get(str(value).strip().lower(), -1)


def _event(
    *,
    rule: str,
    severity: str,
    message: str,
    sector: str | None = None,
    dimension: str | None = None,
    metric: str | None = None,
    observed: Any = None,
    threshold: str | None = None,
) -> dict[str, Any]:
    digest = hashlib.sha1(
        f"{rule}|{sector}|{dimension}|{metric}|{message}".encode()
    ).hexdigest()[:10]
    event_id = f"{rule}-{digest}"
    payload: dict[str, Any] = {
        "id": event_id,
        "rule": rule,
        "severity": severity,
        "message": message,
    }
    if sector:
        payload["sector"] = sector
    if dimension:
        payload["dimension"] = dimension
    if metric:
        payload["metric"] = metric
    if observed is not None:
        payload["observed"] = observed
    if threshold:
        payload["threshold"] = threshold
    return payload


def _build_alert_events(drift_payload: dict[str, Any]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []

    recommendation = drift_payload.get("recommendation_transition", {})
    previous_reco = str(recommendation.get("previous"))
    current_reco = str(recommendation.get("current"))
    if previous_reco != current_reco:
        severity = "critical" if previous_reco == "go" and current_reco == "no-go" else "warning"
        events.append(
            _event(
                rule="cdr5_recommendation_transition",
                severity=severity,
                message=f"Recommendation transitioned {previous_reco} -> {current_reco}.",
                metric="recommendation.status",
                observed=current_reco,
            )
        )

    for sector, metrics in drift_payload.get("sectors", {}).items():
        current_present = bool(metrics.get("current_present"))
        previous_present = bool(metrics.get("previous_present"))
        if current_present and not previous_present:
            events.append(
                _event(
                    rule="cdr5_sector_introduced",
                    severity="info",
                    message="Sector introduced in current calibration snapshot.",
                    sector=sector,
                )
            )
            continue
        if previous_present and not current_present:
            events.append(
                _event(
                    rule="cdr5_sector_missing",
                    severity="critical",
                    message="Sector missing from current calibration snapshot.",
                    sector=sector,
                )
            )
            continue

        cdr3_all = (metrics.get("cdr3_deltas") or {}).get("all", {})
        pair_delta = int(cdr3_all.get("pair_complete_delta", 0))
        if pair_delta < 0:
            events.append(
                _event(
                    rule="cdr5_pair_completeness_rollup_regression",
                    severity="warning",
                    message=f"All-cohort pair-complete dimensions regressed by {pair_delta}.",
                    sector=sector,
                    metric="cdr3.all.pair_complete_delta",
                    observed=pair_delta,
                    threshold="< 0",
                )
            )
        medium_plus_delta = int(cdr3_all.get("medium_plus_delta", 0))
        if medium_plus_delta < 0:
            events.append(
                _event(
                    rule="cdr5_medium_plus_rollup_regression",
                    severity="warning",
                    message=f"All-cohort medium+ dimensions regressed by {medium_plus_delta}.",
                    sector=sector,
                    metric="cdr3.all.medium_plus_delta",
                    observed=medium_plus_delta,
                    threshold="< 0",
                )
            )

        if int(metrics.get("unmapped_category_delta", 0)) > 0:
            events.append(
                _event(
                    rule="cdr5_unmapped_categories_increase",
                    severity="warning",
                    message="Unmapped risk categories increased week-over-week.",
                    sector=sector,
                    metric="unmapped_category_delta",
                    observed=int(metrics.get("unmapped_category_delta", 0)),
                    threshold="> 0",
                )
            )

        posture_delta_raw = metrics.get("overall_posture_score_proxy_delta")
        posture_delta = (
            float(posture_delta_raw)
            if isinstance(posture_delta_raw, (int, float))
            else None
        )
        if posture_delta is not None and abs(posture_delta) > 0.10:
            direction = "regressed" if posture_delta < 0 else "improved"
            events.append(
                _event(
                    rule="cdr5_overall_posture_proxy_delta",
                    severity="warning",
                    message=f"Overall posture proxy {direction} by {posture_delta:+.4f} (>|0.10|).",
                    sector=sector,
                    metric="overall_posture_score_proxy_delta",
                    observed=posture_delta,
                    threshold="abs(delta) > 0.10",
                )
            )

        for dimension, dim_delta in (metrics.get("dimension_drift") or {}).items():
            transition = str(dim_delta.get("pair_complete_transition", ""))
            if transition == "1->0":
                events.append(
                    _event(
                        rule="cdr5_pair_completeness_dimension_regression",
                        severity="critical",
                        message="Pair completeness regressed from present to absent.",
                        sector=sector,
                        dimension=dimension,
                        metric="pair_complete_transition",
                        observed=transition,
                        threshold="1->0",
                    )
                )

            band_previous = str(dim_delta.get("sample_reliability_band_previous", "unknown"))
            band_current = str(dim_delta.get("sample_reliability_band_current", "unknown"))
            if band_previous != band_current:
                downgraded = _band_rank(band_current) < _band_rank(band_previous)
                severity = "critical" if downgraded and band_current == "low" else "warning"
                if downgraded:
                    events.append(
                        _event(
                            rule="cdr5_sample_reliability_band_downgrade",
                            severity=severity,
                            message=f"Sample reliability band downgraded ({band_previous}->{band_current}).",
                            sector=sector,
                            dimension=dimension,
                            metric="sample_reliability_band_transition",
                            observed=f"{band_previous}->{band_current}",
                        )
                    )

            for metric_name, drop_field in (
                ("exposure evidence", "exposure_drop_pct"),
                ("mitigant evidence", "mitigant_drop_pct"),
                ("source document diversity", "distinct_documents_drop_pct"),
            ):
                drop_pct = float(dim_delta.get(drop_field, 0.0) or 0.0)
                if drop_pct > 30.0:
                    severity = "critical" if drop_pct >= 50.0 else "warning"
                    events.append(
                        _event(
                            rule=f"cdr5_{drop_field}",
                            severity=severity,
                            message=f"{metric_name} dropped by {drop_pct}% (>30%).",
                            sector=sector,
                            dimension=dimension,
                            metric=drop_field,
                            observed=drop_pct,
                            threshold="> 30%",
                        )
                    )

            conflict_rate_delta_raw = dim_delta.get("conflict_rate_proxy_delta")
            conflict_rate_delta = (
                float(conflict_rate_delta_raw)
                if isinstance(conflict_rate_delta_raw, (int, float))
                else None
            )
            if conflict_rate_delta is not None and conflict_rate_delta > 0.20:
                events.append(
                    _event(
                        rule="cdr5_conflict_rate_proxy_spike",
                        severity="critical",
                        message=f"Conflict-rate proxy spiked by {conflict_rate_delta:.4f} (>0.20).",
                        sector=sector,
                        dimension=dimension,
                        metric="conflict_rate_proxy_delta",
                        observed=conflict_rate_delta,
                        threshold="> 0.20",
                    )
                )

    return events


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
        "hold_advisory_generation": requires_incident,
        "alert_count": len(events),
    }


def _next_actions(*, summary: dict[str, Any], on_call_owner: str) -> list[str]:
    if summary["requires_incident"]:
        return [
            f"Open incident immediately and assign owner `{on_call_owner}`.",
            "Freeze advisory package generation until critical CDR-5 events are resolved.",
            "Review latest calibration + drift artifacts and identify source data regressions.",
            "Record remediation timeline and re-run Phase 10 bundle after fixes.",
        ]
    if summary["counts_by_severity"]["warning"] > 0:
        return [
            f"Create follow-up task for owner `{on_call_owner}` within 24h.",
            "Review warning-level CDR-5 events and update weekly evidence notes.",
            "Track next run for recurrence or escalation to critical.",
        ]
    return [
        "No action required beyond weekly evidence archival.",
        "Continue scheduled Phase 10 monitoring cadence.",
    ]


def _write_markdown(path: Path, payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# Bond Corpus Drift Alert Routing",
        "",
        f"- Generated (UTC): `{payload['generated_at_utc']}`",
        f"- Source drift report: `{payload['source_drift_report']}`",
        f"- Drift status: `{payload['drift_status']}`",
        f"- Highest severity: `{summary['highest_severity']}`",
        f"- Requires incident: `{summary['requires_incident']}`",
        f"- Hold advisory generation: `{summary['hold_advisory_generation']}`",
        "",
        "## Alert Summary",
        "",
        f"- Info: `{summary['counts_by_severity']['info']}`",
        f"- Warning: `{summary['counts_by_severity']['warning']}`",
        f"- Critical: `{summary['counts_by_severity']['critical']}`",
        "",
        "## CDR-5 Metric Coverage",
        "",
    ]

    for metric, status in payload.get("cdr5_metric_coverage", {}).items():
        lines.append(f"- `{metric}`: {status}")

    lines.extend(["", "## Routed Events", ""])
    lines.extend(
        [
            "| Severity | Rule | Sector | Dimension | Message |",
            "|---|---|---|---|---|",
        ]
    )

    events = payload.get("events", [])
    if events:
        for event in events:
            lines.append(
                f"| {event.get('severity', '')} | {event.get('rule', '')} | "
                f"{event.get('sector', '-')} | {event.get('dimension', '-')} | "
                f"{event.get('message', '').replace('|', '/')} |"
            )
    else:
        lines.append("| none | - | - | - | No routed alert events. |")

    lines.extend(["", "## Escalation Actions", ""])
    for action in payload.get("next_actions", []):
        lines.append(f"- {action}")

    path.write_text("\n".join(lines), encoding="utf-8")


def route_bond_corpus_drift_alerts(
    *,
    reports_dir: Path,
    drift_report: Path | None,
    on_call_owner: str,
    policy_version: str,
) -> AlertRoutingResult:
    reports_dir.mkdir(parents=True, exist_ok=True)
    stamp = _timestamp()
    output_json = reports_dir / f"bond_corpus_alert_routing_{stamp}.json"
    output_md = reports_dir / f"bond_corpus_alert_routing_{stamp}.md"

    source_report = drift_report.resolve() if drift_report else _latest_drift_report(reports_dir)
    if source_report is None or not source_report.exists():
        payload = {
            "generated_at_utc": datetime.now(UTC).isoformat(),
            "source_drift_report": None,
            "drift_status": "missing",
            "policy_version": policy_version,
            "on_call_owner": on_call_owner,
            "cdr5_metric_coverage": {},
            "events": [
                _event(
                    rule="cdr5_missing_drift_report",
                    severity="warning",
                    message="No drift report was found to route.",
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

    drift_payload = _load_json(source_report)
    events = _build_alert_events(drift_payload)
    summary = _summary(events)
    payload = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "source_drift_report": source_report.name,
        "drift_status": drift_payload.get("drift_status"),
        "policy_version": policy_version,
        "on_call_owner": on_call_owner,
        "cdr5_metric_coverage": drift_payload.get("cdr5_metric_coverage", {}),
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
    parser = argparse.ArgumentParser(description="Route bond corpus drift alerts into escalation artifacts.")
    parser.add_argument(
        "--reports-dir",
        type=Path,
        default=_default_reports_dir(),
        help="Directory containing bond_corpus_drift_<timestamp>.json reports.",
    )
    parser.add_argument(
        "--drift-report",
        type=Path,
        default=None,
        help="Optional explicit drift report JSON path. If omitted, latest report is used.",
    )
    parser.add_argument(
        "--on-call-owner",
        default="unassigned",
        help="Owner to stamp into escalation actions.",
    )
    parser.add_argument(
        "--policy-version",
        default="cdr5-alert-routing-v1",
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
    result = route_bond_corpus_drift_alerts(
        reports_dir=args.reports_dir.resolve(),
        drift_report=args.drift_report.resolve() if args.drift_report else None,
        on_call_owner=str(args.on_call_owner),
        policy_version=str(args.policy_version),
    )
    print(f"[bond-corpus-alert-routing] highest_severity={result.highest_severity}")
    print(f"[bond-corpus-alert-routing] requires_incident={result.requires_incident}")
    print(f"[bond-corpus-alert-routing] critical_count={result.critical_count}")
    print(f"[bond-corpus-alert-routing] markdown={result.report_md_path.as_posix()}")
    print(f"[bond-corpus-alert-routing] json={result.report_json_path.as_posix()}")
    if args.fail_on_critical and result.critical_count > 0:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
