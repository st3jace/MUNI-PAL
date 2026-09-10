"""The ONLY bridge from the test suite to `lab/twin-bfms`.

Usage in a lab fence test (critic M12: `tests/` is a package, so import it as a module
of that package; keep `labkit` imports out of the top import block):

    from tests import lab_support  # noqa: F401

    def test_something():
        labkit = lab_support.import_labkit()
        law = labkit.law

`lab/` is never importable from `src/munipal`; this shim is the one place that puts the
program folder on `sys.path`.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from types import ModuleType

REPO_ROOT: Path = Path(__file__).resolve().parents[1]
LAB_ROOT: Path = REPO_ROOT / "lab" / "twin-bfms"


def ensure_lab_on_path() -> Path:
    """Insert `<repo>/lab/twin-bfms` at the front of `sys.path` (idempotent)."""
    lab = str(LAB_ROOT)
    if lab not in sys.path:
        sys.path.insert(0, lab)
    return LAB_ROOT


def import_labkit() -> ModuleType:
    """Import `labkit` with its `law`, `types` and `provenance` submodules loaded."""
    ensure_lab_on_path()
    labkit = importlib.import_module("labkit")
    for name in ("law", "types", "provenance"):
        importlib.import_module(f"labkit.{name}")
    return labkit


ensure_lab_on_path()
