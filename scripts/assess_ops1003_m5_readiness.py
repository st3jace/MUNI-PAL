"""
Assess OPS-1003 M5 production-grade readiness from latest Phase 10 artifacts.

Usage:
    python scripts/assess_ops1003_m5_readiness.py
    python scripts/assess_ops1003_m5_readiness.py --reports-dir reports/phase10_postlaunch
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

REQUIRED_ARTIFACT_PATTERNS: dict[str, str] = {
    "calibration": "bond_corpus_calibration_*.json",
    "advisory_cohort_inference": "advisory_cohort_inference_*.json",
    "advisory_package_smoke": "advisory_package_smoke_*.json",
    "age_weighting_policy": "age_weighting_policy_*.json",
    "bond_corpus_drift": "bond_corpus_drift_*.json",
    "bond_corpus_alert_routing": "bond_corpus_alert_routing_*.json",
}


@dataclass
class AssessmentResult:
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


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _latest_report(*, reports_dir: Path, pattern: str) -> Path | None:
    matches = sorted(reports_dir.glob(pattern))
    if not matches:
        return None
    return matches[-1]


def _cohort_assessment_payload(sector_payload: dict[str, Any]) -> dict[str, Any]:
    cohort_assessment = sector_payload.get("cohort_assessment", {})
    if isinstance(cohort_assessment, dict):
        return cohort_assessment
    return {}


def _rollup_all(sector_payload: dict[str, Any]) -> dict[str, Any]:
    cohort_assessment = _cohort_assessment_payload(sector_payload)
    dimension_rollup = cohort_assessment.get("dimension_rollup", {})
    if isinstance(dimension_rollup, dict):
        all_rollup = dimension_rollup.get("all", {})
        if isinstance(all_rollup, dict):
            return all_rollup
    return {}


def _cdr3_all(sector_payload: dict[str, Any]) -> dict[str, Any]:
    cohort_assessment = _cohort_assessment_payload(sector_payload)
    cdr3_status = cohort_assessment.get("cdr3_status", {})
    if isinstance(cdr3_status, dict):
        all_status = cdr3_status.get("all", {})
        if isinstance(all_status, dict):
            return all_status
    return {}


def _recommendation_from_findings(
    *,
    blockers: list[str],
    residual_risks: list[str],
) -> tuple[str, list[str]]:
    if blockers:
        return "no-go", blockers
    if residual_risks:
        return "go", [
            "No blocking gates detected.",
            f"Residual risks recorded: {len(residual_risks)}.",
        ]
    return "go", ["No blocking gates or residual risks detected."]


def _write_markdown(path: Path, payload: dict[str, Any]) -> None:
    recommendation = payload["recommendation"]
    summary = payload["summary"]
    lines = [
        "# OPS-1003 M5 Production-Grade Readiness",
        "",
        f"- Generated (UTC): `{payload['generated_at_utc']}`",
        f"- Recommendation status: `{recommendation['status']}`",
        "",
        "## Source Artifacts",
        "",
    ]

    for artifact_name, artifact_path in payload["source_artifacts"].items():
        lines.append(f"- {artifact_name}: `{artifact_path}`")

    lines.extend(
        [
            "",
            "## Gate Summary",
            "",
            f"- Calibration recommendation: `{summary['calibration_recommendation']}`",
            f"- CDR-3 all-cohort pair completeness met: `{summary['cdr3_all_pair_complete_met']}`",
            f"- CDR-1 medium coverage met: `{summary['cdr1_medium_coverage_met']}`",
            f"- CDR-4 source diversity met: `{summary['cdr4_source_diversity_met']}`",
            f"- Advisory cohort inference recommendation: `{summary['advisory_cohort_recommendation']}`",
            f"- Advisory package smoke recommendation: `{summary['advisory_package_smoke_recommendation']}`",
            f"- Age-weighting policy recommendation: `{summary['age_weighting_policy_recommendation']}`",
            f"- Drift status: `{summary['drift_status']}`",
            f"- Drift recommendation current: `{summary['drift_recommendation_current']}`",
            f"- Alert routing highest severity: `{summary['alert_routing_highest_severity']}`",
            f"- Alert routing critical count: `{summary['alert_routing_critical_count']}`",
            "",
            "## Sector CDR Snapshot",
            "",
            "| Sector | CDR-3 all pair complete | CDR-1 medium hits | CDR-4 source-diversity hits |",
            "|---|---:|---:|---:|",
        ]
    )

    for sector_name, sector in payload["sector_cdr_snapshot"].items():
        lines.append(
            f"| {sector_name} | {sector['cdr3_all_pair_complete']} | "
            f"{sector['cdr1_medium_hits']} | {sector['cdr4_source_diversity_hits']} |"
        )

    lines.extend(["", "## Blockers", ""])
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


def assess_ops1003_m5_readiness(*, reports_dir: Path) -> AssessmentResult:
    reports_dir.mkdir(parents=True, exist_ok=True)
    stamp = _timestamp()
    output_json = reports_dir / f"ops1003_m5_readiness_{stamp}.json"
    output_md = reports_dir / f"ops1003_m5_readiness_{stamp}.md"

    source_artifacts: dict[str, str | None] = {}
    missing_artifacts: list[str] = []
    loaded_payloads: dict[str, dict[str, Any]] = {}

    for artifact_name, pattern in REQUIRED_ARTIFACT_PATTERNS.items():
        latest = _latest_report(reports_dir=reports_dir, pattern=pattern)
        source_artifacts[artifact_name] = latest.name if latest is not None else None
        if latest is None:
            missing_artifacts.append(artifact_name)
            continue
        loaded_payloads[artifact_name] = _load_json(latest)

    blockers: list[str] = []
    residual_risks: list[str] = []

    if missing_artifacts:
        for artifact_name in missing_artifacts:
            blockers.append(f"Missing required artifact: {artifact_name}.")

    calibration_payload = loaded_payloads.get("calibration", {})
    calibration_recommendation = (
        str(calibration_payload.get("recommendation", {}).get("status", "unknown")).strip().lower()
    )
    if calibration_recommendation != "go":
        blockers.append(
            f"Calibration recommendation is `{calibration_recommendation}` (expected `go`)."
        )

    sector_cdr_snapshot: dict[str, dict[str, int]] = {}
    cdr3_all_pair_complete_met = True
    cdr1_medium_coverage_met = True
    cdr4_source_diversity_met = True
    sectors_evaluated = 0
    for sector_name, sector_payload in calibration_payload.get("sectors", {}).items():
        if not isinstance(sector_payload, dict):
            continue
        if str(sector_payload.get("status", "unknown")).strip().lower() != "ok":
            continue
        sectors_evaluated += 1
        cdr3_all = _cdr3_all(sector_payload)
        pair_complete = int(cdr3_all.get("dimensions_with_pair_complete", 0))
        rollup_all = _rollup_all(sector_payload)
        cdr1_hits = 0
        cdr4_hits = 0
        for dimension in RISK_DIMENSIONS:
            entry = rollup_all.get(dimension, {}) if isinstance(rollup_all, dict) else {}
            if isinstance(entry, dict):
                cdr1_hits += int(entry.get("meets_cdr1_medium", 0))
                cdr4_hits += int(entry.get("meets_cdr4_source_diversity", 0))
        sector_cdr_snapshot[sector_name] = {
            "cdr3_all_pair_complete": pair_complete,
            "cdr1_medium_hits": cdr1_hits,
            "cdr4_source_diversity_hits": cdr4_hits,
        }
        if pair_complete < len(RISK_DIMENSIONS):
            cdr3_all_pair_complete_met = False
        if cdr1_hits < len(RISK_DIMENSIONS):
            cdr1_medium_coverage_met = False
        if cdr4_hits < len(RISK_DIMENSIONS):
            cdr4_source_diversity_met = False

    if sectors_evaluated == 0:
        cdr3_all_pair_complete_met = False
        cdr1_medium_coverage_met = False
        cdr4_source_diversity_met = False
        blockers.append("No calibration sectors with status `ok` were found.")

    if not cdr3_all_pair_complete_met:
        blockers.append("CDR-3 all-cohort pair completeness is not met across sectors.")
    if not cdr1_medium_coverage_met:
        residual_risks.append(
            "CDR-1 remains partial: one or more sectors have <5/5 dimensions at medium sample coverage."
        )
    if not cdr4_source_diversity_met:
        residual_risks.append(
            "CDR-4 remains partial: one or more sectors have <5/5 dimensions with source diversity."
        )

    advisory_cohort_payload = loaded_payloads.get("advisory_cohort_inference", {})
    advisory_cohort_recommendation = (
        str(advisory_cohort_payload.get("recommendation", {}).get("status", "unknown"))
        .strip()
        .lower()
    )
    if advisory_cohort_recommendation != "go":
        blockers.append(
            f"Advisory cohort inference recommendation is `{advisory_cohort_recommendation}` (expected `go`)."
        )

    advisory_smoke_payload = loaded_payloads.get("advisory_package_smoke", {})
    advisory_package_smoke_recommendation = (
        str(advisory_smoke_payload.get("recommendation", {}).get("status", "unknown"))
        .strip()
        .lower()
    )
    if advisory_package_smoke_recommendation != "go":
        blockers.append(
            "Advisory package smoke recommendation is "
            f"`{advisory_package_smoke_recommendation}` (expected `go`)."
        )

    age_weighting_payload = loaded_payloads.get("age_weighting_policy", {})
    age_weighting_recommendation = (
        str(age_weighting_payload.get("recommendation", {}).get("status", "unknown"))
        .strip()
        .lower()
    )
    age_weighting_reasons = [
        str(reason).strip().lower()
        for reason in age_weighting_payload.get("recommendation", {}).get("reasons", [])
        if str(reason).strip()
    ]
    if age_weighting_recommendation == "insufficient_data":
        blockers.append("Age-weighting policy assessment is `insufficient_data`.")
    elif age_weighting_recommendation == "hold":
        hold_is_healthy_baseline = any(
            "recency staleness is limited" in reason
            for reason in age_weighting_reasons
        )
        if not hold_is_healthy_baseline:
            residual_risks.append(
                "CDR-2 remains staged-off (`hold`); continue weekly reassessment before enablement."
            )
    elif age_weighting_recommendation == "staged_enable":
        residual_risks.append(
            "CDR-2 recommends `staged_enable`; controlled rollout + monitoring is still required."
        )

    drift_payload = loaded_payloads.get("bond_corpus_drift", {})
    drift_status = str(drift_payload.get("drift_status", "unknown")).strip().lower()
    drift_recommendation_current = (
        str(drift_payload.get("recommendation_transition", {}).get("current", "unknown"))
        .strip()
        .lower()
    )
    if drift_recommendation_current != "go":
        blockers.append(
            "Current drift recommendation transition target is "
            f"`{drift_recommendation_current}` (expected `go`)."
        )
    elif drift_status not in {"stable", "improved"}:
        residual_risks.append(
            f"Drift status is `{drift_status}`; continue week-over-week monitoring."
        )

    alert_routing_payload = loaded_payloads.get("bond_corpus_alert_routing", {})
    alert_summary = alert_routing_payload.get("summary", {})
    alert_routing_highest_severity = (
        str(alert_summary.get("highest_severity", "unknown")).strip().lower()
    )
    alert_routing_critical_count = int(alert_summary.get("counts_by_severity", {}).get("critical", 0))
    requires_incident = bool(alert_summary.get("requires_incident", False))
    if requires_incident or alert_routing_critical_count > 0:
        blockers.append(
            "Alert routing indicates critical severity and incident requirement."
        )
    elif alert_routing_highest_severity == "warning":
        if drift_status in {"stable", "improved"}:
            residual_risks.append(
                "Alert routing includes warning-level events; track follow-up in weekly ops."
            )

    recommendation_status, recommendation_notes = _recommendation_from_findings(
        blockers=blockers,
        residual_risks=residual_risks,
    )

    payload = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "source_artifacts": source_artifacts,
        "summary": {
            "sectors_evaluated": sectors_evaluated,
            "calibration_recommendation": calibration_recommendation,
            "cdr3_all_pair_complete_met": cdr3_all_pair_complete_met,
            "cdr1_medium_coverage_met": cdr1_medium_coverage_met,
            "cdr4_source_diversity_met": cdr4_source_diversity_met,
            "advisory_cohort_recommendation": advisory_cohort_recommendation,
            "advisory_package_smoke_recommendation": advisory_package_smoke_recommendation,
            "age_weighting_policy_recommendation": age_weighting_recommendation,
            "drift_status": drift_status,
            "drift_recommendation_current": drift_recommendation_current,
            "alert_routing_highest_severity": alert_routing_highest_severity,
            "alert_routing_critical_count": alert_routing_critical_count,
            "requires_incident": requires_incident,
            "missing_artifact_count": len(missing_artifacts),
            "blocker_count": len(blockers),
            "residual_risk_count": len(residual_risks),
        },
        "sector_cdr_snapshot": sector_cdr_snapshot,
        "recommendation": {
            "status": recommendation_status,
            "blockers": blockers,
            "residual_risks": residual_risks,
            "notes": recommendation_notes,
        },
    }

    output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    _write_markdown(output_md, payload)

    return AssessmentResult(
        report_json_path=output_json,
        report_md_path=output_md,
        status=recommendation_status,
        blockers=blockers,
        residual_risks=residual_risks,
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Assess OPS-1003 M5 readiness from latest Phase 10 evidence artifacts.",
    )
    parser.add_argument(
        "--reports-dir",
        type=Path,
        default=_default_reports_dir(),
        help="Directory containing phase10 postlaunch report artifacts.",
    )
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    result = assess_ops1003_m5_readiness(
        reports_dir=args.reports_dir.resolve(),
    )
    print(f"[ops1003-m5-readiness] status={result.status}")
    print(f"[ops1003-m5-readiness] markdown={result.report_md_path.as_posix()}")
    print(f"[ops1003-m5-readiness] json={result.report_json_path.as_posix()}")
    if result.blockers:
        print("[ops1003-m5-readiness] blockers:")
        for blocker in result.blockers:
            print(f"- {blocker}")
    if result.residual_risks:
        print("[ops1003-m5-readiness] residual_risks:")
        for risk in result.residual_risks:
            print(f"- {risk}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
