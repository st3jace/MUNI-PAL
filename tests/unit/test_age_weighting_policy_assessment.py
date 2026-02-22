from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType


def _load_policy_module() -> ModuleType:
    script_path = Path(__file__).resolve().parents[2] / "scripts" / "assess_age_weighting_policy.py"
    spec = importlib.util.spec_from_file_location("assess_age_weighting_policy", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _calibration_payload(*, waste_stale_365_pct: float, healthcare_stale_365_pct: float) -> dict[str, object]:
    return {
        "generated_at_utc": "2026-02-21T19:00:00+00:00",
        "recommendation": {"status": "go"},
        "sectors": {
            "waste": {
                "status": "ok",
                "recency": {
                    "stale_ratio_180_pct": 45.0,
                    "stale_ratio_365_pct": waste_stale_365_pct,
                },
            },
            "healthcare": {
                "status": "ok",
                "recency": {
                    "stale_ratio_180_pct": 32.0,
                    "stale_ratio_365_pct": healthcare_stale_365_pct,
                },
            },
        },
    }


def test_age_weighting_policy_recommends_staged_enable_for_high_staleness(tmp_path: Path):
    module = _load_policy_module()
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    calibration_path = reports_dir / "bond_corpus_calibration_20260221_190000.json"
    calibration_path.write_text(
        json.dumps(_calibration_payload(waste_stale_365_pct=48.0, healthcare_stale_365_pct=22.0), indent=2),
        encoding="utf-8",
    )

    result = module.assess_age_weighting_policy(
        reports_dir=reports_dir,
        full_weight_days=365,
        candidate_max_penalties=(0.10, 0.15, 0.20),
    )

    payload = json.loads(result.report_json_path.read_text(encoding="utf-8"))
    assert payload["recommendation"]["status"] == "staged_enable"
    assert payload["recommendation"]["suggested_env"]["RISK_REPORTING_V2_AGE_WEIGHTING"] == "true"
    assert payload["recommendation"]["suggested_env"]["RISK_REPORTING_V2_AGE_WEIGHTING_MAX_PENALTY"] == "0.20"
    assert payload["summary"]["max_stale_ratio_365"] == 0.48


def test_age_weighting_policy_handles_missing_calibration(tmp_path: Path):
    module = _load_policy_module()
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    result = module.assess_age_weighting_policy(
        reports_dir=reports_dir,
        full_weight_days=365,
        candidate_max_penalties=(0.10, 0.15, 0.20),
    )

    payload = json.loads(result.report_json_path.read_text(encoding="utf-8"))
    assert payload["recommendation"]["status"] == "insufficient_data"
    assert payload["recommendation"]["suggested_env"]["RISK_REPORTING_V2_AGE_WEIGHTING"] == "false"
    assert result.status == "insufficient_data"
