"""Fence: the run report is hash-sealed, tamper-evident and golden-diffed (BUILD-SPEC 7, 6 row 22;
critic M16: the variant goldens differ from the base exactly where 3.4 says).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from tests import lab_support

LAB = lab_support.LAB_ROOT
LAB01, LAB02, LAB03 = "SYN-HSG-AZ-2025-LAB01", "SYN-HSG-AZ-2025-LAB02", "SYN-HSG-AZ-2025-LAB03"
_HEX64 = "a" * 64
_HEADER_KEYS = (
    "_legend", "label_notice", "schema_version", "run_id", "scenario_id", "scenario_sha256",
    "seed", "asof", "generator_version", "lab_version", "repo_commit", "repo_dirty", "python",
    "pins", "fulfillment_tree_sha256_before", "fulfillment_tree_sha256_after", "environment",
    "name_collision_check", "pilot_gates", "stages", "conformance_table", "register_summary",
    "counts", "lab_statements", "forbidden_scan", "golden_diff", "sealed_at", "content_hash",
)


def _sample_report(labkit):
    types, law = labkit.types, labkit.law
    stage = {"station": "6_borrower_prep", "bfms_stage": "WP2", "deal_phase": "diligence", "pilot_stage": "upload"}
    return types.RunReport(
        run_id=f"{LAB01}__2026-09-10__deadbeef",
        scenario_id=LAB01,
        scenario_sha256=_HEX64,
        seed=20250626,
        asof="2026-09-10",
        python="3.11.15",
        pins=dict.fromkeys(law.PIN_KEYS, _HEX64),
        pilot_gates=types.PilotGates(pilot_smoke_test_green="pass", known_gaps_accepted=["S05.artifact_dedup (F9)"]),
        stages=[
            types.StageResult(id="S00", status="pass", assertion="health", **{**stage, "station": "all", "bfms_stage": "WP1", "deal_phase": "engagement", "pilot_stage": "none"}),
            types.StageResult.from_sub_assertions(
                id="S05", assertion="vault", sub_assertions=[
                    {"key": "chunk_hash", "status": "pass"},
                    {"key": "artifact_dedup", "status": "fail", "reason": "second artifact id created (F9)"},
                ], **stage,
            ),
            types.StageResult(id="S11", status="not_applicable", reason="engines out of bounds", assertion="WP5", **{**stage, "station": "4_structure", "bfms_stage": "WP5", "deal_phase": "pricing", "pilot_stage": "none"}),
        ],
        conformance_table=[
            types.ConformanceRow(event="indenture_executed", station="4_structure", log_status="fired", date="2025-06-26", bfms_object="DealDocument trust-indenture", expected_state="executed", observed_state="executed", evidence_ref="closing-documents/01-indenture-excerpt.md", status="pass"),
            types.ConformanceRow(event="tefra_notice", station="3_issuance", log_status="unknown", bfms_object="(none)", expected_state="unchanged", observed_state="unchanged", status="unknown", reason="not carried by scenario"),
        ],
        register_summary={"status_counts": {"filed": 6, "not filed": 1, "evidence missing": 2, "not testable": 8}, "gaps": 2, "open_items": 3},
        bfms_emitted_language=[types.EmittedLanguage(source="readiness.explanation", sha256=_HEX64, excerpt="x" * 120)],
        lab_statements=["review performed by the lab-scripted reviewer, not a human"],
        sealed_at="2026-09-10T00:00:00+00:00",
    )


def test_lab_report_types_seal_and_tamper() -> None:
    labkit = lab_support.import_labkit()
    types = labkit.types
    report = _sample_report(labkit)
    assert report.content_hash is None and report.verify() is False
    sealed = report.seal()
    assert sealed.verify() is True and report.content_hash is None
    # S00 pass + chunk_hash pass + conformance pass; S05 fail (folded) + artifact_dedup fail;
    # tefra_notice unknown; S11 not_applicable -- counts are computed, never typed.
    assert sealed.counts == {"pass": 3, "fail": 2, "unknown": 1, "not_applicable": 1}
    assert sealed.compute_content_hash() == sealed.content_hash

    payload = sealed.model_dump(mode="json", by_alias=True)
    payload["stages"][1]["sub_assertions"][1]["status"] = "pass"
    tampered = types.RunReport.model_validate(payload)
    assert tampered.verify() is False, "flipping a status must break the seal"
    payload["stages"][1]["sub_assertions"][1]["status"] = "fail"
    assert types.RunReport.model_validate(payload).verify() is True
    payload["pilot_gates"]["registered_ma_confirmed"] = "pass"
    with pytest.raises(ValidationError):
        types.RunReport.model_validate(payload)
    with pytest.raises(ValidationError):
        types.EmittedLanguage(source="x", sha256=_HEX64, excerpt="y" * 121)
    with pytest.raises(ValidationError):
        types.RunReport()  # every header field is required; nothing defaults to a value


def _md_body(text: str, legend: str) -> str:
    """Body of a lab `.md` written by `provenance.write_md` (frontmatter, legend blockquotes
    and the closing legend line removed)."""
    lines = text.split("\n")
    assert lines[0] == "---"
    rest = lines[lines.index("---", 1) + 1 :]
    assert rest[:3] == ["", f"> {legend}", ""], "legend is not the first blockquote"
    assert rest[-1] == "" and rest[-2] == legend, "legend is not the last line"
    body = rest[3:-3]
    out: list[str] = []
    i = 0
    while i < len(body):
        if body[i : i + 3] == ["", f"> {legend}", ""]:
            i += 3
            continue
        out.append(body[i])
        i += 1
    return "\n".join(out)


def test_lab_report_seal_and_tamper(tmp_path: Path) -> None:
    labkit = lab_support.import_labkit()
    law = labkit.law
    from labkit import report as report_mod

    for name in ("build", "write", "verify", "diff_against_expected", "golden_view", "render_md", "load"):
        assert hasattr(report_mod, name), f"labkit.report.{name} missing (spec section 1)"

    sealed = _sample_report(labkit).seal()
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    json_path, md_path = report_mod.write(sealed, run_dir)
    assert json_path.name == "run-report.json" and md_path.name == "run-report.md"
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    for key in _HEADER_KEYS:
        assert key in payload, f"run-report.json lacks {key}"
    assert payload["_legend"] == law.LEGEND and payload["label_notice"] == law.LABEL_NOTICE
    assert payload["_provenance"]["scenario_id"] == LAB01  # stamped by the single writer
    assert json_path.read_text(encoding="utf-8") == labkit.provenance.canonical_json(payload)
    loaded = report_mod.load(json_path)
    assert loaded.verify() is True and report_mod.verify(json_path) is True
    assert loaded.content_hash == sealed.content_hash
    md = md_path.read_text(encoding="utf-8")
    assert _md_body(md, law.LEGEND) == report_mod.render_md(payload), "run-report.md is not re-derivable from the json"
    assert law.LABEL_NOTICE in md and law.SMOKE_GATE_MEANING in md
    assert md.rstrip("\n").split("\n")[-1] == law.LEGEND and f"content_hash: {sealed.content_hash}" in md
    for entry in payload["bfms_emitted_language"]:
        assert len(entry["sha256"]) == 64 and len(entry["excerpt"]) <= law.BFMS_EXCERPT_MAX_CHARS

    payload["stages"][0]["status"] = "fail"
    json_path.write_text(labkit.provenance.canonical_json(payload), encoding="utf-8")
    assert report_mod.verify(json_path) is False, "editing a status after sealing must break verify()"
    golden = report_mod.golden_view(loaded)
    for key in ("scenario_id", "stages", "sub_assertions", "conformance", "register_status_counts", "gaps", "open_items", "reasons"):
        assert key in golden, f"golden view lacks {key}"
    assert golden["stages"] == {"S00": "pass", "S05": "fail", "S11": "not_applicable"}
    assert golden["sub_assertions"] == {"S05.chunk_hash": "pass", "S05.artifact_dedup": "fail"}
    assert golden["conformance"] == {"indenture_executed": "pass", "tefra_notice": "unknown"}
    assert golden["register_status_counts"]["filed"] == 6 and golden["gaps"] == 2
    assert not any(k in golden for k in ("content_hash", "run_id", "scenario_sha256", "bfms_emitted_language"))
    assert report_mod.diff_against_expected(golden, golden) == []
    tampered = json.loads(json.dumps(golden))
    tampered["stages"]["S00"] = "fail"
    assert report_mod.diff_against_expected(golden, tampered) == [{"key": "stages.S00", "expected": "fail", "observed": "pass"}]
    assert report_mod.diff_against_expected(golden, None) != []


def _golden(deal_id: str) -> dict:
    path = LAB / "expected" / deal_id / "run-report.expected.json"
    assert path.is_file(), f"golden not derived yet (runner lane, build step 6): {path.relative_to(LAB).as_posix()}"
    return json.loads(path.read_text(encoding="utf-8"))


def test_lab_variants_provably_change_report() -> None:
    lab_support.import_labkit()
    base, late_afs, dropped = _golden(LAB01), _golden(LAB02), _golden(LAB03)
    assert base["register_status_counts"] == {"filed": 6, "not filed": 1, "evidence missing": 2, "not testable": 8}
    assert late_afs["register_status_counts"] == {"filed": 3, "not filed": 1, "evidence missing": 5, "not testable": 8}
    assert (base["gaps"], late_afs["gaps"]) == (2, 5)
    assert base["open_items"] == late_afs["open_items"] == 3
    assert late_afs["conformance"]["afs_posted_fy2025"] == "unknown"
    assert base["conformance"]["afs_posted_fy2025"] != "unknown"
    pre_close = [s for s in base["stages"] if s < "S15"]
    assert all(late_afs["stages"][s] == base["stages"][s] for s in pre_close), "late_afs changed a pre-close stage"

    assert dropped["register_status_counts"] == base["register_status_counts"]
    assert dropped["stages"]["S15"] == base["stages"]["S15"]
    assert "S04.declared_gap" in dropped["sub_assertions"] and "S04.declared_gap" not in base["sub_assertions"]

    def unknown_count(golden: dict) -> int:
        return sum(1 for k, v in golden["sub_assertions"].items() if k.startswith("S06.") and v == "unknown")

    assert unknown_count(dropped) > unknown_count(base), "dropping site_control_permits must add S06 unknowns"
    assert unknown_count(dropped) - unknown_count(base) == 7
