"""
Enforce OPS-1003 regression gates from latest Phase 10 artifacts.

Usage:
    python scripts/enforce_ops1003_regression_gates.py
    python scripts/enforce_ops1003_regression_gates.py --reports-dir reports/phase10_postlaunch
    python scripts/enforce_ops1003_regression_gates.py --max-residual-risks 0
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

M5_READINESS_PATTERN = "ops1003_m5_readiness_*.json"
CALIBRATION_PATTERN = "bond_corpus_calibration_*.json"


@dataclass
class RegressionGateResult:
    status: str
    violations: list[str]
    latest_m5_readiness: str | None
    latest_calibration: str | None
    cdr1_medium_coverage_met: bool
    cdr4_source_diversity_met: bool
    residual_risk_count: int
    m5_recommendation_status: str


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _default_reports_dir() -> Path:
    return _repo_root() / "reports" / "phase10_postlaunch"


def _latest_report(*, reports_dir: Path, pattern: str) -> Path | None:
    matches = sorted(reports_dir.glob(pattern))
    if not matches:
        return None
    return matches[-1]


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def evaluate_regression_gates(
    *,
    reports_dir: Path,
    max_residual_risks: int = 0,
    require_m5_go: bool = True,
) -> RegressionGateResult:
    violations: list[str] = []

    latest_m5 = _latest_report(reports_dir=reports_dir, pattern=M5_READINESS_PATTERN)
    latest_calibration = _latest_report(reports_dir=reports_dir, pattern=CALIBRATION_PATTERN)

    if latest_m5 is None:
        violations.append("Missing OPS-1003 M5 readiness artifact.")
        return RegressionGateResult(
            status="fail",
            violations=violations,
            latest_m5_readiness=None,
            latest_calibration=latest_calibration.name if latest_calibration else None,
            cdr1_medium_coverage_met=False,
            cdr4_source_diversity_met=False,
            residual_risk_count=max_residual_risks + 1,
            m5_recommendation_status="missing",
        )

    m5_payload = _load_json(latest_m5)
    summary = m5_payload.get("summary", {})
    recommendation = m5_payload.get("recommendation", {})

    cdr1_medium_coverage_met = bool(summary.get("cdr1_medium_coverage_met", False))
    cdr4_source_diversity_met = bool(summary.get("cdr4_source_diversity_met", False))
    residual_risk_count = int(summary.get("residual_risk_count", 0))
    m5_recommendation_status = str(recommendation.get("status", "unknown")).strip().lower()

    if not cdr1_medium_coverage_met:
        violations.append("Regression: CDR-1 medium coverage is not met.")
    if not cdr4_source_diversity_met:
        violations.append("Regression: CDR-4 source diversity is not met.")
    if residual_risk_count > max_residual_risks:
        violations.append(
            "Regression: residual risk count "
            f"{residual_risk_count} exceeds threshold {max_residual_risks}."
        )
    if require_m5_go and m5_recommendation_status != "go":
        violations.append(
            "Regression: OPS-1003 M5 recommendation is "
            f"`{m5_recommendation_status}` (expected `go`)."
        )

    return RegressionGateResult(
        status="pass" if not violations else "fail",
        violations=violations,
        latest_m5_readiness=latest_m5.name,
        latest_calibration=latest_calibration.name if latest_calibration else None,
        cdr1_medium_coverage_met=cdr1_medium_coverage_met,
        cdr4_source_diversity_met=cdr4_source_diversity_met,
        residual_risk_count=residual_risk_count,
        m5_recommendation_status=m5_recommendation_status,
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Enforce OPS-1003 regression gates from latest readiness artifacts.",
    )
    parser.add_argument(
        "--reports-dir",
        type=Path,
        default=_default_reports_dir(),
        help="Directory containing Phase 10 postlaunch reports.",
    )
    parser.add_argument(
        "--max-residual-risks",
        type=int,
        default=0,
        help="Maximum allowed residual risk count before gate failure.",
    )
    parser.add_argument(
        "--require-m5-go",
        action="store_true",
        default=False,
        help="Fail if latest M5 recommendation status is not `go`.",
    )
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    result = evaluate_regression_gates(
        reports_dir=args.reports_dir.resolve(),
        max_residual_risks=args.max_residual_risks,
        require_m5_go=args.require_m5_go,
    )

    print(f"[ops1003-regression-gate] status={result.status}")
    print(f"[ops1003-regression-gate] latest_m5_readiness={result.latest_m5_readiness}")
    print(f"[ops1003-regression-gate] latest_calibration={result.latest_calibration}")
    print(
        "[ops1003-regression-gate] cdr1_medium_coverage_met="
        f"{result.cdr1_medium_coverage_met}"
    )
    print(
        "[ops1003-regression-gate] cdr4_source_diversity_met="
        f"{result.cdr4_source_diversity_met}"
    )
    print(f"[ops1003-regression-gate] residual_risk_count={result.residual_risk_count}")
    print(
        "[ops1003-regression-gate] m5_recommendation_status="
        f"{result.m5_recommendation_status}"
    )
    if result.violations:
        print("[ops1003-regression-gate] violations:")
        for violation in result.violations:
            print(f"- {violation}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
