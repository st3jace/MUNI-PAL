from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

RISK_DIMENSIONS = (
    "risk.technology",
    "risk.construction",
    "risk.market",
    "risk.regulatory",
    "risk.feedstock",
)


def _load_drift_module() -> ModuleType:
    script_path = Path(__file__).resolve().parents[2] / "scripts" / "assess_bond_corpus_drift.py"
    spec = importlib.util.spec_from_file_location("assess_bond_corpus_drift", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _calibration_payload(*, posture_score: float, conflict_rate_feedstock: float) -> dict[str, object]:
    dim_template = {
        "exposure_count": 30,
        "mitigant_count": 15,
        "distinct_documents": 5,
        "pair_complete": 1,
        "meets_cdr1_medium": 1,
        "meets_cdr1_high": 0,
        "meets_cdr4_source_diversity": 1,
        "conflict_rate_proxy": 0.50,
        "dimension_posture_score_proxy": 0.65,
    }
    rollup_all = {dim: dict(dim_template) for dim in RISK_DIMENSIONS}
    rollup_all["risk.feedstock"]["conflict_rate_proxy"] = conflict_rate_feedstock
    rollup_all["_meta"] = {
        "rows_considered": 120,
        "unmapped_category_count": 0,
        "overall_posture_score_proxy": posture_score,
        "conflict_rate_proxy_avg": 0.50,
        "conflict_rate_proxy_max": conflict_rate_feedstock,
    }

    return {
        "generated_at_utc": "2026-02-21T18:00:00+00:00",
        "recommendation": {"status": "go", "reasons": []},
        "sectors": {
            "waste": {
                "status": "ok",
                "cohort_assessment": {
                    "cdr3_status": {
                        "all": {
                            "dimensions_with_pair_complete": 5,
                            "dimensions_at_medium_plus": 5,
                        },
                        "revenue": {
                            "dimensions_with_pair_complete": 5,
                            "dimensions_at_medium_plus": 5,
                        },
                        "conduit": {
                            "dimensions_with_pair_complete": 5,
                            "dimensions_at_medium_plus": 5,
                        },
                        "private_activity": {
                            "dimensions_with_pair_complete": 5,
                            "dimensions_at_medium_plus": 5,
                        },
                    },
                    "dimension_rollup": {
                        "all": rollup_all,
                    },
                },
            }
        },
    }


def test_drift_flags_posture_and_conflict_thresholds(tmp_path: Path):
    drift = _load_drift_module()
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    previous = _calibration_payload(posture_score=0.82, conflict_rate_feedstock=0.10)
    current = _calibration_payload(posture_score=0.68, conflict_rate_feedstock=0.36)
    (reports_dir / "bond_corpus_calibration_20260221_180000.json").write_text(
        json.dumps(previous, indent=2),
        encoding="utf-8",
    )
    (reports_dir / "bond_corpus_calibration_20260221_190000.json").write_text(
        json.dumps(current, indent=2),
        encoding="utf-8",
    )

    result = drift.assess_drift(reports_dir=reports_dir)
    payload = json.loads(result.report_json_path.read_text(encoding="utf-8"))
    alerts_blob = "\n".join(payload["alerts"])
    assert "overall posture proxy regressed" in alerts_blob
    assert "conflict-rate proxy spiked" in alerts_blob
    assert payload["cdr5_metric_coverage"]["overall_posture_score_delta_gt_0_10"].startswith(
        "evaluated"
    )
    assert payload["cdr5_metric_coverage"]["conflict_rate_spike_gt_0_20"].startswith("evaluated")
