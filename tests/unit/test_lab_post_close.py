"""Fence: the Obligation Register algorithm (`fulfillment/demo/run.py::build`) over the lab packs
(BUILD-SPEC 5 row S15, 6 row 21).

The demo module is loaded read-only by importlib with its module-level `ROOT` pointed at a
run-assembled directory (never `main()` / `render_html()`); the fulfillment tree hash is
proven unchanged; LAB01 equals the demo build row-for-row after the platform-token scrub;
LAB02 (`late_afs`) differs only where BUILD-SPEC 3.4 says.
"""

from __future__ import annotations

import ast
import shutil
from datetime import date
from pathlib import Path

from tests import lab_support

LAB = lab_support.LAB_ROOT
REPO = lab_support.REPO_ROOT
PACKS = LAB / "packs"
DEMO = REPO / "fulfillment" / "demo"
LAB01, LAB02 = "SYN-HSG-AZ-2025-LAB01", "SYN-HSG-AZ-2025-LAB02"
ASOF = date(2026, 9, 10)  # lab.asof literal of every committed scenario
AFS_ROWS = ("OB-01", "OB-09", "OB-10")


def _assemble(pack: Path, root: Path) -> Path:
    (root / "documents").mkdir(parents=True)
    (root / "vault").mkdir()
    for doc in sorted((pack / "closing-documents").glob("*.md")):
        shutil.copyfile(doc, root / "documents" / doc.name)
    shutil.copyfile(pack / "post-close" / "approved-inputs.csv", root / "approved-inputs.csv")
    for evidence in sorted((pack / "post-close" / "vault").glob("*.txt")):
        shutil.copyfile(evidence, root / "vault" / evidence.name)
    return root


def _scrub_all(scrub, value):
    if isinstance(value, str):
        return scrub(value)
    if isinstance(value, dict):
        return {k: _scrub_all(scrub, v) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return type(value)(_scrub_all(scrub, v) for v in value)
    return value


def _counts(result: dict, statuses) -> dict[str, int]:
    return {s: sum(1 for row in result["register"] if row["status"] == s) for s in statuses}


def test_lab_post_close_base_equivalence_and_late_afs(tmp_path: Path) -> None:
    lab_support.import_labkit()
    from labkit import generate_pack, law, provenance

    before = provenance.tree_sha256(REPO / "fulfillment")
    run = generate_pack.load_module(generate_pack.RUN_PY_PATH, "lab_fence_demo_run")
    assert tuple(run.STATUSES) == law.REGISTER_STATUSES and len(run.STATUSES) == 4

    run.ROOT = DEMO
    demo = _scrub_all(generate_pack.scrub_platform_token, run.build(ASOF))
    run.ROOT = _assemble(PACKS / LAB01, tmp_path / "lab01")
    lab01 = run.build(ASOF)
    run.ROOT = _assemble(PACKS / LAB02, tmp_path / "lab02")
    lab02 = run.build(ASOF)
    assert provenance.tree_sha256(REPO / "fulfillment") == before, "fulfillment/ tree changed during the build"
    assert (DEMO / "output" / "register.html").is_file()  # untouched demo output, never regenerated here

    for key in ("register", "calendar", "vault_index", "gaps", "open_items"):
        assert lab01[key] == demo[key], f"LAB01 {key} differs from the demo build after the scrub"
    assert not any(law.EMMA_WORD.search(str(row)) for row in lab01["register"])
    counts = _counts(lab01, run.STATUSES)
    assert counts == {"filed": 6, "not filed": 1, "evidence missing": 2, "not testable": 8}
    assert len(lab01["register"]) == 17 and len(lab01["gaps"]) == 2 and len(lab01["open_items"]) == 3
    assert all(v["bound_to"] != "UNBOUND" for v in lab01["vault_index"]) and len(lab01["vault_index"]) == 12
    assert {row["status"] for row in lab01["register"]} <= set(run.STATUSES)

    by_id_01 = {row["obligation_id"]: row for row in lab01["register"]}
    by_id_02 = {row["obligation_id"]: row for row in lab02["register"]}
    assert set(by_id_01) == set(by_id_02)
    for ob_id, row in by_id_02.items():
        if ob_id in AFS_ROWS:
            assert row["status"] == "evidence missing", f"{ob_id}: {row['status']}"
            assert by_id_01[ob_id]["status"] == "filed"
        else:
            assert row == by_id_01[ob_id], f"{ob_id} changed under late_afs"
    assert _counts(lab02, run.STATUSES) == {"filed": 3, "not filed": 1, "evidence missing": 5, "not testable": 8}
    assert len(lab02["gaps"]) == len(lab01["gaps"]) + 3
    assert len(lab02["vault_index"]) == len(lab01["vault_index"]) - 3
    assert {g[0] for g in lab02["gaps"]} - {g[0] for g in lab01["gaps"]} == set(AFS_ROWS)
    assert lab02["open_items"] == lab01["open_items"]
    assert {row["status"] for row in lab02["register"]} <= set(run.STATUSES)


def test_lab_post_close_never_renders_or_mains() -> None:
    path = LAB / "labkit" / "post_close.py"
    assert path.is_file(), "labkit/post_close.py not written yet (runner lane)"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    calls = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
            if name in ("render_html", "main"):
                calls.append(f"line {node.lineno}: {name}()")
    assert calls == [], f"post_close.py calls the demo's HTML/CLI entry points: {calls}"
    text = path.read_text(encoding="utf-8")
    assert "subprocess" not in text, "post_close.py must load run.py by importlib, not as a subprocess"
    assert "ROOT" in text and "importlib" in text
