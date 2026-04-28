#!/usr/bin/env python3
"""Count files in the Muni-Pal agent-safe source review scope."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

INCLUDED_PATHS = [
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

EXCLUDED_PATHS = [
    ".git",
    "node_modules",
    ".venv",
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
    "emma/emma_crawler",
    "emma/bond_os_extractor/data",
]
EXCLUDED_PARTS = {part for path in EXCLUDED_PATHS for part in Path(path).parts}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}


def is_excluded(path: Path, root: Path) -> bool:
    try:
        rel_parts = path.relative_to(root).parts
    except ValueError:
        return True
    return any(part in EXCLUDED_PARTS for part in rel_parts)


def iter_scoped_files(root: Path) -> list[str]:
    files: list[str] = []
    for rel in INCLUDED_PATHS:
        path = root / rel
        if not path.exists():
            continue
        if is_excluded(path, root):
            continue
        if path.is_file():
            if path.suffix not in EXCLUDED_SUFFIXES:
                files.append(path.relative_to(root).as_posix())
            continue
        for child in path.rglob("*"):
            if is_excluded(child, root):
                continue
            if child.is_file() and child.suffix not in EXCLUDED_SUFFIXES:
                files.append(child.relative_to(root).as_posix())
    return sorted(set(files))


def main() -> int:
    parser = argparse.ArgumentParser(description="Count files in the agent-safe source review scope.")
    parser.add_argument("--root", default=".", help="repository root, default: current directory")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    parser.add_argument("--sample", type=int, default=25, help="number of scoped paths to include in the sample")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    files = iter_scoped_files(root)
    missing = [rel for rel in INCLUDED_PATHS if not (root / rel).exists()]
    payload = {
        "root": str(root),
        "file_count": len(files),
        "included_paths": INCLUDED_PATHS,
        "excluded_paths": EXCLUDED_PATHS,
        "missing_paths": missing,
        "files_sample": files[: args.sample],
    }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"root: {payload['root']}")
        print(f"scoped_source_files: {payload['file_count']}")
        if missing:
            print("missing_scope_paths:")
            for rel in missing:
                print(f"- {rel}")
        print("included_paths:")
        for rel in INCLUDED_PATHS:
            print(f"- {rel}")
        print("excluded_paths:")
        for rel in EXCLUDED_PATHS:
            print(f"- {rel}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
