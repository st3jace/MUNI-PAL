"""
Assess CDR-2 age-weighting policy from latest bond corpus calibration output.

Usage:
    python scripts/assess_age_weighting_policy.py
    python scripts/assess_age_weighting_policy.py --reports-dir reports/phase10_postlaunch
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

DEFAULT_CANDIDATE_MAX_PENALTIES = (0.10, 0.15, 0.20)


@dataclass
class AssessmentResult:
    report_json_path: Path
    report_md_path: Path
    status: str
    reasons: list[str]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _default_reports_dir() -> Path:
    return _repo_root() / "reports" / "phase10_postlaunch"


def _timestamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%d_%H%M%S")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _latest_calibration_report(reports_dir: Path) -> Path | None:
    reports = sorted(reports_dir.glob("bond_corpus_calibration_*.json"))
    if not reports:
        return None
    return reports[-1]


def _safe_percent(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 0.0
    return round((numerator / denominator) * 100.0, 2)


def _write_markdown(path: Path, payload: dict[str, Any]) -> None:
    recommendation = payload["recommendation"]
    summary = payload["summary"]
    lines = [
        "# Age Weighting Policy Assessment",
        "",
        f"- Generated (UTC): `{payload['generated_at_utc']}`",
        f"- Source calibration report: `{payload['source_calibration_report']}`",
        f"- Recommendation status: `{recommendation['status']}`",
        "",
        "## Recency Summary",
        "",
        f"- Sectors evaluated: `{summary['sectors_evaluated']}`",
        f"- Max stale ratio (>365d): `{summary['max_stale_ratio_365']}`",
        f"- Avg stale ratio (>365d): `{summary['avg_stale_ratio_365']}`",
        "",
        "## Sector Recency",
        "",
        "| Sector | Stale Ratio >180d | Stale Ratio >365d |",
        "|---|---:|---:|",
    ]

    for sector, sector_payload in payload["sectors"].items():
        lines.append(
            f"| {sector} | {sector_payload['stale_ratio_180']} | {sector_payload['stale_ratio_365']} |"
        )

    lines.extend(
        [
            "",
            "## Candidate Penalty Simulation",
            "",
            "| Max Penalty | Avg Score Penalty | Avg Confidence Multiplier |",
            "|---:|---:|---:|",
        ]
    )
    for candidate in payload["candidate_analysis"]:
        lines.append(
            f"| {candidate['max_penalty']} | {candidate['avg_score_penalty']} | "
            f"{candidate['avg_confidence_multiplier']} |"
        )

    lines.extend(
        [
            "",
            "## Suggested Environment",
            "",
        ]
    )
    for key, value in recommendation["suggested_env"].items():
        lines.append(f"- `{key}={value}`")

    lines.extend(["", "## Recommendation Notes", ""])
    if recommendation["reasons"]:
        for reason in recommendation["reasons"]:
            lines.append(f"- {reason}")
    else:
        lines.append("- No blocking issues detected.")

    path.write_text("\n".join(lines), encoding="utf-8")


def assess_age_weighting_policy(
    *,
    reports_dir: Path,
    full_weight_days: int,
    candidate_max_penalties: tuple[float, ...],
) -> AssessmentResult:
    reports_dir.mkdir(parents=True, exist_ok=True)
    stamp = _timestamp()
    output_json = reports_dir / f"age_weighting_policy_{stamp}.json"
    output_md = reports_dir / f"age_weighting_policy_{stamp}.md"

    source_report = _latest_calibration_report(reports_dir)
    if source_report is None:
        payload = {
            "generated_at_utc": datetime.now(UTC).isoformat(),
            "source_calibration_report": None,
            "full_weight_days": full_weight_days,
            "candidate_max_penalties": list(candidate_max_penalties),
            "sectors": {},
            "candidate_analysis": [],
            "summary": {
                "sectors_evaluated": 0,
                "max_stale_ratio_365": 0.0,
                "avg_stale_ratio_365": 0.0,
            },
            "recommendation": {
                "status": "insufficient_data",
                "suggested_env": {
                    "RISK_REPORTING_V2_AGE_WEIGHTING": "false",
                    "RISK_REPORTING_V2_AGE_WEIGHTING_FULL_WEIGHT_DAYS": str(full_weight_days),
                    "RISK_REPORTING_V2_AGE_WEIGHTING_MAX_PENALTY": "0.15",
                },
                "reasons": ["No bond_corpus_calibration report found."],
            },
        }
        output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        _write_markdown(output_md, payload)
        return AssessmentResult(
            report_json_path=output_json,
            report_md_path=output_md,
            status="insufficient_data",
            reasons=payload["recommendation"]["reasons"],
        )

    calibration_payload = _load_json(source_report)
    sectors: dict[str, Any] = {}
    stale_ratios_365: list[float] = []
    for sector_name, sector_payload in calibration_payload.get("sectors", {}).items():
        if sector_payload.get("status") != "ok":
            continue
        recency = sector_payload.get("recency", {})
        stale_ratio_365_pct = float(recency.get("stale_ratio_365_pct", 0.0))
        stale_ratio_180_pct = float(recency.get("stale_ratio_180_pct", 0.0))
        stale_ratio_365 = round(stale_ratio_365_pct / 100.0, 4)
        stale_ratio_180 = round(stale_ratio_180_pct / 100.0, 4)
        stale_ratios_365.append(stale_ratio_365)
        sectors[sector_name] = {
            "stale_ratio_180": stale_ratio_180,
            "stale_ratio_365": stale_ratio_365,
        }

    sectors_evaluated = len(sectors)
    avg_stale_ratio_365 = round(sum(stale_ratios_365) / sectors_evaluated, 4) if sectors_evaluated else 0.0
    max_stale_ratio_365 = round(max(stale_ratios_365), 4) if stale_ratios_365 else 0.0

    candidate_analysis: list[dict[str, Any]] = []
    for candidate in candidate_max_penalties:
        penalties = [round(ratio * candidate, 4) for ratio in stale_ratios_365]
        avg_penalty = round(sum(penalties) / len(penalties), 4) if penalties else 0.0
        candidate_analysis.append(
            {
                "max_penalty": round(candidate, 4),
                "avg_score_penalty": avg_penalty,
                "avg_confidence_multiplier": round(1.0 - avg_penalty, 4),
            }
        )

    suggested_max_penalty = 0.10
    if max_stale_ratio_365 >= 0.35:
        suggested_max_penalty = 0.20
    elif max_stale_ratio_365 >= 0.15:
        suggested_max_penalty = 0.15

    should_enable = sectors_evaluated > 0 and (
        max_stale_ratio_365 >= 0.15 or avg_stale_ratio_365 >= 0.10
    )
    status = "staged_enable" if should_enable else "hold"
    reasons: list[str] = []
    if sectors_evaluated == 0:
        reasons.append("No sector recency data available in calibration payload.")
    if should_enable:
        reasons.append(
            "Recency staleness exceeds tuning threshold; staged age-weighting enablement is recommended."
        )
    else:
        reasons.append("Recency staleness is limited; keep age-weighting disabled until next data refresh.")
    reasons.append(
        "Suggested max penalty selected from observed stale ratio distribution across sectors."
    )

    payload = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "source_calibration_report": source_report.name,
        "full_weight_days": int(full_weight_days),
        "candidate_max_penalties": [round(value, 4) for value in candidate_max_penalties],
        "sectors": sectors,
        "candidate_analysis": candidate_analysis,
        "summary": {
            "sectors_evaluated": sectors_evaluated,
            "max_stale_ratio_365": max_stale_ratio_365,
            "avg_stale_ratio_365": avg_stale_ratio_365,
            "stale_ratio_spread_pct": _safe_percent(
                max_stale_ratio_365 - avg_stale_ratio_365,
                max_stale_ratio_365 if max_stale_ratio_365 > 0 else 1.0,
            ),
        },
        "recommendation": {
            "status": status,
            "suggested_env": {
                "RISK_REPORTING_V2_AGE_WEIGHTING": str(should_enable).lower(),
                "RISK_REPORTING_V2_AGE_WEIGHTING_FULL_WEIGHT_DAYS": str(int(full_weight_days)),
                "RISK_REPORTING_V2_AGE_WEIGHTING_MAX_PENALTY": f"{suggested_max_penalty:.2f}",
            },
            "reasons": reasons,
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
    parser = argparse.ArgumentParser(description="Assess CDR-2 age-weighting policy from calibration recency.")
    parser.add_argument(
        "--reports-dir",
        type=Path,
        default=_default_reports_dir(),
        help="Directory containing bond_corpus_calibration_<timestamp>.json files.",
    )
    parser.add_argument(
        "--full-weight-days",
        type=int,
        default=365,
        help="Reference full-weight horizon in days.",
    )
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    result = assess_age_weighting_policy(
        reports_dir=args.reports_dir.resolve(),
        full_weight_days=args.full_weight_days,
        candidate_max_penalties=DEFAULT_CANDIDATE_MAX_PENALTIES,
    )
    print(f"[age-weighting-policy] status={result.status}")
    print(f"[age-weighting-policy] markdown={result.report_md_path.as_posix()}")
    print(f"[age-weighting-policy] json={result.report_json_path.as_posix()}")
    if result.reasons:
        print("[age-weighting-policy] reasons:")
        for reason in result.reasons:
            print(f"- {reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
