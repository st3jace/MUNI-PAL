"""
Run Phase 8 closeout validation bundle and write evidence artifacts.

This script executes local CI-equivalent gates and writes:
- JSON machine-readable results
- Markdown human-readable summary/checklist

Usage:
    python scripts/run_phase8_closeout_bundle.py
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from collections.abc import Iterable
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
) -> CommandResult:
    started = time.perf_counter()
    proc = subprocess.run(
        command,
        cwd=repo_root,
        shell=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    duration = time.perf_counter() - started
    safe_name = name.lower().replace(" ", "_").replace("/", "_")
    log_path = logs_dir / f"{safe_name}.log"
    log_text = (
        f"$ {command}\n\n"
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
        "phase": "phase_8_closeout_bundle",
        "generated_at_utc": finished_at,
        "started_at_utc": started_at,
        "overall_status": overall_status,
        "results": [asdict(result) | {"status": result.status} for result in results],
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
        "# Phase 8 Closeout Bundle Report",
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
            "## Target CI/Staging Manual Closeout",
            "",
            "- [ ] Confirm first green run of `.github/workflows/core-security-risk-gate.yml` in target CI.",
            "- [ ] Apply migration `b8c9d0e1f2a3` in target DB and capture output.",
            "- [ ] Validate tenant backfill results (`missing_tenant_rows = 0` and tenant distribution query).",
            "- [ ] Set `TENANT_ISOLATION_V2=true` in staging and restart API.",
            "- [ ] Validate same-tenant project access succeeds (list/read/write).",
            "- [ ] Validate cross-tenant project access is denied with `403`.",
            "- [ ] Execute rollback drill (`TENANT_ISOLATION_V2=false`) and capture restoration evidence.",
            "- [ ] Record all evidence and sign-off in `reports/phase8_closeout/STAGING_EVIDENCE_TEMPLATE.md`.",
            "- [ ] Link CI run URL and staging evidence in `V2/EXECUTION_TRACKER.md`.",
            "",
        ]
    )

    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    repo_root = _repo_root()
    stamp = _timestamp()
    report_root = repo_root / "reports" / "phase8_closeout"
    logs_dir = report_root / f"logs_{stamp}"
    logs_dir.mkdir(parents=True, exist_ok=True)

    started_at = datetime.now(UTC).isoformat()

    commands: list[tuple[str, str]] = [
        (
            "Backend CI-Equivalent Gate",
            "pytest -q "
            "tests/contract/test_openapi_contract.py "
            "tests/integration/test_readiness_api.py "
            "tests/integration/test_checklist_api.py "
            "tests/integration/test_facts_api.py "
            "tests/integration/test_projects_api.py "
            "tests/integration/test_playbooks_api.py "
            "tests/integration/test_auth_enforcement_routes.py "
            "tests/integration/test_project_authorization.py "
            "tests/integration/test_object_authorization.py "
            "tests/integration/test_role_policy.py "
            "tests/integration/test_security_integration.py "
            "tests/integration/test_tenant_isolation.py "
            "tests/integration/test_risk_reporting_foundation.py "
            "tests/integration/test_advisory_packages_api.py "
            "tests/unit/test_auth_dependencies.py "
            "tests/unit/test_audit_service.py "
            "tests/unit/test_audit_route_events.py "
            "tests/unit/test_risk_reporting_service.py "
            "tests/unit/test_advisory_package_service.py "
            "tests/unit/test_fact_service.py "
            "-p no:cacheprovider",
        ),
        (
            "Frontend Tests",
            "npm --prefix frontend run test",
        ),
        (
            "Frontend Production Build",
            "npm --prefix frontend run build",
        ),
        (
            "Tenant Isolation Regression Slice",
            "pytest -q "
            "tests/integration/test_tenant_isolation.py "
            "tests/integration/test_project_authorization.py "
            "tests/unit/test_auth_dependencies.py",
        ),
    ]

    results: list[CommandResult] = []
    for name, command in commands:
        print(f"[phase8-closeout] running: {name}")
        results.append(
            _run_command(
                name=name,
                command=command,
                repo_root=repo_root,
                logs_dir=logs_dir,
            )
        )

    finished_at = datetime.now(UTC).isoformat()
    overall_status = "pass" if all(result.returncode == 0 for result in results) else "fail"

    json_report_path = report_root / f"phase8_closeout_{stamp}.json"
    md_report_path = report_root / f"phase8_closeout_{stamp}.md"

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

    print(f"[phase8-closeout] overall={overall_status}")
    print(f"[phase8-closeout] markdown={md_report_path.relative_to(repo_root).as_posix()}")
    print(f"[phase8-closeout] json={json_report_path.relative_to(repo_root).as_posix()}")
    if overall_status != "pass":
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
