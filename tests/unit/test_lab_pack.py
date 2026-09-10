"""Fence: the committed synthetic packs (BUILD-SPEC 4, 6 rows 12-16).

Legend + envelope by construction, determinism, manifest completeness, rules-extractor
readability (per artifact, critic M4), playbook request mapping, and reuse of the demo
constants (closing documents, approved inputs, vault) with the platform-token scrubs.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

from tests import lab_support

LAB = lab_support.LAB_ROOT
REPO = lab_support.REPO_ROOT
PACKS = LAB / "packs"
DEAL_IDS = ("SYN-HSG-AZ-2025-LAB01", "SYN-HSG-AZ-2025-LAB02", "SYN-HSG-AZ-2025-LAB03")
_LEGEND_TRIPLE_LEN = 3


def _scenario_path(deal_id: str) -> Path:
    return LAB / "scenarios" / f"{deal_id}.synthetic.json"


def _files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*") if p.is_file())


def _rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").split("\n")


def _md_body(path: Path, legend: str) -> str:
    """Body of a lab `.md`: after frontmatter + first legend blockquote, before the last legend."""
    lines = _lines(path)
    assert lines[0] == "---"
    end = lines.index("---", 1)
    rest = lines[end + 1 :]
    assert rest[:3] == ["", f"> {legend}", ""], "legend is not the first blockquote"
    body = rest[3:]
    assert body[-1] == "" and body[-2] == legend, "legend is not the last line"
    body = body[:-3]
    out: list[str] = []
    i = 0
    while i < len(body):
        if body[i : i + _LEGEND_TRIPLE_LEN] == ["", f"> {legend}", ""]:
            i += _LEGEND_TRIPLE_LEN
            continue
        out.append(body[i])
        i += 1
    return "\n".join(out)


def test_lab_legend_and_envelope_by_construction(tmp_path: Path) -> None:
    lab_support.import_labkit()
    from labkit import generate_pack, law, provenance

    result = generate_pack.generate(_scenario_path(DEAL_IDS[0]), tmp_path)
    root = result.pack_root
    files = _files(root)
    assert len(files) == result.files_written + 1  # + PACK-MANIFEST.json
    problems: list[str] = []
    for path in files:
        rel = _rel(path, root)
        assert path.suffix in law.ALLOWED_EXTENSIONS, rel
        assert not (set(path.relative_to(root).parts[:-1]) & law.IGNORED_DIR_NAMES), rel
        assert path.name.isascii(), rel
        allowed = 1 if rel == "closing-documents/03-continuing-disclosure-agreement.md" else 0
        problems += [f"{rel}: {p}" for p in provenance.audit_file(path, emma_allowed=allowed)]
        lines = _lines(path)
        if path.suffix == ".md":
            assert lines[0] == "---" and "sha256_body: " in "\n".join(lines[:10]), rel
            assert f"> {law.LEGEND}" in lines, rel
            assert lines[-2] == law.LEGEND and lines[-1] == "", rel
        elif path.suffix == ".txt" and rel.startswith("intake/"):
            assert lines[0] == "# source: synthetic", rel
            assert lines[7] == law.LEGEND, rel
            assert any(line.startswith("# created_from: ") for line in lines[:7]), rel
        elif path.suffix == ".txt":
            assert rel.startswith("post-close/vault/"), rel
            assert lines[0].startswith("SYNTHETIC EVIDENCE FILE - "), rel
            assert lines[1] == law.LEGEND, rel
            assert lines[2] == "# source: synthetic", rel
        elif path.suffix == ".json":
            doc = json.loads(path.read_text(encoding="utf-8"))
            assert doc["_legend"] == law.LEGEND and doc["_provenance"]["source"] == "synthetic", rel
            assert doc["_provenance"]["scenario_id"] == DEAL_IDS[0], rel
        elif path.suffix == ".csv":
            assert path.with_name(path.name + law.CSV_SIDECAR_SUFFIX).is_file(), rel
    assert problems == [], problems


def test_lab_pack_determinism_and_manifest(tmp_path: Path) -> None:
    lab_support.import_labkit()
    from labkit import generate_pack, law, provenance

    pins = json.loads((PACKS / "_pins.json").read_text(encoding="utf-8"))
    first = generate_pack.generate(_scenario_path(DEAL_IDS[0]), tmp_path / "a")
    second = generate_pack.generate(_scenario_path(DEAL_IDS[0]), tmp_path / "b")
    assert provenance.tree_sha256(first.pack_root) == provenance.tree_sha256(second.pack_root)
    assert first.manifest_sha256 == second.manifest_sha256

    for deal_id in DEAL_IDS:
        committed = PACKS / deal_id
        regenerated = generate_pack.generate(_scenario_path(deal_id), tmp_path / "c").pack_root
        assert provenance.tree_sha256(committed) == provenance.tree_sha256(regenerated), f"{deal_id}: committed pack drifted"
        assert pins["pack_manifest_sha256"][deal_id] == _sha(committed / law.PACK_MANIFEST_NAME)

        manifest = json.loads((committed / law.PACK_MANIFEST_NAME).read_text(encoding="utf-8"))
        listed = {entry["path"]: entry for entry in manifest["files"]}
        on_disk = {_rel(p, committed) for p in _files(committed)} - {law.PACK_MANIFEST_NAME}
        assert set(listed) == on_disk, f"{deal_id}: manifest/disk mismatch {set(listed) ^ on_disk}"
        for rel, entry in listed.items():
            assert entry["sha256"] == _sha(committed / rel), f"{deal_id}: {rel} sha256 drift"
            assert isinstance(entry["created_from"], list) and entry["created_from"], f"{deal_id}: {rel} lacks created_from"
        absent = manifest["absent_by_scenario"]
        assert all(entry["status"] == "absent_by_scenario" and entry["reason"] for entry in absent)
        by_type = {entry.get("type") for entry in absent}
        assert {"form_8038", "plom", "limited_offering_memorandum", "investor_letters", "closing_memo", "signature_pages"} <= by_type
        assert any(e.get("obligation_id") == "OB-14" for e in absent), f"{deal_id}: rebate certificate absence not recorded"
        vault_absent = {e["vault_file"] for e in absent if e.get("vault_file")}
        if deal_id == DEAL_IDS[1]:
            for stem in ("afs-FY2025", "annual-report-FY2025", "dscr-calc-FY2025"):
                assert f"post-close/vault/{stem}.txt" in vault_absent, f"{deal_id}: {stem} absence not recorded"
                assert not (committed / "post-close" / "vault" / f"{stem}.txt").exists()
            assert len(list((committed / "post-close" / "vault").glob("*.txt"))) == 9
        else:
            assert len(list((committed / "post-close" / "vault").glob("*.txt"))) == 12
        if deal_id == DEAL_IDS[2]:
            assert any(e.get("artifact_key") == "site_control_permits" for e in absent)
            assert not (committed / "intake" / "03_DUE-DILIGENCE" / "site_control_permits.txt").exists()
            assert len(list((committed / "intake").rglob("*.txt"))) == 4
        else:
            assert len(list((committed / "intake").rglob("*.txt"))) == 5


def test_lab_intake_readable_by_rules_extractor() -> None:
    lab_support.import_labkit()
    from labkit import generate_pack, law, scenario

    from munipal.services.extraction.rules_based_extractor import RulesBasedExtractor

    extractor = RulesBasedExtractor()
    for deal_id in DEAL_IDS:
        sc = scenario.load(_scenario_path(deal_id))
        pack = PACKS / deal_id
        manifest = json.loads((pack / "intake" / "intake-manifest.json").read_text(encoding="utf-8"))
        assert manifest["self_check"]["result"] == "pass"
        assert manifest["self_check"]["mode"].startswith("per-artifact")
        order = manifest["upload_order"]
        assert [e["order"] for e in order] == list(range(1, len(order) + 1))
        assert [e["artifact_key"] for e in order] == list(sc.intake_docs)
        for entry in order:
            path = pack / entry["path"]
            text = path.read_text(encoding="utf-8")
            assert _sha(path) == entry["sha256"]
            assert law.LEGEND in text and "# scenario_id: " in text
            expected = entry["expected_paths"]
            assert expected == sc.intake_docs[entry["artifact_key"]]
            facts = extractor.extract([{"id": entry["path"], "text_content": text}], expected)
            by_path: dict[str, list] = {}
            for fact in facts:
                by_path.setdefault(fact.schema_path, []).append(fact)
            for schema_path in expected:
                got = by_path.get(schema_path, [])
                assert len(got) == 1, f"{deal_id}/{entry['path']}: {schema_path} -> {len(got)} facts"
                want = generate_pack.expected_value(schema_path, sc.intake_facts[schema_path])
                assert got[0].value == want, f"{deal_id}/{entry['path']}: {schema_path} -> {got[0].value!r} != {want!r}"
                assert got[0].confidence == 0.72
                assert entry["labels"][schema_path] == generate_pack.label_for(schema_path)
                assert entry["labels"][schema_path].lower() in generate_pack.labels_for(schema_path)
        assert sorted(sc.dropped_intake_paths) == sorted(p for d in manifest["dropped"] for p in d["paths"])


def test_lab_intake_matches_playbook_request() -> None:
    lab_support.import_labkit()
    from labkit import scenario

    from munipal.services.pilot_onboarding import (
        _OPERATOR_WORKSPACE_FOLDERS,
        build_pilot_onboarding_workflow,
    )
    from munipal.services.readiness_service import SECTOR_READINESS_PROFILES
    from munipal.services.sector_playbooks import _HOUSING_FACT_ARTIFACTS

    workflow = build_pilot_onboarding_workflow("housing")
    key_by_display = {a.display_name: a.artifact_key for a in workflow.playbook.required_artifacts}
    requested = []
    for item in workflow.document_request_list:
        display, _, level = item.rpartition(" (")
        assert level.rstrip(")") in ("required", "recommended"), item
        assert display in key_by_display, item
        requested.append(key_by_display[display])
    assert len(requested) == len(set(requested))

    for deal_id in DEAL_IDS:
        sc = scenario.load(_scenario_path(deal_id))
        pack = PACKS / deal_id
        manifest = json.loads((pack / "intake" / "intake-manifest.json").read_text(encoding="utf-8"))
        present = {e["artifact_key"]: e for e in manifest["upload_order"]}
        dropped = {d["artifact_key"] for d in manifest["dropped"]}
        assert set(present) | dropped == set(requested), f"{deal_id}: request list and intake keys differ"
        assert dropped == set(sc.dropped_artifacts)
        assert set(manifest["workspace_folders"]) == set(_OPERATOR_WORKSPACE_FOLDERS)
        for entry in present.values():
            assert entry["folder"] in _OPERATOR_WORKSPACE_FOLDERS
            assert entry["path"].split("/")[1] == entry["folder"]
        checklist = (pack / "intake" / "00_WELCOME" / "document-request-checklist.md").read_text(encoding="utf-8")
        for item in workflow.document_request_list:
            assert item in checklist, f"{deal_id}: checklist lacks {item!r}"
        if deal_id != DEAL_IDS[2]:
            label_lines = {
                schema_path: (pack / e["path"]).read_text(encoding="utf-8")
                for e in present.values()
                for schema_path in e["expected_paths"]
            }
            for schema_path, keys in _HOUSING_FACT_ARTIFACTS.items():
                assert schema_path in present[keys[0]]["expected_paths"], f"{schema_path} not in {keys[0]}"
                assert f"{present[keys[0]]['labels'][schema_path]}: " in label_lines[schema_path]
            profile = SECTOR_READINESS_PROFILES["housing_affordable_multifamily"]
            for dim in profile["dimensions"].values():
                for schema_path in dim["contributing_paths"]:
                    assert schema_path in label_lines, f"readiness path {schema_path} has no intake line"
                    entry = next(e for e in present.values() if schema_path in e["expected_paths"])
                    assert f"{entry['labels'][schema_path]}: " in label_lines[schema_path]


def test_lab_closing_docs_and_post_close_reuse_demo_constants() -> None:
    lab_support.import_labkit()
    from labkit import generate_pack, law

    bf, run = generate_pack.demo_modules()
    pins = json.loads((PACKS / "_pins.json").read_text(encoding="utf-8"))
    assert pins["run_py_sha256"] == _sha(generate_pack.RUN_PY_PATH), "fulfillment/demo/run.py drifted; regenerate packs deliberately"
    assert pins["build_fixtures_sha256"] == _sha(generate_pack.BUILD_FIXTURES_PATH), "build_fixtures.py drifted"
    assert pins["bondi_format_json_sha256"] == _sha(generate_pack.FORMAT_JSON_PATH)
    assert tuple(run.STATUSES) == law.REGISTER_STATUSES

    for deal_id in DEAL_IDS:
        pack = PACKS / deal_id
        for name, body in bf.DOCUMENTS.items():
            path = pack / "closing-documents" / name
            assert path.is_file(), f"{deal_id}: {name} missing"
            expected_body = body.rstrip("\n")
            assert _md_body(path, law.LEGEND) == expected_body, f"{deal_id}: {name} body differs from DOCUMENTS"
            frontmatter = "\n".join(_lines(path)[:12])
            assert f"sha256_body: {hashlib.sha256(expected_body.encode('utf-8')).hexdigest()}" in frontmatter
        assert {p.name for p in (pack / "closing-documents").glob("*.md")} == set(bf.DOCUMENTS)

        with (pack / "post-close" / "approved-inputs.csv").open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            assert reader.fieldnames == list(bf.APPROVED_FIELDS)
            rows = list(reader)
        expected_rows = []
        for raw in bf.APPROVED:
            rec = dict(zip(bf.APPROVED_FIELDS, raw, strict=True))
            rec["obligation"] = generate_pack.scrub_platform_token(rec["obligation"])
            rec["recipient"] = generate_pack.scrub_platform_token(rec["recipient"])
            expected_rows.append(rec)
        assert rows == expected_rows, f"{deal_id}: approved-inputs rows differ from APPROVED after the two scrubs"
        scrubbed = sum(1 for raw, rec in zip(bf.APPROVED, expected_rows, strict=True) if dict(zip(bf.APPROVED_FIELDS, raw, strict=True)) != rec)
        assert scrubbed >= 5, "the scrub touched fewer rows than the demo's platform-token rows"

        assert _md_body(pack / "post-close" / bf.REF, law.LEGEND) == bf.APPROVAL_NOTE.rstrip("\n")

        vault = pack / "post-close" / "vault"
        by_name = {fname: (title, filed, recipient) for fname, title, filed, recipient in bf.VAULT}
        for path in sorted(vault.glob("*.txt")):
            assert path.name in by_name, f"{deal_id}: vault file {path.name} not in build_fixtures.VAULT"
            title, filed, recipient = by_name[path.name]
            lines = _lines(path)
            assert lines[0] == f"SYNTHETIC EVIDENCE FILE - {title}"
            assert lines[1] == law.LEGEND
            body = [line for line in lines[2:] if line and not line.startswith("# ")]
            assert body == [f"Filed/delivered: {filed}", f"Recipient: {generate_pack.scrub_platform_token(recipient)}"], path.name
        if deal_id != DEAL_IDS[1]:
            assert {p.name for p in vault.glob("*.txt")} == set(by_name)
