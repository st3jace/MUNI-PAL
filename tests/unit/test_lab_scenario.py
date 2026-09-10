"""Fence: scenario shape, base-core == demo-core (F10), one-knob variants (BUILD-SPEC 3, 6)."""

from __future__ import annotations

import copy
import json

import pytest

from tests import lab_support

LAB = lab_support.LAB_ROOT
REPO = lab_support.REPO_ROOT
BASE = "SYN-HSG-AZ-2025-LAB01"
VARIANTS = ("SYN-HSG-AZ-2025-LAB02", "SYN-HSG-AZ-2025-LAB03")


def _scenario_path(deal_id: str):
    return LAB / "scenarios" / f"{deal_id}.synthetic.json"


def test_lab_scenario_shape_and_base_equals_demo_core() -> None:
    lab_support.import_labkit()
    from labkit import law, scenario

    loaded = {deal_id: scenario.load(_scenario_path(deal_id)) for deal_id in (BASE, *VARIANTS)}
    for deal_id, sc in loaded.items():
        assert sc.deal_id == deal_id
        assert sc.data["mode"] == "synthetic"
        assert sc.deal_id != law.DEMO_DEAL_ID
        assert law.LAB_DEAL_ID_RE.match(sc.deal_id)
        assert set(sc.data["stations"]) <= set(law.BONDI_STATIONS)
        assert sc.deal_v0_schema_note in ("live", scenario.DEAL_V0_ABSENT)
        assert sc.contract.required and "stations" in sc.contract.required
        assert law.ISO_DATE_RE.match(sc.asof)
        assert sc.closing is None or law.ISO_DATE_RE.match(sc.closing)
        assert sc.lab["review_plan"]["reviewer_id"] == law.REVIEWER_ID

    base = loaded[BASE].data

    def rejected(mutate, label: str) -> None:
        data = copy.deepcopy(base)
        mutate(data)
        with pytest.raises(scenario.ScenarioError, match=r".+"):
            scenario.validate(data)
        _ = label

    rejected(lambda d: d.__setitem__("mode", "calibration"), "calibration mode")
    rejected(lambda d: d["parties"][0].__setitem__("name", "Mesa Verde Capital Partners LLC"), "untabled party")
    rejected(lambda d: d["constraints"][0].__setitem__("status", "ok"), "constraint status ok")
    rejected(lambda d: d["instrument"].__setitem__("dated", "2025-13-01"), "impossible date")
    rejected(lambda d: d.__delitem__("stations"), "stations missing")
    rejected(lambda d: d.__setitem__("deal_id", law.DEMO_DEAL_ID), "demo id reused")

    demo = json.loads(scenario.DEMO_SCENARIO_PATH.read_text(encoding="utf-8"))
    assert "stations" not in demo, "F10 closed: the demo scenario now carries stations; revisit the base-core rule"
    assert demo["deal_id"] == law.DEMO_DEAL_ID
    assert scenario.base_core_vs_demo(base) == []
    assert all(sc.deal_id != demo["deal_id"] for sc in loaded.values())


def test_lab_variants_flip_exactly_one_knob() -> None:
    lab_support.import_labkit()
    from labkit import scenario

    base = scenario.load(_scenario_path(BASE))
    assert base.derived_from is None and base.knob_delta == {}
    for deal_id in VARIANTS:
        variant = scenario.load(_scenario_path(deal_id))
        assert variant.derived_from == BASE
        raw = json.loads(_scenario_path(deal_id).read_text(encoding="utf-8"))
        assert set(raw) == {"deal_id", "derived_from", "mode", "knob_delta"}
        knob_keys = sorted(variant.knob_delta)
        assert knob_keys, f"{deal_id}: empty knob_delta"
        touched = sorted(scenario.diff_paths(variant.data, base.data))
        assert touched == knob_keys, f"{deal_id}: diff {touched} != knob_delta keys {knob_keys}"
        knobs = {k for k in variant.knob_delta if k.startswith("lab.knobs.")}
        assert len(knobs) == 1, f"{deal_id}: exactly one lab knob per variant, got {sorted(knobs)}"
        assert variant.data["lab"]["expected_report"] == f"expected/{deal_id}/run-report.expected.json"
    lab02 = scenario.load(_scenario_path(VARIANTS[0]))
    assert lab02.data["lab"]["knobs"]["late_afs"] is True
    assert lab02.data["disclosure"]["afs"][0]["posted"] is None
    assert lab02.intake_docs == base.intake_docs
    lab03 = scenario.load(_scenario_path(VARIANTS[1]))
    assert lab03.data["lab"]["knobs"]["drop_required_artifact"] == "site_control_permits"
    assert lab03.dropped_artifacts == ["site_control_permits"]
    assert len(lab03.dropped_intake_paths) == 7
    assert lab03.data["disclosure"] == base.data["disclosure"]
