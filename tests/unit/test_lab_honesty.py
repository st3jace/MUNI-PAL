"""Fence: four-valued honesty by construction (brief rule 4; BUILD-SPEC 6 rows 18-20).

The two client pilot gates cannot be constructed as anything but `not_applicable`; every
status is a Literal; lab statements reject the forbidden words; the smoke gate follows a
table; the hold knob short-circuits without inventing a close.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from tests import lab_support

LAB = lab_support.LAB_ROOT
DEAL_IDS = ("SYN-HSG-AZ-2025-LAB01", "SYN-HSG-AZ-2025-LAB02", "SYN-HSG-AZ-2025-LAB03")
HOLD_EVENTS = ("closing", "g32_os_filed", "cda_executed", "8038_filed", "afs_posted_fy2025")
_HEX64 = "0" * 64


def _minimal_report_kwargs(labkit) -> dict:
    types = labkit.types
    law = labkit.law
    return {
        "run_id": "SYN-HSG-AZ-2025-LAB01__2026-09-10__deadbeef",
        "scenario_id": "SYN-HSG-AZ-2025-LAB01",
        "scenario_sha256": _HEX64,
        "seed": 20250626,
        "asof": "2026-09-10",
        "python": "3.11.15",
        "pins": dict.fromkeys(law.PIN_KEYS, "absent"),
        "pilot_gates": types.PilotGates(pilot_smoke_test_green="pass"),
    }


def test_lab_ma_gate_structural_and_four_valued() -> None:
    labkit = lab_support.import_labkit()
    types, law = labkit.types, labkit.law

    gates = types.PilotGates(pilot_smoke_test_green="fail")
    assert gates.registered_ma_confirmed == "not_applicable"
    assert gates.engagement_scope_signed == "not_applicable"
    assert gates.registered_ma_confirmed_reason == law.CLIENT_GATE_REASON == "internal lab; no client"
    for gate in ("registered_ma_confirmed", "engagement_scope_signed"):
        for value in ("pass", "fail", "unknown", "satisfied", True):
            with pytest.raises(ValidationError):
                types.PilotGates(pilot_smoke_test_green="pass", **{gate: value})
    with pytest.raises(ValidationError):
        types.PilotGates(pilot_smoke_test_green="unknown")
    with pytest.raises(ValidationError):
        types.PilotGates(pilot_smoke_test_green="pass", registered_ma_confirmed_reason="  ")

    stage_fields = {"id": "S01", "station": "2_conduit", "bfms_stage": "WP1", "deal_phase": "engagement", "pilot_stage": "intake", "assertion": "x"}
    with pytest.raises(ValidationError):
        types.StageResult(status="ok", **stage_fields)
    with pytest.raises(ValidationError):
        types.StageResult(status="unknown", **stage_fields)  # unknown needs a reason
    with pytest.raises(ValidationError):
        types.StageResult(status="pass", sub_assertions=[types.SubAssertion(key="k", status="fail")], **stage_fields)
    with pytest.raises(ValidationError):
        types.SubAssertion(key="k", status="not_applicable")
    with pytest.raises(ValidationError):
        types.ConformanceRow(event="closing", station="5_buyers", log_status="fired", date="2025-06-26", bfms_object="phase", expected_state="completed", observed_state="completed", status="ok")
    with pytest.raises(ValidationError):
        types.ConformanceRow(event="closing", station="5_buyers", log_status="fired", date="2025-13-01", bfms_object="phase", expected_state="completed", observed_state="completed", status="pass")
    folded = types.StageResult.from_sub_assertions(sub_assertions=[{"key": "a", "status": "pass"}, {"key": "b", "status": "unknown", "reason": "not carried"}], **stage_fields)
    assert folded.status == "unknown" and folded.reason == "not carried"
    assert types.worst_status(["pass", "not_applicable"]) == "pass"
    assert types.worst_status(["not_applicable"]) == "not_applicable"

    kwargs = _minimal_report_kwargs(labkit)
    for bad in ("We recommend proceeding.", "The deal is compliant.", "The deal was approved by the board.", "twin-bfms is a process twin of issuance."):
        with pytest.raises(ValidationError):
            types.RunReport(lab_statements=[bad], **kwargs)
    ok = types.RunReport(lab_statements=["3 approved facts drive the checklist; review by the lab-scripted reviewer."], **kwargs)
    assert ok.counts == {"pass": 0, "fail": 0, "unknown": 0, "not_applicable": 0}
    with pytest.raises(ValidationError):
        types.RunReport(**{**kwargs, "pins": {}})
    with pytest.raises(ValidationError):
        types.RunReport(**{**kwargs, "scenario_id": law.DEMO_DEAL_ID})
    with pytest.raises(ValidationError):
        types.RunReport(**{**kwargs, "_legend": "SYNTHETIC"})


def test_lab_goldens_carry_client_gates_not_applicable() -> None:
    labkit = lab_support.import_labkit()
    law = labkit.law
    missing = [d for d in DEAL_IDS if not (LAB / "expected" / d / "run-report.expected.json").is_file()]
    assert missing == [], f"goldens not derived yet (runner lane, build step 6): {missing}"
    for deal_id in DEAL_IDS:
        golden = json.loads((LAB / "expected" / deal_id / "run-report.expected.json").read_text(encoding="utf-8"))
        assert golden["scenario_id"] == deal_id
        gates = golden.get("pilot_gates") or {}
        for gate, status in law.PILOT_GATE_STATUS.items():
            assert gates.get(gate) == status, f"{deal_id}: golden {gate} != {status}"
            assert law.CLIENT_GATE_REASON in json.dumps(gates), f"{deal_id}: client-gate reason missing"
        assert set(golden["stages"]) == set(law.EXPECTED_STAGE_IDS)
        assert set(golden["stages"].values()) <= set(law.FOUR_VALUES)
        assert golden["stages"]["S11"] == "not_applicable" and golden["stages"]["S17"] == "not_applicable"


def _view(stages: dict[str, str], subs: dict[str, str] | None = None, conf: dict[str, str] | None = None) -> dict:
    return {
        "scenario_id": DEAL_IDS[0],
        "stages": dict(stages),
        "sub_assertions": dict(subs or {}),
        "conformance": dict(conf or {}),
        "register_status_counts": {"filed": 6, "not filed": 1, "evidence missing": 2, "not testable": 8},
        "gaps": 2,
        "open_items": 3,
        "reasons": {},
    }


_F9 = {"S05.artifact_dedup": "fail", "S05.artifact_level_sha256": "fail"}
_SMOKE_TABLE = [
    # label, observed view, golden view (None = absent), fence-class violation, expected gate
    ("golden match, only F9 fails", _view({"S00": "pass", "S05": "fail"}, _F9), _view({"S00": "pass", "S05": "fail"}, _F9), False, "pass"),
    ("golden match, no fails", _view({"S00": "pass", "S11": "not_applicable"}), _view({"S00": "pass", "S11": "not_applicable"}), False, "pass"),
    ("fence-class violation", _view({"S00": "pass", "S05": "fail"}, _F9), _view({"S00": "pass", "S05": "fail"}, _F9), True, "fail"),
    ("golden absent", _view({"S00": "pass"}), None, False, "fail"),
    ("non-golden fail", _view({"S00": "fail"}), _view({"S00": "pass"}), False, "fail"),
    ("unknown where golden expects pass", _view({"S00": "unknown", "S05": "fail"}, _F9), _view({"S00": "pass", "S05": "fail"}, _F9), False, "fail"),
    ("BFMS improved: pass where golden expects fail", _view({"S00": "pass", "S05": "pass"}), _view({"S00": "pass", "S05": "fail"}, _F9), False, "fail"),
    ("golden-matched fail outside the F9 set", _view({"S00": "pass", "S06": "fail"}), _view({"S00": "pass", "S06": "fail"}), False, "fail"),
    ("stage missing vs golden", _view({"S00": "pass"}), _view({"S00": "pass", "S01": "pass"}), False, "fail"),
    ("conformance fail matched by golden", _view({"S00": "pass"}, None, {"closing": "fail"}), _view({"S00": "pass"}, None, {"closing": "fail"}), False, "fail"),
]


@pytest.mark.parametrize(("label", "observed", "golden", "violation", "expected"), _SMOKE_TABLE, ids=[row[0] for row in _SMOKE_TABLE])
def test_lab_smoke_gate_rule_table(label, observed, golden, violation, expected) -> None:
    """S16: `report.smoke_gate(view, expected, golden_diff, fence_class_violation)` is pass iff
    the golden matches, no fence-class violation was recorded, and the only fail rows are
    the accepted F9 rows (`report.KNOWN_GAP_KEYS`)."""
    lab_support.import_labkit()
    from labkit import report

    assert report.KNOWN_GAP_KEYS >= set(_F9), "F9 rows must be the accepted gaps"
    _f16 = {"S12", "S12.sector_liability_disclaimers_present"}
    assert not (report.KNOWN_GAP_KEYS - {"S05", *_F9, *_f16}), f"accepted gaps widened beyond F9/F16: {sorted(report.KNOWN_GAP_KEYS)}"
    golden_diff = report.diff_against_expected(observed, golden)
    status, reason = report.smoke_gate(observed, golden, golden_diff, violation)
    assert status == expected, f"{label}: {status} ({reason})"
    assert (status == "pass") == (reason == ""), f"{label}: a fail needs a reason, a pass needs none"


def _hold_scenario(tmp_path: Path):
    lab_support.import_labkit()
    from labkit import scenario

    data = json.loads((LAB / "scenarios" / f"{DEAL_IDS[0]}.synthetic.json").read_text(encoding="utf-8"))
    hold = copy.deepcopy(data)
    hold["deal_id"] = "SYN-HSG-AZ-2025-LAB99"
    hold["lab"]["deal_status"] = "on_hold"
    hold["lab"]["knobs"]["deal_status"] = "on_hold"
    hold["lab"]["expected_report"] = "expected/SYN-HSG-AZ-2025-LAB99/run-report.expected.json"
    path = tmp_path / "SYN-HSG-AZ-2025-LAB99.synthetic.json"
    path.write_text(json.dumps(hold, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    sc = scenario.load(path)
    assert sc.on_hold and sc.deal_status == "on_hold"
    return sc


def test_lab_hold_knob_emitter(tmp_path: Path) -> None:
    lab_support.import_labkit()
    from labkit import events

    sc = _hold_scenario(tmp_path)
    emission = events.emit(sc.data)
    by_event = {row.event: row for row in emission.events}
    for event in HOLD_EVENTS:
        row = by_event[event]
        assert row.date == "" and row.status == "on_hold", f"{event}: {row}"
        assert "close not invented" in row.reason
    assert by_event["final_resolution"].status == "fired" and by_event["final_resolution"].date == "2025-06-11"
    assert all(r.date == "" for r in emission.undated_rows())
    assert emission.undated_rows() == emission.events[len(emission.dated_rows()) :]


def test_lab_hold_knob_short_circuits_honestly(tmp_path: Path) -> None:
    lab_support.import_labkit()
    from labkit import events, law, post_close, replay

    from munipal.services.deal_workflow import build_deal_workflow_from_seed, validate_deal_workflow

    sc = _hold_scenario(tmp_path)
    for hold in law.HOLD_STATUSES:
        status, reason = post_close.gate(hold, True)
        assert status == "not_applicable", f"gate({hold!r}) returned {status!r}"
        assert "close not invented" in reason
    status, reason = post_close.gate(sc.deal_status, False)
    assert status == "not_applicable" and "close not invented" in reason
    status, reason = post_close.gate("closed", False)
    assert status == "not_applicable" and "close not invented" in reason
    assert post_close.gate("closed", True) == ("pass", "")

    emission = events.emit(sc.data)
    rows = [r.as_dict() for r in emission.events]
    workflow = build_deal_workflow_from_seed(
        deal_id=sc.deal_id, name="hold", year=2025, borrower="Saguaro Commons Apartments, LP",
        conduit_issuer="The Industrial Development Authority of the City of Mesquite Flats", sector="housing",
    )
    result = replay.apply(rows, workflow, replay.Evidence(deal_status="on_hold", closing_literal=None))
    validate_deal_workflow(result.workflow)
    timeline = {t.phase: t.status for t in result.workflow.phase_timeline}
    for phase in ("closing", "post-closing", "closed"):
        if phase in timeline:
            assert timeline[phase] == "planned", f"{phase} advanced on a hold scenario"
    assert result.workflow.deal.closing_date is None
    hold_rows = {r.event: r for r in result.rows if r.event in HOLD_EVENTS}
    assert set(hold_rows) == set(HOLD_EVENTS)
    assert all(r.status == "unknown" and r.date is None for r in hold_rows.values())
    matrix = result.workflow.document_state_matrix()
    assert not any(state in ("executed", "filed") for state in matrix.values()), matrix
