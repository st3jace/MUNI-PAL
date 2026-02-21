"""
Run Phase 9 release readiness validation bundle and write evidence artifacts.

This script executes CI-equivalent gates plus launch-profile regressions and writes:
- JSON machine-readable results
- Markdown human-readable summary/checklist

Usage:
    python scripts/run_phase9_release_readiness_bundle.py
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
        "phase": "phase_9_release_readiness_bundle",
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
        "# Phase 9 Release Readiness Bundle Report",
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
            "## Target CI/Staging Manual Readiness",
            "",
            "- [ ] Complete `REL-901`: sign baseline pack in `V2/BASELINE_PACK_20260218.md`.",
            "- [ ] Complete `REL-902`: execute and sign SEC-008 checklist in `V2/SECURITY_HARDENING_ROLLOUT_CHECKLIST.md`.",
            "- [ ] Set `AUTH_ENFORCEMENT_V2=true` and `ROLE_ENFORCEMENT_V2=true` in staging launch profile.",
            "- [ ] Validate security flows with JWT-only auth (no `X-User-Id` dependency).",
            "- [ ] Validate tenant isolation with JWT tenant claims (`tenant_id`/`tenant`/`org`) and capture evidence.",
            "- [ ] Validate launch observability (401/403/cross-tenant-denied queries + alert routing).",
            "- [ ] Execute cutover rehearsal and rollback drill with timestamps.",
            "- [ ] Record results and sign-off in `reports/phase9_release/STAGING_EVIDENCE_TEMPLATE.md`.",
            "- [ ] Link CI run URL and evidence references in `V2/EXECUTION_TRACKER.md`.",
            "",
        ]
    )

    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    repo_root = _repo_root()
    stamp = _timestamp()
    report_root = repo_root / "reports" / "phase9_release"
    logs_dir = report_root / f"logs_{stamp}"
    logs_dir.mkdir(parents=True, exist_ok=True)

    started_at = datetime.now(UTC).isoformat()
    default_env = {"USE_SQLITE": "true"}

    commands: list[tuple[str, str, Mapping[str, str] | None]] = [
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
            "tests/integration/test_tenant_isolation_jwt_mode.py "
            "tests/integration/test_risk_reporting_foundation.py "
            "tests/integration/test_advisory_packages_api.py "
            "tests/unit/test_auth_dependencies.py "
            "tests/unit/test_audit_service.py "
            "tests/unit/test_audit_route_events.py "
            "tests/unit/test_risk_reporting_service.py "
            "tests/unit/test_advisory_package_service.py "
            "tests/unit/test_fact_service.py "
            "-p no:cacheprovider",
            default_env,
        ),
        (
            "Frontend Tests",
            "npm --prefix frontend run test",
            None,
        ),
        (
            "Frontend Production Build",
            "npm --prefix frontend run build",
            None,
        ),
        (
            "Launch Profile Auth+Tenant Slice",
            "pytest -q "
            "tests/integration/test_auth_enforcement_routes.py "
            "tests/integration/test_security_integration.py "
            "tests/integration/test_tenant_isolation_jwt_mode.py "
            "tests/unit/test_auth_dependencies.py",
            {
                **default_env,
                "AUTH_ENFORCEMENT_V2": "true",
                "ROLE_ENFORCEMENT_V2": "true",
                "TENANT_ISOLATION_V2": "true",
                "JWT_SECRET_KEY": "test-secret",
                "JWT_ALGORITHM": "HS256",
            },
        ),
    ]

    results: list[CommandResult] = []
    for name, command, extra_env in commands:
        print(f"[phase9-release] running: {name}")
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

    json_report_path = report_root / f"phase9_release_{stamp}.json"
    md_report_path = report_root / f"phase9_release_{stamp}.md"

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

    print(f"[phase9-release] overall={overall_status}")
    print(f"[phase9-release] markdown={md_report_path.relative_to(repo_root).as_posix()}")
    print(f"[phase9-release] json={json_report_path.relative_to(repo_root).as_posix()}")
    if overall_status != "pass":
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
