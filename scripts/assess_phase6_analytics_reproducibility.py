"""
Assess Phase 6 analytics reproducibility by replaying score runs per sector.

Usage:
    python scripts/assess_phase6_analytics_reproducibility.py
    python scripts/assess_phase6_analytics_reproducibility.py --fail-on-drift
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping


SECTORS: tuple[str, ...] = ("waste", "healthcare")


@dataclass
class ReproducibilityResult:
    report_json_path: Path
    report_md_path: Path
    status: str
    sector_status: dict[str, str]
    issues: list[str]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _default_reports_dir() -> Path:
    return _repo_root() / "reports" / "phase4_6_closeout"


def _timestamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%d_%H%M%S")


def _canonicalize_score_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    canonical = json.loads(json.dumps(payload))
    canonical.pop("scored_at", None)
    return canonical


def evaluate_sector_reproducibility(
    *,
    sector: str,
    first_payload: Mapping[str, Any],
    second_payload: Mapping[str, Any],
) -> tuple[str, list[str]]:
    issues: list[str] = []
    first_summary = first_payload.get("summary", {})
    second_summary = second_payload.get("summary", {})

    first_total = int(first_summary.get("total_obligors", 0) or 0)
    second_total = int(second_summary.get("total_obligors", 0) or 0)
    if first_total <= 0 or second_total <= 0:
        issues.append(f"{sector}: zero obligors scored in one or more runs.")

    canonical_first = _canonicalize_score_payload(first_payload)
    canonical_second = _canonicalize_score_payload(second_payload)
    if canonical_first != canonical_second:
        issues.append(f"{sector}: canonical score outputs drifted between repeated runs.")

    return ("pass" if not issues else "fail", issues)


def _run_score_command(*, repo_root: Path, sector: str, output_path: Path) -> tuple[int, str]:
    command = [
        sys.executable,
        "-m",
        "emma.bond_os_extractor.src.cli",
        "--sector",
        sector,
        "score",
        "--threshold",
        "50",
        "--output",
        str(output_path),
    ]
    proc = subprocess.run(
        command,
        cwd=repo_root,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
    log_text = (
        f"$ {' '.join(command)}\n"
        f"returncode={proc.returncode}\n\n"
        "--- STDOUT ---\n"
        f"{proc.stdout}\n"
        "--- STDERR ---\n"
        f"{proc.stderr}\n"
    )
    return proc.returncode, log_text


def _write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# Phase 6 Analytics Reproducibility Assessment",
        "",
        f"- Generated (UTC): `{payload['generated_at_utc']}`",
        f"- Status: `{payload['recommendation']['status']}`",
        "",
        "## Sector Results",
        "",
        "| Sector | Status | Total Obligors (Run1) | Total Obligors (Run2) | Investable (Run1) | Investable (Run2) |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for row in payload["sector_results"]:
        lines.append(
            f"| {row['sector']} | `{row['status']}` | {row['run1_total_obligors']} | "
            f"{row['run2_total_obligors']} | {row['run1_investable']} | {row['run2_investable']} |"
        )

    lines.extend(["", "## Issues", ""])
    issues = payload["recommendation"]["issues"]
    if issues:
        for issue in issues:
            lines.append(f"- {issue}")
    else:
        lines.append("- None.")

    lines.extend(["", "## Logs", ""])
    for log_rel in payload["log_files"]:
        lines.append(f"- `{log_rel}`")

    path.write_text("\n".join(lines), encoding="utf-8")


def assess_phase6_analytics_reproducibility(
    *,
    reports_dir: Path,
) -> ReproducibilityResult:
    reports_dir.mkdir(parents=True, exist_ok=True)
    stamp = _timestamp()
    output_json = reports_dir / f"analytics_reproducibility_{stamp}.json"
    output_md = reports_dir / f"analytics_reproducibility_{stamp}.md"
    logs_dir = reports_dir / f"analytics_reproducibility_logs_{stamp}"
    logs_dir.mkdir(parents=True, exist_ok=True)

    repo_root = _repo_root()
    sector_rows: list[dict[str, Any]] = []
    sector_status: dict[str, str] = {}
    issues: list[str] = []
    log_files: list[str] = []

    with tempfile.TemporaryDirectory(prefix="phase6-repro-") as temp_dir:
        temp_root = Path(temp_dir)
        for sector in SECTORS:
            run1_path = temp_root / f"{sector}_run1.json"
            run2_path = temp_root / f"{sector}_run2.json"

            run1_code, run1_log = _run_score_command(
                repo_root=repo_root,
                sector=sector,
                output_path=run1_path,
            )
            run1_log_path = logs_dir / f"{sector}_run1.log"
            run1_log_path.write_text(run1_log, encoding="utf-8")
            log_files.append(str(run1_log_path.relative_to(repo_root)).replace("\\", "/"))

            run2_code, run2_log = _run_score_command(
                repo_root=repo_root,
                sector=sector,
                output_path=run2_path,
            )
            run2_log_path = logs_dir / f"{sector}_run2.log"
            run2_log_path.write_text(run2_log, encoding="utf-8")
            log_files.append(str(run2_log_path.relative_to(repo_root)).replace("\\", "/"))

            if run1_code != 0:
                sector_status[sector] = "fail"
                issues.append(f"{sector}: first score command failed.")
                sector_rows.append(
                    {
                        "sector": sector,
                        "status": "fail",
                        "run1_total_obligors": 0,
                        "run2_total_obligors": 0,
                        "run1_investable": 0,
                        "run2_investable": 0,
                    }
                )
                continue
            if run2_code != 0:
                sector_status[sector] = "fail"
                issues.append(f"{sector}: second score command failed.")
                sector_rows.append(
                    {
                        "sector": sector,
                        "status": "fail",
                        "run1_total_obligors": 0,
                        "run2_total_obligors": 0,
                        "run1_investable": 0,
                        "run2_investable": 0,
                    }
                )
                continue

            first_payload = json.loads(run1_path.read_text(encoding="utf-8"))
            second_payload = json.loads(run2_path.read_text(encoding="utf-8"))
            status, sector_issues = evaluate_sector_reproducibility(
                sector=sector,
                first_payload=first_payload,
                second_payload=second_payload,
            )
            sector_status[sector] = status
            issues.extend(sector_issues)

            first_summary = first_payload.get("summary", {})
            second_summary = second_payload.get("summary", {})
            sector_rows.append(
                {
                    "sector": sector,
                    "status": status,
                    "run1_total_obligors": int(first_summary.get("total_obligors", 0) or 0),
                    "run2_total_obligors": int(second_summary.get("total_obligors", 0) or 0),
                    "run1_investable": int(first_summary.get("investable_count", 0) or 0),
                    "run2_investable": int(second_summary.get("investable_count", 0) or 0),
                }
            )

    overall_status = "pass" if not issues else "fail"
    payload = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "phase": "phase_6_analytics_reproducibility",
        "recommendation": {
            "status": overall_status,
            "issues": issues,
        },
        "sector_results": sector_rows,
        "log_files": log_files,
    }
    output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    _write_markdown(output_md, payload)

    return ReproducibilityResult(
        report_json_path=output_json,
        report_md_path=output_md,
        status=overall_status,
        sector_status=sector_status,
        issues=issues,
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Assess analytics reproducibility by comparing repeated score outputs.",
    )
    parser.add_argument(
        "--reports-dir",
        type=Path,
        default=_default_reports_dir(),
        help="Directory where report artifacts are written.",
    )
    parser.add_argument(
        "--fail-on-drift",
        action="store_true",
        help="Exit non-zero when reproducibility issues are detected.",
    )
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    result = assess_phase6_analytics_reproducibility(
        reports_dir=args.reports_dir.resolve(),
    )
    print(f"[phase6-reproducibility] status={result.status}")
    print(f"[phase6-reproducibility] sectors={result.sector_status}")
    print(f"[phase6-reproducibility] markdown={result.report_md_path.as_posix()}")
    print(f"[phase6-reproducibility] json={result.report_json_path.as_posix()}")
    if result.issues:
        print("[phase6-reproducibility] issues:")
        for issue in result.issues:
            print(f"- {issue}")
    if args.fail_on_drift and result.issues:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

