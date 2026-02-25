"""
Assess OPS-1001 launch telemetry trends and threshold-tuning recommendations.

Usage:
    python scripts/assess_ops1001_telemetry_trends.py
    python scripts/assess_ops1001_telemetry_trends.py --events-path <path> --output-dir <path>
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

DEFAULT_THRESHOLD_401_PER_1K = 40.0
DEFAULT_THRESHOLD_403_PER_1K = 20.0
DEFAULT_THRESHOLD_CROSS_TENANT_PER_1K = 10.0


@dataclass
class AssessmentResult:
    report_json_path: Path
    report_md_path: Path
    status: str
    reasons: list[str]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _default_events_path() -> Path:
    return _repo_root() / "reports" / "phase10_postlaunch" / "ops1001_telemetry_events.jsonl"


def _default_output_dir() -> Path:
    return _repo_root() / "reports" / "phase10_postlaunch"


def _timestamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%d_%H%M%S")


def _safe_per_1k(count: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round((count / total) * 1000.0, 2)


def _coerce_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.isdigit():
            return int(stripped)
    return None


def _parse_timestamp(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(float(value), tz=UTC)
        except (OverflowError, OSError, ValueError):
            return None
    text = str(value).strip()
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


def _extract_timestamp(event: dict[str, Any]) -> datetime | None:
    for key in ("timestamp", "time", "ts", "created_at", "event_time", "@timestamp"):
        parsed = _parse_timestamp(event.get(key))
        if parsed is not None:
            return parsed
    audit_event = event.get("audit_event")
    if isinstance(audit_event, dict):
        parsed = _parse_timestamp(audit_event.get("timestamp"))
        if parsed is not None:
            return parsed
    return None


def _extract_status_code(event: dict[str, Any]) -> int | None:
    for key in ("status_code", "status", "http_status", "response_status"):
        value = _coerce_int(event.get(key))
        if value is not None:
            return value

    http_payload = event.get("http")
    if isinstance(http_payload, dict):
        for key in ("status_code", "status", "response_status"):
            value = _coerce_int(http_payload.get(key))
            if value is not None:
                return value

    metadata = event.get("metadata")
    if isinstance(metadata, dict):
        for key in ("status_code", "http_status", "response_status"):
            value = _coerce_int(metadata.get(key))
            if value is not None:
                return value

    return None


def _extract_string_candidates(event: dict[str, Any]) -> list[str]:
    candidates: list[str] = []
    for key in ("detail", "message", "error", "reason"):
        value = event.get(key)
        if isinstance(value, str):
            candidates.append(value)

    metadata = event.get("metadata")
    if isinstance(metadata, dict):
        for key in ("detail", "message", "reason"):
            value = metadata.get(key)
            if isinstance(value, str):
                candidates.append(value)

    audit_event = event.get("audit_event")
    if isinstance(audit_event, dict):
        for key in ("target_id", "action", "target_type"):
            value = audit_event.get(key)
            if isinstance(value, str):
                candidates.append(value)
        audit_meta = audit_event.get("metadata")
        if isinstance(audit_meta, dict):
            for key in ("detail", "message", "reason"):
                value = audit_meta.get(key)
                if isinstance(value, str):
                    candidates.append(value)

    return candidates


def _is_cross_tenant_denied(event: dict[str, Any]) -> bool:
    for key in ("cross_tenant_denied", "is_cross_tenant_denied"):
        value = event.get(key)
        if isinstance(value, bool):
            return value

    metadata = event.get("metadata")
    if isinstance(metadata, dict):
        for key in ("cross_tenant_denied", "is_cross_tenant_denied"):
            value = metadata.get(key)
            if isinstance(value, bool):
                return value

    haystack = " ".join(_extract_string_candidates(event)).lower()
    return "cross-tenant access denied" in haystack or "cross tenant access denied" in haystack


def _load_events(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            rows.append(parsed)
    return rows


def _metric_payload(
    *,
    name: str,
    count: int,
    total_requests: int,
    daily_counts: Counter[str],
    daily_totals: Counter[str],
    threshold_per_1k: float,
    window_days: int,
    allow_threshold_suggestion: bool,
) -> dict[str, Any]:
    overall_rate_per_1k = _safe_per_1k(count, total_requests)
    max_daily_count = 0
    max_daily_rate_per_1k = 0.0
    breach_days: list[str] = []

    for day, day_count in sorted(daily_counts.items()):
        day_total = daily_totals.get(day, 0)
        day_rate = _safe_per_1k(day_count, day_total)
        if day_count > max_daily_count:
            max_daily_count = day_count
        if day_rate > max_daily_rate_per_1k:
            max_daily_rate_per_1k = day_rate
        if day_rate > threshold_per_1k:
            breach_days.append(day)

    suggested_threshold_per_1k = threshold_per_1k
    if allow_threshold_suggestion and total_requests > 0:
        growth_factor_daily = max_daily_rate_per_1k * 1.2
        growth_factor_overall = overall_rate_per_1k * 1.5
        suggested_threshold_per_1k = round(
            max(threshold_per_1k, growth_factor_daily, growth_factor_overall, 0.1),
            2,
        )

    return {
        "name": name,
        "count": count,
        "rate_per_1k": overall_rate_per_1k,
        "threshold_per_1k": round(threshold_per_1k, 2),
        "max_daily_count": max_daily_count,
        "max_daily_rate_per_1k": round(max_daily_rate_per_1k, 2),
        "breach_days": breach_days,
        "breach_count": len(breach_days),
        "suggested_threshold_per_1k": suggested_threshold_per_1k,
        "window_days": int(window_days),
    }


def _write_markdown(path: Path, payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    recommendation = payload["recommendation"]
    lines = [
        "# OPS-1001 Telemetry Trend Assessment",
        "",
        f"- Generated (UTC): `{payload['generated_at_utc']}`",
        f"- Source events file: `{payload['source_events_file']}`",
        f"- Recommendation status: `{recommendation['status']}`",
        "",
        "## Window Summary",
        "",
        f"- Window start (UTC): `{summary['window_start_utc']}`",
        f"- Window end (UTC): `{summary['window_end_utc']}`",
        f"- Window days configured: `{summary['window_days']}`",
        f"- Events parsed in window: `{summary['events_in_window']}`",
        f"- Total requests observed: `{summary['total_requests']}`",
        f"- Distinct event days: `{summary['days_observed']}`",
        "",
        "## Metric Rates",
        "",
        "| Metric | Count | Rate / 1k | Threshold / 1k | Max Daily / 1k | Breach Days |",
        "|---|---:|---:|---:|---:|---:|",
    ]

    for metric_name in ("unauthorized_401", "forbidden_403", "cross_tenant_denied"):
        metric = payload["metrics"][metric_name]
        lines.append(
            f"| {metric_name} | {metric['count']} | {metric['rate_per_1k']} | "
            f"{metric['threshold_per_1k']} | {metric['max_daily_rate_per_1k']} | {metric['breach_count']} |"
        )

    lines.extend(["", "## Threshold Recommendations", ""])
    if recommendation["threshold_updates"]:
        for update in recommendation["threshold_updates"]:
            lines.append(
                f"- `{update['metric']}`: `{update['current_threshold_per_1k']}` -> "
                f"`{update['suggested_threshold_per_1k']}` ({update['reason']})"
            )
    else:
        lines.append("- No threshold updates suggested.")

    lines.extend(["", "## Recommendation Notes", ""])
    if recommendation["reasons"]:
        for reason in recommendation["reasons"]:
            lines.append(f"- {reason}")
    else:
        lines.append("- No automated notes generated.")

    if payload["daily_counts"]:
        lines.extend(
            [
                "",
                "## Daily Counts",
                "",
                "| Day (UTC) | Total Requests | 401 | 403 | Cross-Tenant Denied |",
                "|---|---:|---:|---:|---:|",
            ]
        )
        for day, counts in payload["daily_counts"].items():
            lines.append(
                f"| {day} | {counts['total_requests']} | {counts['unauthorized_401']} | "
                f"{counts['forbidden_403']} | {counts['cross_tenant_denied']} |"
            )

    path.write_text("\n".join(lines), encoding="utf-8")


def assess_ops1001_telemetry_trends(
    *,
    events_path: Path,
    output_dir: Path,
    window_days: int,
    min_total_requests: int,
    threshold_401_per_1k: float,
    threshold_403_per_1k: float,
    threshold_cross_tenant_per_1k: float,
) -> AssessmentResult:
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = _timestamp()
    output_json = output_dir / f"ops1001_telemetry_trends_{stamp}.json"
    output_md = output_dir / f"ops1001_telemetry_trends_{stamp}.md"

    now_utc = datetime.now(UTC)
    window_start = now_utc - timedelta(days=max(window_days, 1))
    raw_events = _load_events(events_path)

    daily_totals: Counter[str] = Counter()
    daily_401: Counter[str] = Counter()
    daily_403: Counter[str] = Counter()
    daily_cross_tenant: Counter[str] = Counter()

    events_in_window = 0
    total_requests = 0
    count_401 = 0
    count_403 = 0
    count_cross_tenant = 0

    for event in raw_events:
        event_ts = _extract_timestamp(event)
        if event_ts is None or event_ts < window_start:
            continue
        events_in_window += 1
        day_key = event_ts.date().isoformat()

        status_code = _extract_status_code(event)
        if status_code is not None and 100 <= status_code < 600:
            total_requests += 1
            daily_totals[day_key] += 1
            if status_code == 401:
                count_401 += 1
                daily_401[day_key] += 1
            if status_code == 403:
                count_403 += 1
                daily_403[day_key] += 1

        if _is_cross_tenant_denied(event):
            count_cross_tenant += 1
            daily_cross_tenant[day_key] += 1

    reasons: list[str] = []
    status = "stable"
    allow_threshold_suggestion = total_requests >= min_total_requests

    if not events_path.exists():
        status = "insufficient_data"
        reasons.append("No telemetry events file found; supply OPS-1001 event export JSONL.")
    elif events_in_window == 0:
        status = "insufficient_data"
        reasons.append("No parseable telemetry events found inside configured time window.")
    elif total_requests == 0:
        status = "insufficient_data"
        reasons.append("No request-status telemetry rows (HTTP status code) available in window.")
    elif total_requests < min_total_requests:
        status = "hold"
        reasons.append(
            f"Observed request volume ({total_requests}) is below minimum calibration floor ({min_total_requests})."
        )

    metric_401 = _metric_payload(
        name="unauthorized_401",
        count=count_401,
        total_requests=total_requests,
        daily_counts=daily_401,
        daily_totals=daily_totals,
        threshold_per_1k=threshold_401_per_1k,
        window_days=window_days,
        allow_threshold_suggestion=allow_threshold_suggestion,
    )
    metric_403 = _metric_payload(
        name="forbidden_403",
        count=count_403,
        total_requests=total_requests,
        daily_counts=daily_403,
        daily_totals=daily_totals,
        threshold_per_1k=threshold_403_per_1k,
        window_days=window_days,
        allow_threshold_suggestion=allow_threshold_suggestion,
    )
    metric_cross = _metric_payload(
        name="cross_tenant_denied",
        count=count_cross_tenant,
        total_requests=total_requests,
        daily_counts=daily_cross_tenant,
        daily_totals=daily_totals,
        threshold_per_1k=threshold_cross_tenant_per_1k,
        window_days=window_days,
        allow_threshold_suggestion=allow_threshold_suggestion,
    )

    metrics_payload = {
        "unauthorized_401": metric_401,
        "forbidden_403": metric_403,
        "cross_tenant_denied": metric_cross,
    }

    if status in {"stable", "hold"}:
        breached = [
            metric_name
            for metric_name, metric in metrics_payload.items()
            if metric["breach_count"] > 0 or metric["rate_per_1k"] > metric["threshold_per_1k"]
        ]
        if breached and status == "stable":
            status = "tune_now"
            reasons.append(
                "Threshold breach detected for: " + ", ".join(sorted(breached)) + "."
            )
        elif not reasons and status == "stable":
            reasons.append("All monitored OPS-1001 rates are within configured thresholds.")

    threshold_updates: list[dict[str, Any]] = []
    for metric_name, metric in metrics_payload.items():
        current = float(metric["threshold_per_1k"])
        suggested = float(metric["suggested_threshold_per_1k"])
        if suggested > current:
            threshold_updates.append(
                {
                    "metric": metric_name,
                    "current_threshold_per_1k": current,
                    "suggested_threshold_per_1k": suggested,
                    "reason": "Observed rates exceed current threshold envelope.",
                }
            )

    if status == "tune_now" and not threshold_updates:
        reasons.append("Tune thresholds manually; automated suggestion could not compute a higher envelope.")

    daily_payload = {}
    for day in sorted(
        set(daily_totals.keys()) | set(daily_401.keys()) | set(daily_403.keys()) | set(daily_cross_tenant.keys())
    ):
        daily_payload[day] = {
            "total_requests": int(daily_totals.get(day, 0)),
            "unauthorized_401": int(daily_401.get(day, 0)),
            "forbidden_403": int(daily_403.get(day, 0)),
            "cross_tenant_denied": int(daily_cross_tenant.get(day, 0)),
        }

    payload = {
        "generated_at_utc": now_utc.isoformat(),
        "source_events_file": str(events_path),
        "summary": {
            "window_start_utc": window_start.isoformat(),
            "window_end_utc": now_utc.isoformat(),
            "window_days": int(window_days),
            "events_in_window": int(events_in_window),
            "total_requests": int(total_requests),
            "days_observed": len(daily_payload),
            "min_total_requests_for_calibration": int(min_total_requests),
        },
        "threshold_config": {
            "unauthorized_401_per_1k": float(round(threshold_401_per_1k, 2)),
            "forbidden_403_per_1k": float(round(threshold_403_per_1k, 2)),
            "cross_tenant_denied_per_1k": float(round(threshold_cross_tenant_per_1k, 2)),
        },
        "metrics": metrics_payload,
        "daily_counts": daily_payload,
        "recommendation": {
            "status": status,
            "reasons": reasons,
            "threshold_updates": threshold_updates,
        },
    }

    output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    _write_markdown(output_md, payload)
    return AssessmentResult(
        report_json_path=output_json,
        report_md_path=output_md,
        status=status,
        reasons=reasons,
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Assess OPS-1001 telemetry trends and threshold tuning recommendations.",
    )
    parser.add_argument(
        "--events-path",
        type=Path,
        default=_default_events_path(),
        help="Path to telemetry export JSONL file (one JSON object per line).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=_default_output_dir(),
        help="Directory to write telemetry trend reports.",
    )
    parser.add_argument(
        "--window-days",
        type=int,
        default=7,
        help="Lookback window in days.",
    )
    parser.add_argument(
        "--min-total-requests",
        type=int,
        default=200,
        help="Minimum request sample required to auto-tune thresholds.",
    )
    parser.add_argument(
        "--threshold-401-per-1k",
        type=float,
        default=DEFAULT_THRESHOLD_401_PER_1K,
        help="Current 401 alert threshold (events per 1,000 requests).",
    )
    parser.add_argument(
        "--threshold-403-per-1k",
        type=float,
        default=DEFAULT_THRESHOLD_403_PER_1K,
        help="Current 403 alert threshold (events per 1,000 requests).",
    )
    parser.add_argument(
        "--threshold-cross-tenant-per-1k",
        type=float,
        default=DEFAULT_THRESHOLD_CROSS_TENANT_PER_1K,
        help="Current cross-tenant-denied threshold (events per 1,000 requests).",
    )
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    result = assess_ops1001_telemetry_trends(
        events_path=args.events_path.resolve(),
        output_dir=args.output_dir.resolve(),
        window_days=max(args.window_days, 1),
        min_total_requests=max(args.min_total_requests, 1),
        threshold_401_per_1k=max(args.threshold_401_per_1k, 0.0),
        threshold_403_per_1k=max(args.threshold_403_per_1k, 0.0),
        threshold_cross_tenant_per_1k=max(args.threshold_cross_tenant_per_1k, 0.0),
    )
    print(f"[ops1001-telemetry] status={result.status}")
    print(f"[ops1001-telemetry] markdown={result.report_md_path.as_posix()}")
    print(f"[ops1001-telemetry] json={result.report_json_path.as_posix()}")
    if result.reasons:
        print("[ops1001-telemetry] reasons:")
        for reason in result.reasons:
            print(f"- {reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
