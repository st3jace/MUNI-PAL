"""Post-close Obligation Register stage (BUILD-SPEC 5, row S15; spec 2.3).

The sellable algorithm lives in `fulfillment/demo/run.py::build()`. It reads three things
from its module-level `ROOT`: `approved-inputs.csv`, `vault/` (evidence files, line 1 is
the label) and `documents/*.md` (for `find_candidates`). The lab loads that file with
importlib (never as a script, never through the demo's CLI entry point or its HTML
renderer), points `ROOT` at a directory assembled from the pack under `runs/<run_id>/`,
and calls `build(asof)` with the scenario's `lab.asof` literal.

Outputs are written with the demo's own `write_csv` (register / calendar / vault-index /
open-items / candidates) plus a provenance sidecar per csv, and the lab's markdown views
(`gaps.md`, `open-items.md`) and `summary.json` through `labkit.provenance`.

`demo_build(asof)` runs the same function with `ROOT = fulfillment/demo` for the
base-equivalence row; the demo's rows are scrubbed of the MSRB platform token on the
`obligation` / `recipient` columns exactly as the generator scrubbed the pack. The
`fulfillment/` tree is hashed before and after; a change is a fail.
"""

from __future__ import annotations

import importlib.util
import json
import re
import shutil
import sys
from dataclasses import dataclass, field
from datetime import date as _date
from pathlib import Path
from types import ModuleType
from typing import Any

from labkit import law
from labkit.provenance import (
    canonical_json,
    sha256_bytes,
    sha256_file,
    tree_sha256,
    write_json,
    write_md,
)
from labkit.types import Envelope

REPO_ROOT: Path = law.LAB_ROOT.parents[1]
FULFILLMENT_DIR: Path = REPO_ROOT / "fulfillment"
DEMO_DIR: Path = FULFILLMENT_DIR / "demo"
RUN_PY_PATH: Path = DEMO_DIR / "run.py"
REGISTER_ROOT_NAME = "register-root"
REGISTER_OUT_NAME = "register-out"
SCRUB_COLUMNS: tuple[str, ...] = ("obligation", "recipient")
COMPARED_KEYS: tuple[str, ...] = ("register", "calendar", "vault_index", "gaps", "open_items")

_VIA_TOKEN_RE = re.compile(r" via " + law.EMMA_WORD.pattern)
_PAREN_TOKEN_RE = re.compile(r"\s*\(" + law.EMMA_WORD.pattern + r"\)")


class PostCloseError(ValueError):
    """The stage cannot proceed (missing pack input, demo drift, fifth status)."""


def scrub_platform_token(text: str) -> str:
    """Same mechanical scrub as the generator: ` via <token>` and ` (<token>)`."""
    return _PAREN_TOKEN_RE.sub("", _VIA_TOKEN_RE.sub("", text))


# --------------------------------------------------------------------------------------
# Gate
# --------------------------------------------------------------------------------------


def gate(deal_status: str, closing_fired: bool) -> tuple[str, str]:
    """`(status, reason)`: not_applicable when the close is not carried; else pass."""
    if deal_status in law.HOLD_STATUSES:
        return "not_applicable", f"deal_status={deal_status}; close not invented; no register"
    if not closing_fired:
        return "not_applicable", "closing event not fired in the event log; close not invented; no register"
    return "pass", ""


# --------------------------------------------------------------------------------------
# Loading run.py read-only
# --------------------------------------------------------------------------------------


def load_run_module(root: Path, name: str = "lab_demo_run") -> ModuleType:
    """Fresh import of run.py with `ROOT` overridden; bytecode is never written."""
    spec = importlib.util.spec_from_file_location(name, RUN_PY_PATH)
    if spec is None or spec.loader is None:
        raise PostCloseError(f"cannot import {RUN_PY_PATH}")
    module = importlib.util.module_from_spec(spec)
    previous = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    if tuple(getattr(module, "STATUSES", ())) != law.REGISTER_STATUSES:
        raise PostCloseError(f"run.py STATUSES {getattr(module, 'STATUSES', None)!r} != the four lab statuses")
    module.ROOT = Path(root)
    return module


# --------------------------------------------------------------------------------------
# Assembly
# --------------------------------------------------------------------------------------


def assemble(pack_root: Path, run_dir: Path) -> Path:
    """`runs/<run_id>/register-root/{documents,vault,approved-inputs.csv}` from the pack."""
    pack_root = Path(pack_root)
    root = Path(run_dir) / REGISTER_ROOT_NAME
    if root.exists():
        shutil.rmtree(root)
    (root / "documents").mkdir(parents=True)
    (root / "vault").mkdir(parents=True)
    docs = sorted((pack_root / "closing-documents").glob("*.md"))
    if not docs:
        raise PostCloseError("pack carries no closing-documents/*.md")
    for doc in docs:
        shutil.copyfile(doc, root / "documents" / doc.name)
    approved = pack_root / "post-close" / "approved-inputs.csv"
    if not approved.is_file():
        raise PostCloseError("pack carries no post-close/approved-inputs.csv")
    shutil.copyfile(approved, root / "approved-inputs.csv")
    vault_dir = pack_root / "post-close" / "vault"
    if vault_dir.is_dir():
        for evidence in sorted(vault_dir.glob("*.txt")):
            shutil.copyfile(evidence, root / "vault" / evidence.name)
    return root


# --------------------------------------------------------------------------------------
# Build + write
# --------------------------------------------------------------------------------------


@dataclass
class RegisterRun:
    result: dict[str, Any]
    register_root: Path
    out_dir: Path
    status_counts: dict[str, int]
    written: list[str] = field(default_factory=list)
    fifth_status: list[str] = field(default_factory=list)

    @property
    def summary(self) -> dict[str, Any]:
        r = self.result
        return {
            "asof": r["asof"],
            "obligations": len(r["register"]),
            "status_counts": dict(self.status_counts),
            "calendar_rows": len(r["calendar"]),
            "gaps": len(r["gaps"]),
            "open_items": len(r["open_items"]),
            "vault_files": len(r["vault_index"]),
            "unbound_vault_files": [v["file"] for v in r["vault_index"] if v["bound_to"] == "UNBOUND"],
            "candidates": len(r["candidates"]),
        }


def _counts(result: dict[str, Any]) -> tuple[dict[str, int], list[str]]:
    counts = dict.fromkeys(law.REGISTER_STATUSES, 0)
    fifth: list[str] = []
    for row in result["register"]:
        st = row["status"]
        if st in counts:
            counts[st] += 1
        else:
            fifth.append(st)
    for row in result["calendar"]:
        if row["status"] not in counts:
            fifth.append(row["status"])
    return counts, fifth


def build_register(register_root: Path, asof: _date) -> tuple[ModuleType, dict[str, Any]]:
    module = load_run_module(register_root)
    result = module.build(asof)
    return module, result


def _csv_sidecar(path: Path, envelope: Envelope, rows: int, columns: list[str]) -> Path:
    sidecar = path.with_name(path.name + law.CSV_SIDECAR_SUFFIX)
    payload = {
        "for_file": path.name,
        "columns": list(columns),
        "rows": rows,
        "sha256": sha256_file(path),
        "writer": "fulfillment/demo/run.py::write_csv (the demo's own writer; sidecar by the lab)",
    }
    write_json(sidecar, payload, envelope)
    return sidecar


def run_register(pack_root: Path, run_dir: Path, asof_literal: str, envelope: Envelope) -> RegisterRun:
    """Assemble, build with the scenario asof literal, write outputs, count statuses."""
    asof = _date.fromisoformat(asof_literal)
    register_root = assemble(pack_root, run_dir)
    module, result = build_register(register_root, asof)
    counts, fifth = _counts(result)
    out = Path(run_dir) / REGISTER_OUT_NAME
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    env = envelope.model_copy(update={"created_from": ["fulfillment/demo/run.py::build over runs/<run_id>/register-root"]})
    written: list[str] = []

    def _csv(name: str, rows: list[dict[str, Any]], fields: list[str]) -> None:
        path = out / name
        module.write_csv(path, rows, fields)
        text = path.read_bytes().decode("utf-8")
        if law.forbidden_token_hits(text) or law.EMMA_WORD.search(text):
            raise PostCloseError(f"{name}: forbidden token in register output")
        _csv_sidecar(path, env, len(rows), fields)
        written.extend([name, name + law.CSV_SIDECAR_SUFFIX])

    reg_fields = list(result["register"][0].keys()) if result["register"] else ["obligation_id"]
    _csv("register.csv", result["register"], reg_fields)
    cal_fields = list(result["calendar"][0].keys()) if result["calendar"] else ["due_date"]
    _csv("calendar.csv", result["calendar"], cal_fields)
    _csv("vault-index.csv", result["vault_index"], ["file", "label", "bound_to"])
    _csv("open-items.csv", result["open_items"], ["requested_on", "requested_from", "item", "source_document", "clause", "what_was_asked"])
    _csv("candidates.csv", result["candidates"], ["source_document", "clause", "heading", "duty_phrase", "snippet"])

    gaps_lines = [
        "# Gap list (observational)",
        "",
        f"As of {result['asof']}. An approved undertaking names a deliverable and no file is present in the vault.",
        "",
    ]
    gaps_lines += [f"- **{g[0]}** {g[1]} - due {g[2]} - {g[4]} {g[3]} - expected `{g[5]}*`" for g in result["gaps"]]
    if not result["gaps"]:
        gaps_lines.append("(none)")
    write_md(out / "gaps.md", "\n".join(gaps_lines), env)
    written.append("gaps.md")
    open_lines = ["# Items awaiting input", "", "Requested in writing; no written instruction received. Sorted by request date.", ""]
    open_lines += [
        f"- {x['requested_on']} -> {x['requested_from']}: **{x['item']}** ({x['source_document']} {x['clause']}). {x['what_was_asked']}"
        for x in result["open_items"]
    ]
    if not result["open_items"]:
        open_lines.append("(none)")
    write_md(out / "open-items.md", "\n".join(open_lines), env)
    written.append("open-items.md")

    run = RegisterRun(result=result, register_root=register_root, out_dir=out, status_counts=counts, written=written, fifth_status=fifth)
    write_json(out / "summary.json", run.summary, env)
    run.written.append("summary.json")
    return run


# --------------------------------------------------------------------------------------
# Base equivalence against the demo
# --------------------------------------------------------------------------------------


def demo_build(asof_literal: str) -> dict[str, Any]:
    """`run.py::build` with `ROOT = fulfillment/demo`, rows scrubbed like the pack."""
    module, result = build_register(DEMO_DIR, _date.fromisoformat(asof_literal))
    for key in ("register", "calendar"):
        for row in result[key]:
            for col in SCRUB_COLUMNS:
                if col in row:
                    row[col] = scrub_platform_token(row[col])
    for item in result["open_items"]:
        item["item"] = scrub_platform_token(item["item"])
    return result


def _normalise(value: Any) -> Any:
    if isinstance(value, tuple):
        return list(value)
    return value


def compare(lab: dict[str, Any], demo: dict[str, Any]) -> list[str]:
    """Row-for-row differences on the compared keys (empty == equivalent)."""
    diffs: list[str] = []
    for key in COMPARED_KEYS:
        a = [_normalise(x) for x in lab.get(key, [])]
        b = [_normalise(x) for x in demo.get(key, [])]
        if len(a) != len(b):
            diffs.append(f"{key}: {len(a)} rows vs demo {len(b)}")
            continue
        for i, (x, y) in enumerate(zip(a, b, strict=True)):
            if x != y:
                diffs.append(f"{key}[{i}]: {json.dumps(x, sort_keys=True, default=str)[:160]} != {json.dumps(y, sort_keys=True, default=str)[:160]}")
    return diffs


def fulfillment_tree_sha256() -> str:
    return tree_sha256(FULFILLMENT_DIR, ignore_dirs=frozenset({"__pycache__"}))


def run_py_sha256() -> str:
    return sha256_file(RUN_PY_PATH)


def result_sha256(result: dict[str, Any]) -> str:
    return sha256_bytes(canonical_json({k: [_normalise(x) for x in result[k]] for k in COMPARED_KEYS}).encode("utf-8"))


__all__ = [
    "COMPARED_KEYS",
    "DEMO_DIR",
    "FULFILLMENT_DIR",
    "REGISTER_OUT_NAME",
    "REGISTER_ROOT_NAME",
    "RUN_PY_PATH",
    "PostCloseError",
    "RegisterRun",
    "assemble",
    "build_register",
    "compare",
    "demo_build",
    "fulfillment_tree_sha256",
    "gate",
    "load_run_module",
    "result_sha256",
    "run_py_sha256",
    "run_register",
    "scrub_platform_token",
]
