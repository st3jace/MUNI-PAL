"""Fence: `lab/twin-bfms` is never importable from, mounted by, or deployed with `src/`.

BUILD-SPEC section 6, rows 1-3. Import boundary in the other direction (lab -> src) is
allowed only for services; engines, the LLM client, alembic and every send/deploy
library are fenced by a source scan (brief rule 5: no sizing / pricing / approval; rule 3:
TR-1, outputs never leave the build machine).
"""

from __future__ import annotations

import ast
import hashlib
import re
import sys
from pathlib import Path
from types import ModuleType

from tests import lab_support

REPO = lab_support.REPO_ROOT
LAB = lab_support.LAB_ROOT
SRC = REPO / "src" / "munipal"

_LAB_MARKERS = ("labkit", "twin-bfms", "twin_bfms", "lab/")
_ROUTE_MARKER = re.compile(r"(?<![a-z])(lab|twin)(?![a-z])", re.IGNORECASE)
_DEPLOY_MARKERS = ("lab/", "twin-bfms")
_BANNED_TEXT = (
    "munipal.engines",
    "deal_structuring",
    "bond_sizing",
    "import anthropic",
    "from anthropic",
    "import alembic",
    "from alembic",
)
_BANNED_IMPORT_ROOTS = frozenset(
    {"smtplib", "notion", "notion_client", "telegram", "linear", "resend", "sendgrid", "anthropic", "alembic"}
)


def _lab_py_files() -> list[Path]:
    return sorted(p for p in LAB.rglob("*.py") if "__pycache__" not in p.parts and "runs" not in p.relative_to(LAB).parts)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_lab_not_importable_from_src() -> None:
    hits = []
    for path in sorted(SRC.rglob("*.py")):
        text = _read(path)
        for marker in _LAB_MARKERS:
            if marker in text:
                hits.append(f"{path.relative_to(REPO).as_posix()}: {marker!r}")
    assert hits == [], f"src/munipal references the lab: {hits}"

    before = {m for m in sys.modules if m == "labkit" or m.startswith("labkit.")}
    import munipal.main  # noqa: F401
    import munipal.sensing_app  # noqa: F401

    after = {m for m in sys.modules if m == "labkit" or m.startswith("labkit.")}
    assert after == before, f"importing the apps pulled labkit in: {sorted(after - before)}"
    leaks = []
    for name, module in list(sys.modules.items()):
        if not (name == "munipal" or name.startswith("munipal.")) or module is None:
            continue
        for attr, value in vars(module).items():
            if isinstance(value, ModuleType):
                mod_name = value.__name__
            else:
                mod_name = getattr(value, "__module__", None)
            if isinstance(mod_name, str) and (mod_name == "labkit" or mod_name.startswith("labkit.")):
                leaks.append(f"{name}.{attr} -> {mod_name}")
    assert leaks == [], f"munipal modules hold labkit objects: {leaks}"
    assert "twin-bfms".isidentifier() is False


def test_lab_not_mounted_or_deployed() -> None:
    from munipal.main import app as bfms_app
    from munipal.sensing_app import app as sensing_app

    offending = []
    for label, application in (("munipal.main", bfms_app), ("munipal.sensing_app", sensing_app)):
        for route in application.routes:
            path = getattr(route, "path", "")
            if _ROUTE_MARKER.search(path):
                offending.append(f"{label}: {path}")
    assert offending == [], f"lab/twin route paths mounted: {offending}"

    deploy_files = [REPO / "railway.toml", REPO / "frontend" / "vercel.json"]
    deploy_files += sorted((REPO / "frontend").glob("vite.config*.ts"))
    deploy_files += sorted((REPO / ".github" / "workflows").glob("*"))
    hits = []
    for path in deploy_files:
        if not path.is_file():
            continue
        text = _read(path)
        for marker in _DEPLOY_MARKERS:
            if marker in text:
                hits.append(f"{path.relative_to(REPO).as_posix()}: {marker!r}")
    assert hits == [], f"deploy configuration names the lab: {hits}"

    contract = REPO / "contracts" / "openapi.v1.json"
    before = _sha(contract)
    labkit = lab_support.import_labkit()
    assert labkit.LAB_VERSION
    assert _sha(contract) == before, "importing labkit changed contracts/openapi.v1.json"


def _import_roots(tree: ast.Module) -> set[str]:
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            roots.add(node.module.split(".")[0])
    return roots


def _anthropic_client_lines(text: str) -> list[int]:
    return [i for i, line in enumerate(text.split("\n"), start=1) if "AnthropicClient" in line]


def _forbid_llm_span(tree: ast.Module) -> tuple[int, int] | None:
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and node.name == "forbid_llm":
            return node.lineno, node.end_lineno or node.lineno
    return None


def test_lab_never_calls_engines_llm_or_alembic() -> None:
    files = _lab_py_files()
    assert files, "no lab .py files found"
    problems = []
    for path in files:
        rel = path.relative_to(REPO).as_posix()
        text = _read(path)
        for marker in _BANNED_TEXT:
            if marker in text:
                problems.append(f"{rel}: spells {marker!r}")
        tree = ast.parse(text)
        banned = _import_roots(tree) & _BANNED_IMPORT_ROOTS
        if banned:
            problems.append(f"{rel}: imports {sorted(banned)}")
        client_lines = _anthropic_client_lines(text)
        if client_lines:
            if path.name != "harness.py":
                problems.append(f"{rel}: AnthropicClient outside harness.forbid_llm (lines {client_lines})")
            else:
                span = _forbid_llm_span(tree)
                outside = [n for n in client_lines if span is None or not (span[0] <= n <= span[1])]
                if outside:
                    problems.append(f"{rel}: AnthropicClient outside forbid_llm at lines {outside}")
    assert problems == [], problems
