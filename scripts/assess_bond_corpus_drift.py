"""
Assess week-over-week drift for bond corpus calibration snapshots.

Usage:
    python scripts/assess_bond_corpus_drift.py
    python scripts/assess_bond_corpus_drift.py --reports-dir reports/phase10_postlaunch
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

RISK_DIMENSIONS = (
    "risk.technology",
    "risk.construction",
    "risk.market",
    "risk.regulatory",
    "risk.feedstock",
)
COHORTS = ("all", "revenue", "conduit", "private_activity")


@dataclass
class DriftResult:
    report_json_path: Path
    report_md_path: Path
    drift_status: str
    alerts: list[str]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _default_reports_dir() -> Path:
    return _repo_root() / "reports" / "phase10_postlaunch"


def _timestamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%d_%H%M%S")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _delta_int(current: Any, previous: Any) -> int:
    return int(current or 0) - int(previous or 0)


def _as_float(value: Any) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _delta_float(current: Any, previous: Any) -> float:
    return round(_as_float(current) - _as_float(previous), 4)


def _delta_float_optional(*, current: Any, previous: Any, enabled: bool) -> float | None:
    if not enabled:
        return None
    return _delta_float(current, previous)


def _safe_drop_pct(*, current: int, previous: int) -> float:
    if previous <= 0 or current >= previous:
        return 0.0
    return round(((previous - current) / previous) * 100.0, 2)


def _sample_reliability_band(entry: dict[str, Any]) -> str:
    if int(entry.get("meets_cdr1_high", 0)) == 1:
        return "high"
    if int(entry.get("meets_cdr1_medium", 0)) == 1:
        return "medium"
    return "low"


def _band_rank(band: str) -> int:
    return {"low": 0, "medium": 1, "high": 2}.get(str(band).strip().lower(), -1)


def _sector_drift(
    *,
    current_sector: dict[str, Any] | None,
    previous_sector: dict[str, Any] | None,
) -> dict[str, Any]:
    current_present = current_sector is not None
    previous_present = previous_sector is not None
    current_cdr3 = (
        (current_sector or {})
        .get("cohort_assessment", {})
        .get("cdr3_status", {})
    )
    previous_cdr3 = (
        (previous_sector or {})
        .get("cohort_assessment", {})
        .get("cdr3_status", {})
    )
    current_rollup = (
        (current_sector or {})
        .get("cohort_assessment", {})
        .get("dimension_rollup", {})
        .get("all", {})
    )
    previous_rollup = (
        (previous_sector or {})
        .get("cohort_assessment", {})
        .get("dimension_rollup", {})
        .get("all", {})
    )

    cdr3_deltas: dict[str, Any] = {}
    for cohort in COHORTS:
        current_entry = current_cdr3.get(cohort, {})
        previous_entry = previous_cdr3.get(cohort, {})
        cdr3_deltas[cohort] = {
            "pair_complete_current": int(current_entry.get("dimensions_with_pair_complete", 0)),
            "pair_complete_previous": int(previous_entry.get("dimensions_with_pair_complete", 0)),
            "pair_complete_delta": _delta_int(
                current_entry.get("dimensions_with_pair_complete", 0),
                previous_entry.get("dimensions_with_pair_complete", 0),
            ),
            "medium_plus_current": int(current_entry.get("dimensions_at_medium_plus", 0)),
            "medium_plus_previous": int(previous_entry.get("dimensions_at_medium_plus", 0)),
            "medium_plus_delta": _delta_int(
                current_entry.get("dimensions_at_medium_plus", 0),
                previous_entry.get("dimensions_at_medium_plus", 0),
            ),
        }

    dimension_drift: dict[str, Any] = {}
    for dimension in RISK_DIMENSIONS:
        current_entry = current_rollup.get(dimension, {})
        previous_entry = previous_rollup.get(dimension, {})
        exposure_current = int(current_entry.get("exposure_count", 0))
        exposure_previous = int(previous_entry.get("exposure_count", 0))
        mitigant_current = int(current_entry.get("mitigant_count", 0))
        mitigant_previous = int(previous_entry.get("mitigant_count", 0))
        docs_current = int(current_entry.get("distinct_documents", 0))
        docs_previous = int(previous_entry.get("distinct_documents", 0))
        sample_band_current = _sample_reliability_band(current_entry)
        sample_band_previous = _sample_reliability_band(previous_entry)
        conflict_rate_proxy_current = _as_float(current_entry.get("conflict_rate_proxy", 0.0))
        conflict_rate_proxy_previous = _as_float(previous_entry.get("conflict_rate_proxy", 0.0))
        posture_score_proxy_current = _as_float(current_entry.get("dimension_posture_score_proxy", 0.0))
        posture_score_proxy_previous = _as_float(previous_entry.get("dimension_posture_score_proxy", 0.0))
        has_conflict_proxy_previous = "conflict_rate_proxy" in previous_entry
        has_posture_proxy_previous = "dimension_posture_score_proxy" in previous_entry
        pair_current = int(current_entry.get("pair_complete", 0))
        pair_previous = int(previous_entry.get("pair_complete", 0))
        dimension_drift[dimension] = {
            "pair_complete_current": pair_current,
            "pair_complete_previous": pair_previous,
            "pair_complete_transition": f"{pair_previous}->{pair_current}",
            "exposure_current": exposure_current,
            "exposure_previous": exposure_previous,
            "exposure_delta": _delta_int(exposure_current, exposure_previous),
            "exposure_drop_pct": _safe_drop_pct(current=exposure_current, previous=exposure_previous),
            "mitigant_current": mitigant_current,
            "mitigant_previous": mitigant_previous,
            "mitigant_delta": _delta_int(mitigant_current, mitigant_previous),
            "mitigant_drop_pct": _safe_drop_pct(current=mitigant_current, previous=mitigant_previous),
            "distinct_documents_current": docs_current,
            "distinct_documents_previous": docs_previous,
            "distinct_documents_delta": _delta_int(docs_current, docs_previous),
            "distinct_documents_drop_pct": _safe_drop_pct(current=docs_current, previous=docs_previous),
            "sample_reliability_band_current": sample_band_current,
            "sample_reliability_band_previous": sample_band_previous,
            "sample_reliability_band_transition": f"{sample_band_previous}->{sample_band_current}",
            "conflict_rate_proxy_current": conflict_rate_proxy_current,
            "conflict_rate_proxy_previous": conflict_rate_proxy_previous,
            "conflict_rate_proxy_delta": _delta_float_optional(
                current=conflict_rate_proxy_current,
                previous=conflict_rate_proxy_previous,
                enabled=has_conflict_proxy_previous,
            ),
            "dimension_posture_score_proxy_current": posture_score_proxy_current,
            "dimension_posture_score_proxy_previous": posture_score_proxy_previous,
            "dimension_posture_score_proxy_delta": _delta_float_optional(
                current=posture_score_proxy_current,
                previous=posture_score_proxy_previous,
                enabled=has_posture_proxy_previous,
            ),
        }

    current_meta = current_rollup.get("_meta", {})
    previous_meta = previous_rollup.get("_meta", {})
    overall_posture_score_proxy_current = _as_float(current_meta.get("overall_posture_score_proxy", 0.0))
    overall_posture_score_proxy_previous = _as_float(previous_meta.get("overall_posture_score_proxy", 0.0))
    has_overall_posture_proxy_previous = "overall_posture_score_proxy" in previous_meta
    conflict_rate_proxy_avg_current = _as_float(current_meta.get("conflict_rate_proxy_avg", 0.0))
    conflict_rate_proxy_avg_previous = _as_float(previous_meta.get("conflict_rate_proxy_avg", 0.0))
    has_conflict_rate_proxy_avg_previous = "conflict_rate_proxy_avg" in previous_meta
    conflict_rate_proxy_max_current = _as_float(current_meta.get("conflict_rate_proxy_max", 0.0))
    conflict_rate_proxy_max_previous = _as_float(previous_meta.get("conflict_rate_proxy_max", 0.0))
    has_conflict_rate_proxy_max_previous = "conflict_rate_proxy_max" in previous_meta
    return {
        "current_present": current_present,
        "previous_present": previous_present,
        "cdr3_deltas": cdr3_deltas,
        "dimension_drift": dimension_drift,
        "rows_considered_delta": _delta_int(
            current_meta.get("rows_considered", 0),
            previous_meta.get("rows_considered", 0),
        ),
        "unmapped_category_delta": _delta_int(
            current_meta.get("unmapped_category_count", 0),
            previous_meta.get("unmapped_category_count", 0),
        ),
        "overall_posture_score_proxy_current": overall_posture_score_proxy_current,
        "overall_posture_score_proxy_previous": overall_posture_score_proxy_previous,
        "overall_posture_score_proxy_delta": _delta_float_optional(
            current=overall_posture_score_proxy_current,
            previous=overall_posture_score_proxy_previous,
            enabled=has_overall_posture_proxy_previous,
        ),
        "conflict_rate_proxy_avg_current": conflict_rate_proxy_avg_current,
        "conflict_rate_proxy_avg_previous": conflict_rate_proxy_avg_previous,
        "conflict_rate_proxy_avg_delta": _delta_float_optional(
            current=conflict_rate_proxy_avg_current,
            previous=conflict_rate_proxy_avg_previous,
            enabled=has_conflict_rate_proxy_avg_previous,
        ),
        "conflict_rate_proxy_max_current": conflict_rate_proxy_max_current,
        "conflict_rate_proxy_max_previous": conflict_rate_proxy_max_previous,
        "conflict_rate_proxy_max_delta": _delta_float_optional(
            current=conflict_rate_proxy_max_current,
            previous=conflict_rate_proxy_max_previous,
            enabled=has_conflict_rate_proxy_max_previous,
        ),
    }


def _write_markdown(report_path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# Bond Corpus Calibration Drift",
        "",
        f"- Generated (UTC): `{payload['generated_at_utc']}`",
        f"- Drift status: `{payload['drift_status']}`",
        f"- Baseline report: `{payload['baseline_report']}`",
        f"- Current report: `{payload['current_report']}`",
        "",
        "## Recommendation Transition",
        "",
        f"- Previous: `{payload['recommendation_transition']['previous']}`",
        f"- Current: `{payload['recommendation_transition']['current']}`",
        "",
    ]

    alerts = payload.get("alerts", [])
    lines.append("## Alerts")
    lines.append("")
    if alerts:
        for alert in alerts:
            lines.append(f"- {alert}")
    else:
        lines.append("- No significant drift alerts detected.")

    lines.extend(["", "## Sector Drift", ""])
    for sector, sector_payload in payload.get("sectors", {}).items():
        lines.extend([f"### {sector}", ""])
        lines.extend(
            [
                "| Cohort | Pair Complete (Prev) | Pair Complete (Curr) | Delta |",
                "|---|---:|---:|---:|",
            ]
        )
        for cohort, cohort_delta in sector_payload.get("cdr3_deltas", {}).items():
            lines.append(
                f"| {cohort} | {cohort_delta['pair_complete_previous']} | "
                f"{cohort_delta['pair_complete_current']} | {cohort_delta['pair_complete_delta']} |"
            )
        lines.extend(
            [
                "",
                "| Dimension | Pair Transition | Exposure Delta | Mitigant Delta | Distinct Docs Delta |",
                "|---|---|---:|---:|---:|",
            ]
        )
        for dimension, dim_delta in sector_payload.get("dimension_drift", {}).items():
            lines.append(
                f"| {dimension} | {dim_delta['pair_complete_transition']} | "
                f"{dim_delta['exposure_delta']} | {dim_delta['mitigant_delta']} | "
                f"{dim_delta['distinct_documents_delta']} |"
            )
            lines.append(
                f"| {dimension} (bands/docs) | `{dim_delta.get('sample_reliability_band_transition', 'n/a')}` | "
                f"`{dim_delta.get('exposure_drop_pct', 0.0)}%` exposure drop | "
                f"`{dim_delta.get('mitigant_drop_pct', 0.0)}%` mitigant drop | "
                f"`{dim_delta.get('distinct_documents_drop_pct', 0.0)}%` doc drop |"
            )
        lines.extend(
            [
                "",
                f"- Rows considered delta: `{sector_payload.get('rows_considered_delta', 0)}`",
                f"- Unmapped category delta: `{sector_payload.get('unmapped_category_delta', 0)}`",
                f"- Posture score proxy delta: `{sector_payload.get('overall_posture_score_proxy_delta', 'n/a')}`",
                f"- Conflict proxy avg delta: `{sector_payload.get('conflict_rate_proxy_avg_delta', 'n/a')}`",
                f"- Conflict proxy max delta: `{sector_payload.get('conflict_rate_proxy_max_delta', 'n/a')}`",
                "",
            ]
        )

    report_path.write_text("\n".join(lines), encoding="utf-8")


def assess_drift(*, reports_dir: Path) -> DriftResult:
    reports_dir.mkdir(parents=True, exist_ok=True)
    calibration_reports = sorted(reports_dir.glob("bond_corpus_calibration_*.json"))
    stamp = _timestamp()
    output_json = reports_dir / f"bond_corpus_drift_{stamp}.json"
    output_md = reports_dir / f"bond_corpus_drift_{stamp}.md"

    if len(calibration_reports) < 2:
        payload = {
            "generated_at_utc": datetime.now(UTC).isoformat(),
            "drift_status": "insufficient_history",
            "baseline_report": None,
            "current_report": str(calibration_reports[-1].name) if calibration_reports else None,
            "recommendation_transition": {
                "previous": None,
                "current": None,
            },
            "sectors": {},
            "alerts": [
                "At least two bond_corpus_calibration reports are required for drift assessment.",
            ],
        }
        output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        _write_markdown(output_md, payload)
        return DriftResult(
            report_json_path=output_json,
            report_md_path=output_md,
            drift_status="insufficient_history",
            alerts=payload["alerts"],
        )

    previous_report_path = calibration_reports[-2]
    current_report_path = calibration_reports[-1]
    previous_payload = _load_json(previous_report_path)
    current_payload = _load_json(current_report_path)

    sector_names = sorted(
        set(previous_payload.get("sectors", {}).keys()) | set(current_payload.get("sectors", {}).keys())
    )
    sector_drift = {
        sector: _sector_drift(
            current_sector=current_payload.get("sectors", {}).get(sector),
            previous_sector=previous_payload.get("sectors", {}).get(sector),
        )
        for sector in sector_names
    }

    previous_reco = previous_payload.get("recommendation", {}).get("status")
    current_reco = current_payload.get("recommendation", {}).get("status")
    alerts: list[str] = []
    if previous_reco != current_reco:
        alerts.append(f"Recommendation status transition: {previous_reco} -> {current_reco}.")

    for sector, metrics in sector_drift.items():
        current_present = bool(metrics.get("current_present"))
        previous_present = bool(metrics.get("previous_present"))
        if current_present and not previous_present:
            alerts.append(f"{sector}: sector introduced in current calibration snapshot.")
            continue
        if previous_present and not current_present:
            alerts.append(f"{sector}: sector missing from current calibration snapshot.")
            continue

        pair_delta = int(metrics["cdr3_deltas"]["all"]["pair_complete_delta"])
        if pair_delta < 0:
            alerts.append(f"{sector}: all-cohort pair-complete dimensions regressed by {pair_delta}.")
        elif pair_delta > 0:
            alerts.append(f"{sector}: all-cohort pair-complete dimensions improved by +{pair_delta}.")
        medium_plus_delta = int(metrics["cdr3_deltas"]["all"]["medium_plus_delta"])
        if medium_plus_delta < 0:
            alerts.append(f"{sector}: all-cohort medium+ dimensions regressed by {medium_plus_delta}.")
        elif medium_plus_delta > 0:
            alerts.append(f"{sector}: all-cohort medium+ dimensions improved by +{medium_plus_delta}.")
        if int(metrics.get("unmapped_category_delta", 0)) > 0:
            alerts.append(f"{sector}: unmapped risk categories increased.")
        posture_delta = metrics.get("overall_posture_score_proxy_delta")
        if isinstance(posture_delta, (float, int)) and abs(float(posture_delta)) > 0.10:
            direction = "regressed" if posture_delta < 0 else "improved"
            alerts.append(
                f"{sector}: overall posture proxy {direction} by {posture_delta:+.4f} (>|0.10|)."
            )

        for dimension, dim_delta in metrics.get("dimension_drift", {}).items():
            transition = dim_delta.get("pair_complete_transition")
            if transition == "1->0":
                alerts.append(f"{sector} {dimension}: pair completeness regressed (1->0).")
            band_previous = str(dim_delta.get("sample_reliability_band_previous", "unknown"))
            band_current = str(dim_delta.get("sample_reliability_band_current", "unknown"))
            if band_previous != band_current:
                direction = "downgraded" if _band_rank(band_current) < _band_rank(band_previous) else "improved"
                alerts.append(
                    f"{sector} {dimension}: sample reliability band {direction} ({band_previous}->{band_current})."
                )
            if float(dim_delta.get("exposure_drop_pct", 0.0)) > 30.0:
                alerts.append(
                    f"{sector} {dimension}: exposure evidence dropped by "
                    f"{dim_delta.get('exposure_drop_pct', 0.0)}% (>30%)."
                )
            if float(dim_delta.get("mitigant_drop_pct", 0.0)) > 30.0:
                alerts.append(
                    f"{sector} {dimension}: mitigant evidence dropped by "
                    f"{dim_delta.get('mitigant_drop_pct', 0.0)}% (>30%)."
                )
            if float(dim_delta.get("distinct_documents_drop_pct", 0.0)) > 30.0:
                alerts.append(
                    f"{sector} {dimension}: source document diversity dropped by "
                    f"{dim_delta.get('distinct_documents_drop_pct', 0.0)}% (>30%)."
                )
            conflict_rate_delta = dim_delta.get("conflict_rate_proxy_delta")
            if isinstance(conflict_rate_delta, (float, int)) and float(conflict_rate_delta) > 0.20:
                alerts.append(
                    f"{sector} {dimension}: conflict-rate proxy spiked by "
                    f"{conflict_rate_delta:.4f} (>0.20)."
                )

    drift_status = "changed" if alerts else "stable"
    payload = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "drift_status": drift_status,
        "baseline_report": str(previous_report_path.name),
        "current_report": str(current_report_path.name),
        "recommendation_transition": {
            "previous": previous_reco,
            "current": current_reco,
        },
        "cdr5_metric_coverage": {
            "reliability_band_change": "evaluated via sample-size proxy transitions",
            "overall_posture_score_delta_gt_0_10": "evaluated via posture_score_proxy series",
            "conflict_rate_spike_gt_0_20": "evaluated via conflict_rate_proxy series",
            "evidence_count_drop_gt_30pct": "evaluated",
        },
        "sectors": sector_drift,
        "alerts": alerts,
    }
    output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    _write_markdown(output_md, payload)

    return DriftResult(
        report_json_path=output_json,
        report_md_path=output_md,
        drift_status=drift_status,
        alerts=alerts,
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Assess drift between calibration snapshots.")
    parser.add_argument(
        "--reports-dir",
        type=Path,
        default=_default_reports_dir(),
        help="Directory containing bond_corpus_calibration_<timestamp>.json files.",
    )
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    result = assess_drift(reports_dir=args.reports_dir.resolve())
    print(f"[bond-corpus-drift] status={result.drift_status}")
    print(f"[bond-corpus-drift] markdown={result.report_md_path.as_posix()}")
    print(f"[bond-corpus-drift] json={result.report_json_path.as_posix()}")
    if result.alerts:
        print("[bond-corpus-drift] alerts:")
        for alert in result.alerts:
            print(f"- {alert}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
