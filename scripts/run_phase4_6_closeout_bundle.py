"""
Run Phase 4-6 closeout bundle and write evidence artifacts.

This bundle targets:
- Phase 4: ingestion and extraction hardening
- Phase 5: readiness and reporting quality gates
- Phase 6: analytics engine hardening

Usage:
    python scripts/run_phase4_6_closeout_bundle.py
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass
class CommandResult:
    name: str
    command: str
    returncode: int
    duration_seconds: float
    log_file: str

    @property
    def status(self) -> str:
        return "pass" if self.returncode == 0 else "fail"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _timestamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%d_%H%M%S")


def _run_command(
    *,
    name: str,
    command: str,
    repo_root: Path,
    logs_dir: Path,
    extra_env: Mapping[str, str] | None = None,
) -> CommandResult:
    started = time.perf_counter()
    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)
    proc = subprocess.run(
        command,
        cwd=repo_root,
        shell=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )
    duration = time.perf_counter() - started
    safe_name = name.lower().replace(" ", "_").replace("/", "_")
    log_path = logs_dir / f"{safe_name}.log"
    env_notes = ""
    if extra_env:
        env_notes = "--- ENV OVERRIDES ---\n" + "\n".join(
            f"{key}={value}" for key, value in sorted(extra_env.items())
        )
        env_notes += "\n\n"
    log_text = (
        f"$ {command}\n\n"
        f"{env_notes}"
        f"returncode={proc.returncode}\n"
        f"duration_seconds={duration:.2f}\n\n"
        "--- STDOUT ---\n"
        f"{proc.stdout}\n"
        "--- STDERR ---\n"
        f"{proc.stderr}\n"
    )
    log_path.write_text(log_text, encoding="utf-8")
    return CommandResult(
        name=name,
        command=command,
        returncode=proc.returncode,
        duration_seconds=duration,
        log_file=str(log_path.relative_to(repo_root)).replace("\\", "/"),
    )


def _write_json_report(
    *,
    report_path: Path,
    started_at: str,
    finished_at: str,
    results: Iterable[CommandResult],
    overall_status: str,
) -> None:
    payload = {
        "phase": "phase_4_6_closeout_bundle",
        "generated_at_utc": finished_at,
        "started_at_utc": started_at,
        "overall_status": overall_status,
        "results": [asdict(result) | {"status": result.status} for result in results],
        "phase_targets": ["Phase 4", "Phase 5", "Phase 6"],
    }
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_markdown_report(
    *,
    repo_root: Path,
    report_path: Path,
    json_report_path: Path,
    started_at: str,
    finished_at: str,
    results: list[CommandResult],
    overall_status: str,
) -> None:
    lines: list[str] = [
        "# Phase 4-6 Closeout Bundle Report",
        "",
        f"- Started (UTC): `{started_at}`",
        f"- Finished (UTC): `{finished_at}`",
        f"- Overall status: `{overall_status}`",
        f"- JSON report: `{json_report_path.relative_to(repo_root).as_posix()}`",
        "",
        "## Automated Gate Results",
        "",
        "| Check | Status | Duration (s) | Log |",
        "|---|---|---:|---|",
    ]
    for result in results:
        lines.append(
            f"| {result.name} | `{result.status}` | {result.duration_seconds:.2f} | `{result.log_file}` |"
        )

    lines.extend(
        [
            "",
            "## Closeout Checklist",
            "",
            "- [ ] Capture latest CI run URL for `.github/workflows/core-security-risk-gate.yml`.",
            "- [ ] Capture latest CI run URL for `.github/workflows/phase4-6-closeout-dispatch.yml`.",
            "- [ ] Update Phase 4, 5, and 6 status rows in `V2/EXECUTION_TRACKER.md` with evidence links.",
            "- [ ] Confirm no Phase 4/5/6 regressions in the next post-merge core gate run.",
            "",
        ]
    )
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    repo_root = _repo_root()
    stamp = _timestamp()
    report_root = repo_root / "reports" / "phase4_6_closeout"
    logs_dir = report_root / f"logs_{stamp}"
    logs_dir.mkdir(parents=True, exist_ok=True)

    started_at = datetime.now(UTC).isoformat()
    default_env = {
        "USE_SQLITE": "true",
        "AUTH_ENFORCEMENT_V2": "false",
        "ROLE_ENFORCEMENT_V2": "false",
        "TENANT_ISOLATION_V2": "false",
    }

    commands: list[tuple[str, str, Mapping[str, str] | None]] = [
        (
            "Phase 4 Async Orchestration Gate",
            "pytest -q "
            "tests/integration/test_artifacts_api.py "
            "tests/unit/test_artifact_dispatch.py "
            "-p no:cacheprovider",
            default_env,
        ),
        (
            "Phase 4 Canonicalization and Archive Gate",
            "pytest -q "
            "tests/integration/test_facts_api.py "
            "tests/unit/test_fact_service.py "
            "tests/unit/test_audit_route_events.py "
            "-p no:cacheprovider",
            default_env,
        ),
        (
            "Phase 5 Scoring Validation Gate",
            "pytest -q "
            "tests/integration/test_risk_reporting_foundation.py "
            "tests/unit/test_risk_reporting_service.py "
            "-p no:cacheprovider",
            default_env,
        ),
        (
            "Phase 5 Report Quality Gate",
            "pytest -q "
            "tests/integration/test_advisory_packages_api.py "
            "tests/unit/test_advisory_package_service.py "
            "tests/unit/test_audit_route_events.py "
            "-p no:cacheprovider",
            default_env,
        ),
        (
            "Phase 6 Analytics Path Portability Gate",
            "python scripts/verify_phase6_analytics_portability.py --fail-on-hardcoded",
            None,
        ),
        (
            "Phase 6 Analytics Reproducibility Gate",
            "python scripts/assess_phase6_analytics_reproducibility.py --fail-on-drift",
            None,
        ),
    ]

    results: list[CommandResult] = []
    for name, command, extra_env in commands:
        print(f"[phase4-6-closeout] running: {name}")
        results.append(
            _run_command(
                name=name,
                command=command,
                repo_root=repo_root,
                logs_dir=logs_dir,
                extra_env=extra_env,
            )
        )

    finished_at = datetime.now(UTC).isoformat()
    overall_status = "pass" if all(result.returncode == 0 for result in results) else "fail"

    json_report_path = report_root / f"phase4_6_closeout_{stamp}.json"
    md_report_path = report_root / f"phase4_6_closeout_{stamp}.md"

    _write_json_report(
        report_path=json_report_path,
        started_at=started_at,
        finished_at=finished_at,
        results=results,
        overall_status=overall_status,
    )
    _write_markdown_report(
        repo_root=repo_root,
        report_path=md_report_path,
        json_report_path=json_report_path,
        started_at=started_at,
        finished_at=finished_at,
        results=results,
        overall_status=overall_status,
    )

    print(f"[phase4-6-closeout] overall={overall_status}")
    print(f"[phase4-6-closeout] markdown={md_report_path.relative_to(repo_root).as_posix()}")
    print(f"[phase4-6-closeout] json={json_report_path.relative_to(repo_root).as_posix()}")
    if overall_status != "pass":
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

