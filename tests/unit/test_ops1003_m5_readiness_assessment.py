import json
from pathlib import Path

from scripts.assess_ops1003_m5_readiness import (
    _recommendation_from_findings,
    assess_ops1003_m5_readiness,
)


def test_recommendation_no_go_when_blockers_present() -> None:
    status, notes = _recommendation_from_findings(
        blockers=["Calibration recommendation is `no-go`."],
        residual_risks=["CDR-1 remains partial."],
    )

    assert status == "no-go"
    assert notes == ["Calibration recommendation is `no-go`."]


def test_recommendation_go_with_residual_risks() -> None:
    status, notes = _recommendation_from_findings(
        blockers=[],
        residual_risks=["CDR-4 remains partial."],
    )

    assert status == "go"
    assert notes == [
        "No blocking gates detected.",
        "Residual risks recorded: 1.",
    ]


def test_recommendation_go_without_findings() -> None:
    status, notes = _recommendation_from_findings(
        blockers=[],
        residual_risks=[],
    )

    assert status == "go"
    assert notes == ["No blocking gates or residual risks detected."]


def _write_minimum_reports(
    reports_dir: Path,
    *,
    age_weighting_status: str,
    age_weighting_reasons: list[str],
    drift_status: str = "stable",
    drift_current_recommendation: str = "go",
    alert_highest_severity: str = "none",
) -> None:
    calibration_payload = {
        "recommendation": {"status": "go"},
        "sectors": {
            "waste": {
                "status": "ok",
                "cohort_assessment": {
                    "cdr3_status": {
                        "all": {
                            "dimensions_with_pair_complete": 5,
                        }
                    },
                    "dimension_rollup": {
                        "all": {
                            "risk.technology": {"meets_cdr1_medium": 1, "meets_cdr4_source_diversity": 1},
                            "risk.construction": {"meets_cdr1_medium": 1, "meets_cdr4_source_diversity": 1},
                            "risk.market": {"meets_cdr1_medium": 1, "meets_cdr4_source_diversity": 1},
                            "risk.regulatory": {"meets_cdr1_medium": 1, "meets_cdr4_source_diversity": 1},
                            "risk.feedstock": {"meets_cdr1_medium": 1, "meets_cdr4_source_diversity": 1},
                        }
                    },
                },
            }
        },
    }
    advisory_cohort_payload = {"recommendation": {"status": "go"}}
    advisory_smoke_payload = {"recommendation": {"status": "go"}}
    age_weighting_payload = {
        "recommendation": {
            "status": age_weighting_status,
            "reasons": age_weighting_reasons,
        }
    }
    drift_payload = {
        "drift_status": drift_status,
        "recommendation_transition": {"current": drift_current_recommendation},
    }
    alert_routing_payload = {
        "summary": {
            "highest_severity": alert_highest_severity,
            "counts_by_severity": {"critical": 0},
            "requires_incident": False,
        }
    }

    (reports_dir / "bond_corpus_calibration_20260222_180000.json").write_text(
        json.dumps(calibration_payload, indent=2),
        encoding="utf-8",
    )
    (reports_dir / "advisory_cohort_inference_20260222_180000.json").write_text(
        json.dumps(advisory_cohort_payload, indent=2),
        encoding="utf-8",
    )
    (reports_dir / "advisory_package_smoke_20260222_180000.json").write_text(
        json.dumps(advisory_smoke_payload, indent=2),
        encoding="utf-8",
    )
    (reports_dir / "age_weighting_policy_20260222_180000.json").write_text(
        json.dumps(age_weighting_payload, indent=2),
        encoding="utf-8",
    )
    (reports_dir / "bond_corpus_drift_20260222_180000.json").write_text(
        json.dumps(drift_payload, indent=2),
        encoding="utf-8",
    )
    (reports_dir / "bond_corpus_alert_routing_20260222_180000.json").write_text(
        json.dumps(alert_routing_payload, indent=2),
        encoding="utf-8",
    )


def test_age_weighting_hold_with_healthy_recency_is_not_residual_risk(tmp_path: Path) -> None:
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    _write_minimum_reports(
        reports_dir,
        age_weighting_status="hold",
        age_weighting_reasons=[
            "Recency staleness is limited; keep age-weighting disabled until next data refresh.",
        ],
    )

    result = assess_ops1003_m5_readiness(reports_dir=reports_dir)
    payload = json.loads(result.report_json_path.read_text(encoding="utf-8"))
    residuals = payload["recommendation"]["residual_risks"]

    assert result.status == "go"
    assert all("CDR-2" not in risk for risk in residuals)


def test_age_weighting_hold_without_healthy_reason_stays_residual_risk(tmp_path: Path) -> None:
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    _write_minimum_reports(
        reports_dir,
        age_weighting_status="hold",
        age_weighting_reasons=[
            "Pending governance review before staged enablement.",
        ],
    )

    result = assess_ops1003_m5_readiness(reports_dir=reports_dir)
    payload = json.loads(result.report_json_path.read_text(encoding="utf-8"))
    residuals = payload["recommendation"]["residual_risks"]

    assert result.status == "go"
    assert any("CDR-2" in risk for risk in residuals)


def test_drift_changed_with_go_transition_stays_go_with_single_residual(tmp_path: Path) -> None:
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    _write_minimum_reports(
        reports_dir,
        age_weighting_status="hold",
        age_weighting_reasons=[
            "Recency staleness is limited; keep age-weighting disabled until next data refresh.",
        ],
        drift_status="changed",
        drift_current_recommendation="go",
        alert_highest_severity="warning",
    )

    result = assess_ops1003_m5_readiness(reports_dir=reports_dir)
    payload = json.loads(result.report_json_path.read_text(encoding="utf-8"))
    residuals = payload["recommendation"]["residual_risks"]

    assert result.status == "go"
    assert len(residuals) == 1
    assert "Drift status is `changed`" in residuals[0]
