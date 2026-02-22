import json
from pathlib import Path

from scripts.enforce_ops1003_regression_gates import evaluate_regression_gates


def _write_artifacts(
    reports_dir: Path,
    *,
    cdr1_met: bool,
    cdr4_met: bool,
    residual_risk_count: int,
    recommendation_status: str,
) -> None:
    calibration_payload = {"recommendation": {"status": "go"}}
    m5_payload = {
        "summary": {
            "cdr1_medium_coverage_met": cdr1_met,
            "cdr4_source_diversity_met": cdr4_met,
            "residual_risk_count": residual_risk_count,
        },
        "recommendation": {
            "status": recommendation_status,
        },
    }
    (reports_dir / "bond_corpus_calibration_20260222_160000.json").write_text(
        json.dumps(calibration_payload, indent=2),
        encoding="utf-8",
    )
    (reports_dir / "ops1003_m5_readiness_20260222_160000.json").write_text(
        json.dumps(m5_payload, indent=2),
        encoding="utf-8",
    )


def test_regression_gate_passes_when_requirements_met(tmp_path: Path) -> None:
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    _write_artifacts(
        reports_dir,
        cdr1_met=True,
        cdr4_met=True,
        residual_risk_count=0,
        recommendation_status="go",
    )

    result = evaluate_regression_gates(
        reports_dir=reports_dir,
        max_residual_risks=0,
        require_m5_go=True,
    )

    assert result.status == "pass"
    assert result.violations == []


def test_regression_gate_fails_when_cdr1_regresses(tmp_path: Path) -> None:
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    _write_artifacts(
        reports_dir,
        cdr1_met=False,
        cdr4_met=True,
        residual_risk_count=0,
        recommendation_status="go",
    )

    result = evaluate_regression_gates(
        reports_dir=reports_dir,
        max_residual_risks=0,
        require_m5_go=True,
    )

    assert result.status == "fail"
    assert any("CDR-1" in violation for violation in result.violations)


def test_regression_gate_fails_when_residual_risks_exceed_threshold(tmp_path: Path) -> None:
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    _write_artifacts(
        reports_dir,
        cdr1_met=True,
        cdr4_met=True,
        residual_risk_count=1,
        recommendation_status="go",
    )

    result = evaluate_regression_gates(
        reports_dir=reports_dir,
        max_residual_risks=0,
        require_m5_go=True,
    )

    assert result.status == "fail"
    assert any("residual risk count" in violation for violation in result.violations)


def test_regression_gate_fails_when_m5_artifact_missing(tmp_path: Path) -> None:
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    result = evaluate_regression_gates(
        reports_dir=reports_dir,
        max_residual_risks=0,
        require_m5_go=True,
    )

    assert result.status == "fail"
    assert any("Missing OPS-1003 M5 readiness artifact" in violation for violation in result.violations)
