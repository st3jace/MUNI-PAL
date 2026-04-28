#!/usr/bin/env python3
"""Validate that Muni-Pal is being used from the canonical dev workspace.

This script is dependency-free so agents can run it before package installation.
It protects long-running agent sessions from slow or fragile OneDrive-backed WSL
paths and confirms scoped source traversal is safe before implementation work.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import time

DEFAULT_CANONICAL_ROOT = Path("/home/st3ja/Developer/MUNI-PAL")
SCOPED_PATHS = [
    "README.md",
    "PLAN.md",
    "pyproject.toml",
    "uv.lock",
    "docker-compose.yml",
    "docker-compose.prod.yml",
    "docker-compose.sensing.yml",
    "railway.toml",
    ".env.example",
    ".env.sensing.example",
    "frontend/package.json",
    "src",
    "frontend/src",
    "tests",
    "contracts",
    "alembic/versions",
    "scripts",
    "docs",
]
EXCLUDED_PARTS = {
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "Bond Facility Development",
    "V1",
    "V2",
    "artifacts",
    "data",
    "files",
    "pdfs",
    "images",
    "logs",
    ".gstack",
    ".vercel",
}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}


def run(cmd: list[str], cwd: Path, timeout: int) -> tuple[bool, str, float]:
    start = time.monotonic()
    try:
        result = subprocess.run(
            cmd,
            cwd=str(cwd),
            text=True,
            capture_output=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return False, f"timeout after {timeout}s", time.monotonic() - start
    elapsed = time.monotonic() - start
    output = (result.stdout + result.stderr).strip()
    return result.returncode == 0, output, elapsed


def find_repo_root(start: Path) -> Path:
    ok, output, _ = run(["git", "rev-parse", "--show-toplevel"], start, timeout=10)
    if ok and output:
        return Path(output.splitlines()[0]).resolve()
    for candidate in [start, *start.parents]:
        if (candidate / ".git").exists():
            return candidate.resolve()
    return start.resolve()


def is_onedrive_or_windows_mount(path: Path) -> bool:
    normalized = str(path).replace("\\", "/").lower()
    return "/mnt/c/" in normalized or "onedrive" in normalized


def scoped_file_count(root: Path) -> tuple[int, int]:
    files = 0
    missing = 0
    for rel in SCOPED_PATHS:
        path = root / rel
        if not path.exists():
            missing += 1
            continue
        if path.is_file():
            files += 1
            continue
        for child in path.rglob("*"):
            rel_parts = child.relative_to(root).parts
            if any(part in EXCLUDED_PARTS for part in rel_parts):
                continue
            if child.is_file() and child.suffix not in EXCLUDED_SUFFIXES:
                files += 1
    return files, missing


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Muni-Pal development workspace health.")
    parser.add_argument("--warn-only", action="store_true", help="print failures but exit 0")
    parser.add_argument(
        "--canonical-root",
        default=os.environ.get("MUNIPAL_CANONICAL_ROOT", str(DEFAULT_CANONICAL_ROOT)),
        help="expected native WSL checkout path",
    )
    args = parser.parse_args()

    cwd = Path.cwd().resolve()
    root = find_repo_root(cwd)
    canonical = Path(args.canonical_root).resolve()
    failures: list[str] = []

    print(f"cwd: {cwd}")
    print(f"repo_root: {root}")
    print(f"expected_canonical_root: {canonical}")

    if root != canonical:
        failures.append(f"repo root is not the canonical native WSL path: {canonical}")
    if is_onedrive_or_windows_mount(root):
        failures.append("repo root is on OneDrive or /mnt/c; use native WSL checkout for active engineering")

    ok, output, elapsed = run(["git", "rev-parse", "--show-toplevel"], root, timeout=10)
    print(f"git_rev_parse_ok: {ok} ({elapsed:.2f}s)")
    if not ok:
        failures.append(f"git rev-parse failed: {output}")

    ok, output, elapsed = run(["git", "status", "--short", "--branch", "--untracked-files=no"], root, timeout=15)
    print(f"git_status_ok: {ok} ({elapsed:.2f}s)")
    if not ok:
        failures.append(f"git status did not complete quickly: {output}")

    start = time.monotonic()
    try:
        count, missing = scoped_file_count(root)
        elapsed = time.monotonic() - start
        print(f"scoped_source_files: {count}")
        print(f"scoped_missing_paths: {missing}")
        print(f"scoped_traversal_seconds: {elapsed:.2f}")
        if count == 0:
            failures.append("scoped source traversal found no files")
        if elapsed > 10:
            failures.append("scoped source traversal was slow; check filesystem placement and exclusions")
    except Exception as exc:
        failures.append(f"scoped source traversal failed: {exc}")

    if failures:
        print("status: FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 0 if args.warn_only else 1

    print("status: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
