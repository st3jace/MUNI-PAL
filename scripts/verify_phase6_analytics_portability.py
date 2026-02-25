"""
Verify analytics engine source files avoid machine-specific hardcoded paths.

Usage:
    python scripts/verify_phase6_analytics_portability.py
    python scripts/verify_phase6_analytics_portability.py --fail-on-hardcoded
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass
class PathFinding:
    file: str
    line: int
    rule_id: str
    snippet: str


@dataclass
class PortabilityResult:
    report_json_path: Path
    report_md_path: Path
    status: str
    finding_count: int
    findings: list[PathFinding]


WINDOWS_DRIVE_PATTERN = re.compile(
    r"""(?:^|[\s'"(=])([A-Za-z]:[\\/][^'"`\s\)]+)"""
)
UNIX_MACHINE_PATTERN = re.compile(
    r"""(?:^|[\s'"(=])(\/(?:Users|home|opt|var|tmp)\/[^'"`\s\)]+)"""
)
ONEDRIVE_PATTERN = re.compile(r"""(?:^|[\s'"(=])(OneDrive[\\/][^'"`\s\)]+)""", re.IGNORECASE)

RULES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("windows_drive_path", WINDOWS_DRIVE_PATTERN),
    ("unix_machine_path", UNIX_MACHINE_PATTERN),
    ("onedrive_path", ONEDRIVE_PATTERN),
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _default_source_root() -> Path:
    return _repo_root() / "emma" / "bond_os_extractor" / "src"


def _default_reports_dir() -> Path:
    return _repo_root() / "reports" / "phase4_6_closeout"


def _timestamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%d_%H%M%S")


def _normalize_path(path: Path, repo_root: Path) -> str:
    return str(path.relative_to(repo_root)).replace("\\", "/")


def scan_line_for_findings(*, line: str, line_number: int, relative_file: str) -> list[PathFinding]:
    findings: list[PathFinding] = []
    for rule_id, pattern in RULES:
        if pattern.search(line):
            findings.append(
                PathFinding(
                    file=relative_file,
                    line=line_number,
                    rule_id=rule_id,
                    snippet=line.strip(),
                )
            )
    return findings


def scan_source_root(*, source_root: Path, repo_root: Path) -> list[PathFinding]:
    findings: list[PathFinding] = []
    for path in sorted(source_root.rglob("*.py")):
        relative = _normalize_path(path, repo_root)
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            findings.extend(
                scan_line_for_findings(
                    line=line,
                    line_number=line_number,
                    relative_file=relative,
                )
            )
    return findings


def _write_markdown(path: Path, payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    recommendation = payload["recommendation"]
    lines = [
        "# Phase 6 Analytics Path Portability",
        "",
        f"- Generated (UTC): `{payload['generated_at_utc']}`",
        f"- Source root: `{payload['source_root']}`",
        f"- Status: `{recommendation['status']}`",
        f"- Python files scanned: `{summary['python_files_scanned']}`",
        f"- Findings: `{summary['finding_count']}`",
        "",
        "## Findings",
        "",
    ]

    findings = payload["findings"]
    if not findings:
        lines.append("- None.")
    else:
        for item in findings:
            lines.append(
                f"- `{item['file']}:{item['line']}` `{item['rule_id']}` -> `{item['snippet']}`"
            )

    path.write_text("\n".join(lines), encoding="utf-8")


def verify_phase6_analytics_portability(
    *,
    source_root: Path,
    reports_dir: Path,
) -> PortabilityResult:
    reports_dir.mkdir(parents=True, exist_ok=True)
    stamp = _timestamp()
    output_json = reports_dir / f"analytics_portability_{stamp}.json"
    output_md = reports_dir / f"analytics_portability_{stamp}.md"

    repo_root = _repo_root()
    if not source_root.exists():
        findings: list[PathFinding] = [
            PathFinding(
                file=_normalize_path(source_root, repo_root),
                line=0,
                rule_id="missing_source_root",
                snippet="source root does not exist",
            )
        ]
    else:
        findings = scan_source_root(source_root=source_root, repo_root=repo_root)

    python_files_scanned = len(list(source_root.rglob("*.py"))) if source_root.exists() else 0
    status = "pass" if not findings else "fail"
    payload = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "source_root": _normalize_path(source_root, repo_root),
        "summary": {
            "python_files_scanned": python_files_scanned,
            "finding_count": len(findings),
        },
        "recommendation": {
            "status": status,
            "issues": [] if not findings else [f"{len(findings)} portability finding(s) detected."],
        },
        "findings": [
            {
                "file": item.file,
                "line": item.line,
                "rule_id": item.rule_id,
                "snippet": item.snippet,
            }
            for item in findings
        ],
    }
    output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    _write_markdown(output_md, payload)

    return PortabilityResult(
        report_json_path=output_json,
        report_md_path=output_md,
        status=status,
        finding_count=len(findings),
        findings=findings,
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Verify analytics engine path portability by scanning for hardcoded machine-specific paths.",
    )
    parser.add_argument(
        "--source-root",
        type=Path,
        default=_default_source_root(),
        help="Analytics source root to scan.",
    )
    parser.add_argument(
        "--reports-dir",
        type=Path,
        default=_default_reports_dir(),
        help="Directory where report artifacts are written.",
    )
    parser.add_argument(
        "--fail-on-hardcoded",
        action="store_true",
        help="Exit non-zero when portability findings are detected.",
    )
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    result = verify_phase6_analytics_portability(
        source_root=args.source_root.resolve(),
        reports_dir=args.reports_dir.resolve(),
    )
    print(f"[phase6-portability] status={result.status}")
    print(f"[phase6-portability] findings={result.finding_count}")
    print(f"[phase6-portability] markdown={result.report_md_path.as_posix()}")
    print(f"[phase6-portability] json={result.report_json_path.as_posix()}")
    if args.fail_on_hardcoded and result.finding_count > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

