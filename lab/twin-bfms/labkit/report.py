"""Run report: build / write (json + md) / verify / golden view / diff (BUILD-SPEC 7).

The report is a `labkit.types.RunReport`; every status in it is four-valued by type. The
json is canonical (sorted keys, LF) and hash-sealed (`content_hash` covers every other
field); the markdown is rendered from the json only. The golden
(`expected/<deal_id>/run-report.expected.json`) is a status-only view: stage statuses,
sub-assertion statuses, conformance statuses, register counts and the reasons attached
to non-pass rows -- never BFMS prose, never ids, never hashes.

This is the only lab module allowed to read the clock (`sealed_at`).
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from labkit import law
from labkit.provenance import canonical_json, sha256_text, write_json, write_md
from labkit.types import EmittedLanguage, Envelope, PilotGates, RunReport, StageResult

REPORT_JSON = "run-report.json"
REPORT_MD = "run-report.md"
GOLDEN_NAME = "run-report.expected.json"
EXPECTED_DIR: Path = law.LAB_ROOT / "expected"
#: The only fail rows a green smoke gate tolerates (F9 and F16, observed and definite);
#: the stage keys are listed because a failing sub-assertion folds its stage to fail.
KNOWN_GAP_KEYS: frozenset[str] = frozenset({
    "S05", "S05.artifact_dedup", "S05.artifact_level_sha256",
    "S12", "S12.sector_liability_disclaimers_present",
})
KNOWN_GAPS_ACCEPTED: tuple[str, ...] = (
    "S05.artifact_dedup (F9)",
    "S05.artifact_level_sha256 (F9)",
    "S12.sector_liability_disclaimers_present (F16)",
)


# --------------------------------------------------------------------------------------
# Golden view + diff
# --------------------------------------------------------------------------------------


def golden_view(report: RunReport | dict[str, Any]) -> dict[str, Any]:
    """Status-only projection of a report (works on the model or its json dict)."""
    data = report.model_dump(mode="json", by_alias=True) if isinstance(report, RunReport) else report
    stages: dict[str, str] = {}
    subs: dict[str, str] = {}
    reasons: dict[str, str] = {}
    for stage in data.get("stages", []):
        stages[stage["id"]] = stage["status"]
        if stage.get("reason"):
            reasons[stage["id"]] = stage["reason"]
        for sub in stage.get("sub_assertions", []):
            key = f"{stage['id']}.{sub['key']}"
            subs[key] = sub["status"]
            if sub.get("reason"):
                reasons[key] = sub["reason"]
    conformance: dict[str, str] = {}
    for row in data.get("conformance_table", []):
        conformance[row["event"]] = row["status"]
        if row.get("reason"):
            reasons[f"conformance.{row['event']}"] = row["reason"]
    register = data.get("register_summary") or {}
    return {
        "scenario_id": data.get("scenario_id"),
        "stages": stages,
        "sub_assertions": subs,
        "conformance": conformance,
        "register_status_counts": register.get("status_counts", {}),
        "gaps": register.get("gaps"),
        "open_items": register.get("open_items"),
        "base_equivalence": register.get("base_equivalence"),
        "pilot_gates": {
            key: (data.get("pilot_gates") or {}).get(key)
            for key in (
                "registered_ma_confirmed",
                "registered_ma_confirmed_reason",
                "engagement_scope_signed",
                "engagement_scope_signed_reason",
            )
        },
        "reasons": reasons,
    }


def _flatten(prefix: str, value: Any, out: dict[str, Any]) -> None:
    if isinstance(value, dict):
        for k in sorted(value):
            _flatten(f"{prefix}.{k}" if prefix else str(k), value[k], out)
    else:
        out[prefix] = value


def diff_against_expected(view: dict[str, Any], expected: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Flat list of `{key, expected, observed}` (empty == golden match)."""
    if expected is None:
        return [{"key": "<golden>", "expected": "present", "observed": "absent"}]
    a: dict[str, Any] = {}
    b: dict[str, Any] = {}
    _flatten("", expected, a)
    _flatten("", view, b)
    diffs: list[dict[str, Any]] = []
    for key in sorted(set(a) | set(b)):
        if a.get(key, "<missing>") != b.get(key, "<missing>"):
            diffs.append({"key": key, "expected": a.get(key, "<missing>"), "observed": b.get(key, "<missing>")})
    return diffs


def expected_path(deal_id: str) -> Path:
    return EXPECTED_DIR / deal_id / GOLDEN_NAME


def _without_seal_stage(view: dict[str, Any]) -> dict[str, Any]:
    """Copy of a golden view with every S18 entry removed (S18 depends on the diff itself)."""
    out = json.loads(json.dumps(view))
    out.get("stages", {}).pop("S18", None)
    for key in ("sub_assertions", "reasons"):
        block = out.get(key, {})
        for k in [k for k in block if k == "S18" or k.startswith("S18.")]:
            block.pop(k, None)
    return out


def load_expected(path: Path) -> dict[str, Any] | None:
    path = Path(path)
    if not path.is_file():
        return None
    doc = json.loads(path.read_text(encoding="utf-8"))
    for key in ("_legend", "_provenance", "note"):
        doc.pop(key, None)
    return doc


def write_golden(view: dict[str, Any], path: Path, envelope: Envelope) -> Path:
    """Persist a status-only golden (derived from a run, reviewed by a human, never typed)."""
    payload = _without_seal_stage(view)
    # the golden encodes the expectation that a later run matches it: S18 is then pass
    payload.setdefault("stages", {})["S18"] = "pass"
    subs = payload.setdefault("sub_assertions", {})
    subs["S18.forbidden_scan_clean"] = "pass"
    subs["S18.engines_modules_unchanged"] = "pass"
    subs["S18.golden"] = "pass"
    payload["note"] = "status-only golden derived from an actual run; review before freezing"
    write_json(Path(path), payload, envelope.model_copy(update={"created_from": ["labkit/report.py::write_golden"]}))
    return Path(path)


# --------------------------------------------------------------------------------------
# Smoke gate
# --------------------------------------------------------------------------------------


def fail_keys(view: dict[str, Any]) -> set[str]:
    keys = {k for k, v in view["stages"].items() if v == "fail"}
    keys |= {k for k, v in view["sub_assertions"].items() if v == "fail"}
    keys |= {f"conformance.{k}" for k, v in view["conformance"].items() if v == "fail"}
    return keys


def smoke_gate(view: dict[str, Any], expected: dict[str, Any] | None, golden_diff: list[Any], fence_class_violation: bool) -> tuple[str, str]:
    """pass iff golden matches, no fence-class violation and the only fails are the accepted
    known-gap rows (F9, F16)."""
    if fence_class_violation:
        return "fail", "fence-class violation recorded"
    if expected is None:
        return "fail", "golden absent; derive it from this run and review it"
    if golden_diff:
        return "fail", f"{len(golden_diff)} golden delta(s); update the golden after review"
    observed = fail_keys(view)
    if not observed <= KNOWN_GAP_KEYS:
        return "fail", f"fail rows outside the accepted known-gap set (F9, F16): {sorted(observed - KNOWN_GAP_KEYS)}"
    return "pass", ""


# --------------------------------------------------------------------------------------
# Build / seal / write / verify
# --------------------------------------------------------------------------------------


def emitted(source: str, text: str) -> EmittedLanguage:
    """BFMS-native prose is never restated: sha256 + a short excerpt."""
    flat = law.EMMA_WORD.sub("<platform token>", " ".join(str(text).split()))
    excerpt = flat[: law.BFMS_EXCERPT_MAX_CHARS]
    return EmittedLanguage(source=source, sha256=sha256_text(str(text)), excerpt=excerpt)


def build(
    *,
    header: dict[str, Any],
    stages: list[StageResult],
    conformance_table: list[Any],
    deal_workflow_mirror: dict[str, Any],
    register_summary: dict[str, Any],
    review: dict[str, Any],
    vocabulary_divergence: dict[str, Any],
    bfms_emitted_language: list[EmittedLanguage],
    findings_touched: list[str],
    lab_statements: list[str],
    forbidden_scan: dict[str, int],
    expected: dict[str, Any] | None,
    fence_class_violation: bool,
    seal_stage: Any,
) -> RunReport:
    """Assemble the report. `seal_stage(status, reason, golden_diff)` must return the S18
    StageResult; it is called twice (provisional S18 for the diff, then the final one)."""
    provisional = seal_stage("unknown", "provisional", [])
    draft_stages = [*stages, provisional]
    draft = _report(header, draft_stages, conformance_table, deal_workflow_mirror, register_summary, review,
                    vocabulary_divergence, bfms_emitted_language, findings_touched, lab_statements, forbidden_scan,
                    PilotGates(pilot_smoke_test_green="fail", known_gaps_accepted=list(KNOWN_GAPS_ACCEPTED)), [])
    view = _without_seal_stage(golden_view(draft))
    expected_wo = _without_seal_stage(expected) if expected is not None else None
    partial_diff = diff_against_expected(view, expected_wo)
    scan_hits = sum(int(v) for v in forbidden_scan.values())
    if fence_class_violation or scan_hits:
        s18_status, s18_reason = "fail", f"fence-class violation; forbidden scan hits={scan_hits}"
    elif expected is None:
        s18_status, s18_reason = "unknown", "golden absent; derive expected/<deal_id>/run-report.expected.json from this run and review it"
    elif partial_diff:
        s18_status, s18_reason = "fail", f"{len(partial_diff)} golden delta(s); update the golden after review"
    else:
        s18_status, s18_reason = "pass", ""
    final_stages = [*stages, seal_stage(s18_status, s18_reason, partial_diff)]
    full_view = golden_view(_report(header, final_stages, conformance_table, deal_workflow_mirror, register_summary, review,
                                    vocabulary_divergence, bfms_emitted_language, findings_touched, lab_statements,
                                    forbidden_scan, PilotGates(pilot_smoke_test_green="fail"), []))
    golden_diff = diff_against_expected(full_view, expected) if expected is not None else partial_diff
    smoke, smoke_reason = smoke_gate(full_view, expected, golden_diff, fence_class_violation or bool(scan_hits))
    meaning = law.SMOKE_GATE_MEANING + (f" [{smoke_reason}]" if smoke_reason else "")
    gates = PilotGates(
        pilot_smoke_test_green=smoke,  # type: ignore[arg-type]
        pilot_smoke_test_green_meaning=meaning,
        known_gaps_accepted=list(KNOWN_GAPS_ACCEPTED),
    )
    report = _report(header, final_stages, conformance_table, deal_workflow_mirror, register_summary, review,
                     vocabulary_divergence, bfms_emitted_language, findings_touched, lab_statements, forbidden_scan,
                     gates, golden_diff)
    return report.model_copy(update={"sealed_at": datetime.now(UTC).isoformat()}).seal()


def _report(header, stages, conformance_table, mirror, register_summary, review, vocabulary_divergence,
            emitted_language, findings_touched, lab_statements, forbidden_scan, gates, golden_diff) -> RunReport:  # type: ignore[no-untyped-def]
    return RunReport(
        **header,
        pilot_gates=gates,
        stages=sorted(stages, key=lambda s: s.id),
        conformance_table=list(conformance_table),
        deal_workflow_mirror=dict(mirror),
        register_summary=dict(register_summary),
        review=dict(review),
        vocabulary_divergence=dict(vocabulary_divergence),
        bfms_emitted_language=list(emitted_language),
        findings_touched=sorted(set(findings_touched), key=lambda f: (len(f), f)),
        lab_statements=list(lab_statements),
        forbidden_scan=dict(forbidden_scan),
        golden_diff=list(golden_diff),
    )


def write(report: RunReport, run_dir: Path) -> tuple[Path, Path]:
    """json (canonical, legend + provenance keys) and md (rendered from the json only)."""
    run_dir = Path(run_dir)
    env = Envelope(scenario_id=report.scenario_id, seed=report.seed, created_from=["labkit/report.py::build"])
    payload = report.model_dump(mode="json", by_alias=False)
    payload.pop("legend", None)  # the writer stamps `_legend`; `_legend` is the alias
    json_path = run_dir / REPORT_JSON
    write_json(json_path, payload, env)
    md_path = run_dir / REPORT_MD
    write_md(md_path, render_md(json.loads(json_path.read_text(encoding="utf-8"))), env)
    return json_path, md_path


def load(path: Path) -> RunReport:
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    doc.pop("_provenance", None)
    return RunReport.model_validate(doc)


def verify(path: Path) -> bool:
    """Re-read the json and recompute the seal."""
    try:
        return load(path).verify()
    except (OSError, ValueError):
        return False


# --------------------------------------------------------------------------------------
# Markdown rendering (from the json dict only)
# --------------------------------------------------------------------------------------


def _cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def render_md(doc: dict[str, Any]) -> str:
    lines: list[str] = [
        f"# Lab run report {doc['scenario_id']}",
        "",
        doc["label_notice"],
        "",
        "## Header",
        "",
        "| key | value |",
        "|---|---|",
    ]
    for key in ("run_id", "scenario_id", "scenario_sha256", "derived_from", "seed", "asof", "generator_version",
                "lab_version", "repo_commit", "repo_dirty", "python", "fulfillment_tree_sha256_before",
                "fulfillment_tree_sha256_after", "sealed_at"):
        lines.append(f"| {key} | {_cell(doc.get(key))} |")
    for key, value in sorted((doc.get("pins") or {}).items()):
        lines.append(f"| pins.{key} | {_cell(value)} |")
    for key, value in sorted((doc.get("environment") or {}).items()):
        lines.append(f"| environment.{key} | {_cell(value)} |")
    for key, value in sorted((doc.get("name_collision_check") or {}).items()):
        lines.append(f"| name_collision_check.{key} | {_cell(value)} |")
    gates = doc.get("pilot_gates") or {}
    lines += ["", "## Pilot gates", ""]
    for key in ("registered_ma_confirmed", "registered_ma_confirmed_reason", "engagement_scope_signed",
                "engagement_scope_signed_reason", "pilot_smoke_test_green", "pilot_smoke_test_green_meaning",
                "known_gaps_accepted", "gate_definition_ref", "display_name_finding"):
        lines.append(f"- {key}: {_cell(gates.get(key))}")
    lines += ["", "## Stages", "", "| id | station | WP/P | DealPhase | pilot stage | status | reason |", "|---|---|---|---|---|---|---|"]
    for stage in doc.get("stages", []):
        wp = stage["bfms_stage"] + (f" / {stage['checklist_phase']}" if stage.get("checklist_phase") else "")
        lines.append(f"| {stage['id']} | {_cell(stage['station'])} | {_cell(wp)} | {_cell(stage['deal_phase'])} | {_cell(stage['pilot_stage'])} | {stage['status']} | {_cell(stage.get('reason', ''))} |")
        for sub in stage.get("sub_assertions", []):
            lines.append(f"| {stage['id']}.{_cell(sub['key'])} | | | | | {sub['status']} | {_cell(sub.get('reason', ''))} |")
    lines += ["", "## Deal trace (six stations)", "",
              "| date | station | event | log status | BFMS object | expected | observed | evidence | not carried by scenario | status |",
              "|---|---|---|---|---|---|---|---|---|---|"]
    for row in doc.get("conformance_table", []):
        not_carried = row["reason"] if row["status"] in ("unknown", "not_applicable") else ""
        lines.append(
            f"| {_cell(row.get('date') or '')} | {row['station']} | {row['event']} | {row['log_status']} | {_cell(row['bfms_object'])} | "
            f"{_cell(row['expected_state'])} | {_cell(row['observed_state'])} | {_cell(row.get('evidence_ref') or '')} | {_cell(not_carried)} | {row['status']} |"
        )
    reg = doc.get("register_summary") or {}
    lines += ["", "## Register summary", ""]
    for key in sorted(reg):
        lines.append(f"- {key}: {_cell(reg[key])}")
    lines += ["", "## Review", ""]
    for key in sorted(doc.get("review") or {}):
        lines.append(f"- {key}: {_cell(doc['review'][key])}")
    lines += ["", "## Vocabulary divergence", ""]
    for key in sorted(doc.get("vocabulary_divergence") or {}):
        lines.append(f"- {key}: {_cell(doc['vocabulary_divergence'][key])}")
    lines += ["", "## BFMS emitted language (hash + excerpt; never restated)", ""]
    for item in doc.get("bfms_emitted_language", []):
        lines.append(f"- {item['source']}: sha256 {item['sha256'][:12]}... `{_cell(item['excerpt'])}`")
    lines += ["", "## Findings touched", "", ", ".join(doc.get("findings_touched", [])) or "(none)"]
    lines += ["", "## Counts", ""]
    for key, value in sorted((doc.get("counts") or {}).items()):
        lines.append(f"- {key}: {value}")
    lines += ["", "## Forbidden scan", ""]
    for key, value in sorted((doc.get("forbidden_scan") or {}).items()):
        lines.append(f"- {key}: {value}")
    lines += ["", "## Lab statements", ""]
    lines += [f"- {s}" for s in doc.get("lab_statements", [])]
    lines += ["", "## Golden diff", ""]
    diffs = doc.get("golden_diff", [])
    lines += [f"- {_cell(d)}" for d in diffs] if diffs else ["(empty)"]
    lines += ["", f"content_hash: {doc.get('content_hash')}"]
    return "\n".join(lines)


def canonical(report: RunReport) -> str:
    return canonical_json(report.model_dump(mode="json", by_alias=True))


__all__ = [
    "EXPECTED_DIR",
    "GOLDEN_NAME",
    "KNOWN_GAPS_ACCEPTED",
    "KNOWN_GAP_KEYS",
    "REPORT_JSON",
    "REPORT_MD",
    "build",
    "canonical",
    "diff_against_expected",
    "emitted",
    "expected_path",
    "fail_keys",
    "golden_view",
    "load",
    "load_expected",
    "render_md",
    "smoke_gate",
    "verify",
    "write",
    "write_golden",
]
