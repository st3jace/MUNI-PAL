"""E2E fence: the three synthetic housing scenarios driven S00-S18 through the full BFMS
in-process, on the conftest fixtures, against the status-only goldens (BUILD-SPEC 6 row 24;
8 step 7).

For each of SYN-HSG-AZ-2025-LAB01 / LAB02 (`late_afs`) / LAB03 (`drop_required_artifact`):
`harness.attach(...)` on `test_client / db_session / auth_headers / monkeypatch / tmp_path`,
`bfms_driver.Driver(...).run_all()`, `report.build -> write -> verify`, then every stage,
sub-assertion and conformance status must equal `expected/<deal_id>/run-report.expected.json`
(derived from an actual standalone run, never typed) UNMODIFIED: the driver emits one status
per row in both harness modes (`S00.engines_not_loaded` is `not_applicable` by rule in both;
S18 asserts the engines module set is unchanged instead). The sensing corpus must be
unreachable for the whole run (Class D fence), extraction must be the rules-based fallback
(no LLM), the only `fail` rows are the accepted known-gap rows (F9, F16), nothing is written
under `lab/twin-bfms/runs/` (the run lives in `tmp_path`), and each scenario finishes inside
the runtime budget.

Lab code is reached only through `tests.lab_support` (critic M12). Nothing under `src/`
is patched beyond what the harness patches through `monkeypatch`. twin-bfms is a label,
not a claim.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import pytest

from tests import lab_support

LAB: Path = lab_support.LAB_ROOT
DEAL_IDS: tuple[str, ...] = (
    "SYN-HSG-AZ-2025-LAB01",
    "SYN-HSG-AZ-2025-LAB02",
    "SYN-HSG-AZ-2025-LAB03",
)
RUNTIME_BUDGET_SECONDS = 45.0
RULES_MODE = "rules_based_fallback"
SENSING_SECTORS: tuple[str, ...] = ("healthcare", "waste")
CORPUS_UNAVAILABLE: dict[str, bool] = dict.fromkeys(SENSING_SECTORS, False)
ENGINES_ROW = "S00.engines_not_loaded"
# S08 items whose required paths the LAB03 knob (`drop_required_artifact=site_control_permits`)
# removes from the pack: scored against the mechanical expectation, never excused as
# not_applicable (the not_applicable test is over the scenario FAMILY path set) and never
# unknown (BFMS was called and answered); the knob effect is carried in the ratcheted reason.
KNOB_SCORED_ITEMS: tuple[str, ...] = ("S08.item_P2.2", "S08.item_P3.3")
KNOB_SCORED_NOTE = "absent by scenario knob"
ENGINES_ROW_REASON = "shared interpreter possible; enforced by S18.engines_modules_unchanged and the import fence"


def _runs_listing() -> set[str]:
    runs = LAB / "runs"
    return {p.name for p in runs.iterdir()} if runs.is_dir() else set()


def _header(sc: Any, out: Any, run_id: str, commit: str, dirty: bool | str, versions: tuple[str, str]) -> dict[str, Any]:
    """The report header exactly as `lab/twin-bfms/run_lab.py::drive` assembles it."""
    generator_version, lab_version = versions
    return {
        "run_id": run_id,
        "scenario_id": sc.deal_id,
        "scenario_sha256": sc.sha256,
        "derived_from": sc.derived_from,
        "seed": sc.seed,
        "asof": sc.asof,
        "generator_version": generator_version,
        "lab_version": lab_version,
        "repo_commit": commit,
        "repo_dirty": dirty,
        "python": out.python,
        "pins": out.pins,
        "fulfillment_tree_sha256_before": out.fulfillment_tree_before,
        "fulfillment_tree_sha256_after": out.fulfillment_tree_after,
        "environment": out.environment,
    }


@pytest.mark.parametrize("deal_id", DEAL_IDS)
async def test_lab_e2e_housing_three_scenarios(
    deal_id: str,
    test_client,
    db_session,
    auth_headers: dict[str, str],
    factory,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    request: pytest.FixtureRequest,
) -> None:
    labkit = lab_support.import_labkit()
    from labkit import GENERATOR_VERSION, LAB_VERSION, bfms_driver, harness, law
    from labkit import report as report_mod
    from labkit import scenario as scenario_mod

    sc = scenario_mod.load(LAB / "scenarios" / f"{deal_id}.synthetic.json")
    assert sc.deal_id == deal_id and sc.data["mode"] == "synthetic"
    pack_root = LAB / "packs" / deal_id
    assert (pack_root / law.PACK_MANIFEST_NAME).is_file(), f"committed pack missing: {pack_root}"
    golden_path = report_mod.expected_path(deal_id)
    golden = report_mod.load_expected(golden_path)
    assert golden is not None, f"golden absent: {golden_path.relative_to(LAB).as_posix()}"
    assert golden["scenario_id"] == deal_id
    for gate, status in law.PILOT_GATE_STATUS.items():
        assert golden["pilot_gates"][gate] == status
    # the committed golden is compared unmodified: no harness-mode rewrite of any key
    assert golden["sub_assertions"][ENGINES_ROW] == "not_applicable"
    assert golden["reasons"][ENGINES_ROW] == ENGINES_ROW_REASON
    expected = golden
    runs_before = _runs_listing()

    # -- harness on the conftest fixtures; every patch is undone by monkeypatch -----------
    ctx = harness.attach(test_client, db_session, auth_headers, monkeypatch, tmp_path, request=request)
    assert ctx.mode == "attach"
    assert ctx.client is test_client and ctx.session is db_session
    assert factory.session is ctx.session, "the factory and the harness must share the conftest session"
    assert ctx.llm_forbidden and ctx.sensing_pinned
    assert ctx.munipal_root_pin == "attr-patched"
    assert not ctx.anthropic_key_present()
    assert str(ctx.sensing_extractor_path()).startswith(str(tmp_path))

    # -- Class D fence: record every `_corpus_available` answer during the run ------------
    sensing = ctx.sensing_module()
    original_corpus_available = sensing._corpus_available
    corpus_answers: list[tuple[str, bool]] = []

    def _recording_corpus_available(sector: str) -> bool:
        value = bool(original_corpus_available(sector))
        corpus_answers.append((sector, value))
        return value

    monkeypatch.setattr(sensing, "_corpus_available", _recording_corpus_available)
    assert ctx.corpus_available() == CORPUS_UNAVAILABLE

    # -- drive S00-S18 -----------------------------------------------------------------
    commit = bfms_driver.repo_commit()
    dirty = bfms_driver.repo_dirty()
    run_id = bfms_driver.run_id_for(sc, commit)
    run_dir = ctx.run_dir
    driver = bfms_driver.Driver(ctx, sc, pack_root, run_dir, run_id)
    engines_before = harness.engines_modules_loaded()
    started = time.perf_counter()
    out = await driver.run_all()
    report = report_mod.build(
        header=_header(sc, out, run_id, commit, dirty, (GENERATOR_VERSION, LAB_VERSION)),
        stages=out.stages,
        conformance_table=out.conformance_rows,
        deal_workflow_mirror=out.deal_workflow_mirror,
        register_summary=out.register_summary,
        review=out.review,
        vocabulary_divergence=out.vocabulary_divergence,
        bfms_emitted_language=out.bfms_emitted_language,
        findings_touched=out.findings_touched,
        lab_statements=out.lab_statements,
        forbidden_scan=out.forbidden_scan,
        expected=expected,
        fence_class_violation=out.fence_class_violation,
        seal_stage=driver.seal_stage(out.forbidden_scan),
    )
    json_path, md_path = report_mod.write(report, run_dir)
    elapsed = time.perf_counter() - started

    # -- fences on the run itself --------------------------------------------------------
    assert out.fence_class_violation is False
    assert sum(out.forbidden_scan.values()) == 0, out.forbidden_scan
    assert out.environment["extraction_mode"] == RULES_MODE
    assert out.environment["anthropic_key_present"] is False
    assert out.environment["harness_mode"] == "attach"
    assert out.environment["munipal_root_pinned"] == "attr-patched"
    assert out.environment["sensing_corpus_available"] == CORPUS_UNAVAILABLE
    assert harness.engines_modules_loaded() == engines_before, "the run must not import a munipal engines module"
    assert corpus_answers, "sensing._corpus_available was never consulted during the run"
    assert {sector for sector, _ in corpus_answers} == set(SENSING_SECTORS)
    assert all(value is False for _, value in corpus_answers), corpus_answers
    assert ctx.corpus_available() == CORPUS_UNAVAILABLE
    assert elapsed < RUNTIME_BUDGET_SECONDS, f"{deal_id}: {elapsed:.1f}s exceeds the {RUNTIME_BUDGET_SECONDS:.0f}s budget"

    # -- the report verifies and is written from the single writer -----------------------
    assert json_path.is_file() and md_path.is_file()
    assert report_mod.verify(json_path) is True
    loaded = report_mod.load(json_path)
    assert loaded.scenario_id == deal_id and loaded.run_id == run_id
    assert loaded.content_hash == report.content_hash
    assert law.LEGEND in md_path.read_text(encoding="utf-8")

    # -- statuses == committed golden, unmodified (stage / sub-assertion / conformance) ---
    view = report_mod.golden_view(loaded)
    diff = report_mod.diff_against_expected(view, golden)
    assert diff == [], f"{deal_id}: golden deltas -> update the golden after review: {diff}"
    assert loaded.golden_diff == []
    observed_stages = {stage.id: stage.status for stage in loaded.stages}
    assert observed_stages == golden["stages"]
    assert view["sub_assertions"] == golden["sub_assertions"]
    assert view["reasons"] == golden["reasons"]
    assert view["conformance"] == golden["conformance"]
    assert (view["gaps"], view["open_items"]) == (golden["gaps"], golden["open_items"])
    assert view["base_equivalence"] == golden["base_equivalence"]
    assert set(observed_stages) == set(law.EXPECTED_STAGE_IDS)
    assert observed_stages["S11"] == "not_applicable" and observed_stages["S17"] == "not_applicable"
    assert observed_stages["S05"] == "fail", "F9 rows are observed, definite fails"
    assert observed_stages["S12"] == "fail", "the F16 row is an observed, definite fail"
    assert view["sub_assertions"]["S12.sector_liability_disclaimers_present"] == "fail"
    assert view["sub_assertions"]["S18.engines_modules_unchanged"] == "pass"
    assert report_mod.fail_keys(view) <= report_mod.KNOWN_GAP_KEYS, sorted(report_mod.fail_keys(view))
    assert view["register_status_counts"] == golden["register_status_counts"]
    assert set(view["register_status_counts"]) == set(law.REGISTER_STATUSES)

    # -- knob-dropped checklist items are scored (pass/fail), not excused or unmeasured ----
    knob_dropped = bool(sc.dropped_intake_paths)
    for key in KNOB_SCORED_ITEMS:
        assert view["sub_assertions"][key] in {"pass", "fail"}, (key, view["sub_assertions"][key])
        assert (KNOB_SCORED_NOTE in view["reasons"][key]) is knob_dropped, (key, view["reasons"][key])

    # -- pins are recomputed from the files and match packs/_pins.json in-run ------------
    for key in ("S15.run_py_pin_matches", "S15.build_fixtures_pin_matches", "S15.bondi_format_pin_matches", "S15.pack_manifest_pin_matches"):
        assert view["sub_assertions"][key] == "pass", key

    # -- pilot gates: client gates structurally not_applicable; smoke gate green ----------
    gates = loaded.pilot_gates
    assert gates.registered_ma_confirmed == "not_applicable"
    assert gates.engagement_scope_signed == "not_applicable"
    assert gates.registered_ma_confirmed_reason == law.CLIENT_GATE_REASON
    assert gates.pilot_smoke_test_green == "pass", gates.pilot_smoke_test_green_meaning
    assert law.SMOKE_GATE_MEANING in gates.pilot_smoke_test_green_meaning
    assert list(gates.known_gaps_accepted) == list(report_mod.KNOWN_GAPS_ACCEPTED)

    # -- TR-1: the run stayed in tmp_path; nothing landed under lab/twin-bfms/runs/ -------
    assert _runs_listing() == runs_before
    assert json_path.is_relative_to(tmp_path)
    assert not any(p.suffix.lower() in {".pdf", ".docx", ".xlsx"} for p in tmp_path.rglob("*") if p.is_file())
    assert labkit.LAB_VERSION == loaded.lab_version
