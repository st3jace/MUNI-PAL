from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType


def _load_module() -> ModuleType:
    script_path = Path(__file__).resolve().parents[2] / "scripts" / "assess_advisory_package_smoke.py"
    spec = importlib.util.spec_from_file_location("assess_advisory_package_smoke", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_recommendation_is_go_when_required_assertions_pass():
    module = _load_module()

    assertions = {
        "project_id_resolved": True,
        "internal_generate_ok": True,
        "internal_report_fetch_ok": True,
        "external_generate_ok": True,
        "external_package_fetch_ok": True,
        "external_validate_ok": True,
    }
    recommendation, reasons = module._recommendation_from_assertions(assertions)  # noqa: SLF001
    assert recommendation == "go"
    assert reasons == []


def test_recommendation_is_no_go_when_required_assertion_fails():
    module = _load_module()

    assertions = {
        "project_id_resolved": True,
        "internal_generate_ok": True,
        "internal_report_fetch_ok": False,
        "external_generate_ok": True,
        "external_package_fetch_ok": True,
        "external_validate_ok": True,
    }
    recommendation, reasons = module._recommendation_from_assertions(assertions)  # noqa: SLF001
    assert recommendation == "no-go"
    assert reasons == ["internal_report_fetch_ok failed."]
