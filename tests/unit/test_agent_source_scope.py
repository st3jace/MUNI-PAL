from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_agent_source_scope_docs_name_included_and_excluded_paths() -> None:
    policy = (ROOT / "docs/development/CANONICAL_DEV_PATH.md").read_text(encoding="utf-8")

    for included in [
        "src/",
        "frontend/src/",
        "tests/",
        "contracts/",
        "alembic/versions/",
        "scripts/",
        "docs/",
        "pyproject.toml",
        "uv.lock",
    ]:
        assert included in policy

    for excluded in [
        ".git/",
        "node_modules/",
        ".venv/",
        "Bond Facility Development/",
        "V1/",
        "V2/",
        "artifacts/",
        "data/",
        "files/",
        "pdfs/",
        "images/",
        "logs/",
    ]:
        assert excluded in policy


def test_source_scope_count_command_reports_json_without_excluded_paths() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/count_source_scope.py", "--json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    payload = json.loads(result.stdout)

    assert payload["file_count"] > 0
    assert "src" in payload["included_paths"]
    assert "frontend/src" in payload["included_paths"]
    assert "V1" in payload["excluded_paths"]
    assert "V2" in payload["excluded_paths"]
    assert not any(path.startswith(("V1/", "V2/", "node_modules/", ".git/")) for path in payload["files_sample"])


def test_agent_start_here_names_source_scope_count_command() -> None:
    start_here = (ROOT / "docs/agent_ops/START_HERE.md").read_text(encoding="utf-8")

    assert "python scripts/count_source_scope.py --json" in start_here
    assert "do not do whole-repo traversal" in start_here
