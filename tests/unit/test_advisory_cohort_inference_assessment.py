from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType


def _load_module() -> ModuleType:
    script_path = Path(__file__).resolve().parents[2] / "scripts" / "assess_advisory_cohort_inference.py"
    spec = importlib.util.spec_from_file_location("assess_advisory_cohort_inference", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write_healthcare_profile(path: Path) -> None:
    payload = {
        "obligor": {
            "canonical_name": "Chiricahua Community Health Centers Inc",
            "sub_sector": "fqhc",
        },
        "ida_loan": {
            "description": "Sierra Vista IDA Revolving Loan Fund first-stage financing",
            "lender": "Industrial Development Authority of the City of Sierra Vista",
            "borrower": "Chiricahua Community Health Centers, Inc.",
            "principal": 250000,
        },
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_waste_guide(path: Path) -> None:
    payload = {
        "project_name": "GSI Caldor UCS",
        "corpus_summary": {
            "sector": "waste management / environmental services",
        },
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_advisory_cohort_inference_assessment_recommends_go(tmp_path: Path):
    module = _load_module()

    healthcare_path = tmp_path / "cchci_obligor_profile.json"
    waste_path = tmp_path / "risk_implementation_guide.json"
    output_dir = tmp_path / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)

    _write_healthcare_profile(healthcare_path)
    _write_waste_guide(waste_path)

    result = module.assess_advisory_cohort_inference(
        output_dir=output_dir,
        healthcare_profile_path=healthcare_path,
        waste_guide_path=waste_path,
    )

    payload = json.loads(result.report_json_path.read_text(encoding="utf-8"))
    assert payload["recommendation"]["status"] == "go"
    assert payload["summary"]["scenarios_failed"] == 0
    assert payload["summary"]["covered_target_combo_count"] == 6
    assert payload["summary"]["target_combo_count"] == 6


def test_advisory_cohort_inference_assessment_flags_missing_sources(tmp_path: Path):
    module = _load_module()

    output_dir = tmp_path / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)

    result = module.assess_advisory_cohort_inference(
        output_dir=output_dir,
        healthcare_profile_path=tmp_path / "missing_healthcare.json",
        waste_guide_path=tmp_path / "missing_waste.json",
    )

    payload = json.loads(result.report_json_path.read_text(encoding="utf-8"))
    assert payload["recommendation"]["status"] == "no-go"
    assert len(payload["source_artifacts"]["missing"]) == 2
    assert result.recommendation == "no-go"
