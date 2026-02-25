"""
Run Phase 10 post-launch validation bundle and write evidence artifacts.

This script executes CI-equivalent gates and writes:
- JSON machine-readable results
- Markdown human-readable summary/checklist

Usage:
    python scripts/run_phase10_postlaunch_bundle.py
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
        "phase": "phase_10_postlaunch_bundle",
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
        "# Phase 10 Post-Launch Bundle Report",
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
            "## Weekly Manual Operations Checklist",
            "",
            "- [ ] Update 401/403/cross-tenant-denied trend review for this week (`OPS-1001`).",
            "- [ ] Review generated `ops1001_telemetry_trends_<timestamp>.md/.json` artifact for 7-day rates and threshold recommendations (`OPS-1001`).",
            "- [ ] Review generated `ops1001_telemetry_alert_routing_<timestamp>.md/.json` artifact for incident/escalation routing (`OPS-1001`/`OPS-1005`).",
            "- [ ] Record any alert threshold tuning changes and rationale (`OPS-1001`).",
            "- [ ] Execute or schedule second-tenant onboarding rehearsal (`OPS-1002`).",
            "- [ ] Record BFMS production-grade scoring hardening progress (`OPS-1003`).",
            "- [ ] Review generated `healthcare_readiness_<timestamp>.md/.json` artifacts and record outcomes (`OPS-1004`).",
            "- [ ] Review generated `bond_corpus_calibration_<timestamp>.md/.json` artifacts for CDR calibration gaps (`OPS-1003`).",
            "- [ ] Review generated `advisory_cohort_inference_<timestamp>.md/.json` artifact for inferred cohort behavior across sector/deal-type profiles (`OPS-1003`/`OPS-1004`).",
            "- [ ] Review generated `advisory_package_smoke_<timestamp>.md/.json` artifact for internal/external package staging smoke results (`OPS-1003`/`OPS-1004`).",
            "- [ ] Review generated `age_weighting_policy_<timestamp>.md/.json` artifact for CDR-2 staged enable/tuning recommendation (`CDR-2`).",
            "- [ ] Review generated `bond_corpus_drift_<timestamp>.md/.json` artifact for week-over-week CDR drift (`CDR-5`).",
            "- [ ] Review generated `bond_corpus_alert_routing_<timestamp>.md/.json` artifact for CDR-5 escalation routing (`CDR-5`).",
            "- [ ] Review generated `ops1003_m5_readiness_<timestamp>.md/.json` artifact for OPS-1003 M5 go/no-go with residual risks.",
            "- [ ] Execute/record incident drill timeline and outcomes (`OPS-1005`).",
            "- [ ] Populate `reports/phase10_postlaunch/WEEKLY_EVIDENCE_TEMPLATE.md` and link in tracker.",
            "",
        ]
    )

    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    repo_root = _repo_root()
    stamp = _timestamp()
    report_root = repo_root / "reports" / "phase10_postlaunch"
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
            "Phase 10 Corpus Provision",
            "python scripts/provision_phase10_corpus_dbs.py",
            None,
        ),
        (
            "Phase 10 Corpus Preflight",
            "python scripts/verify_phase10_corpus_prereqs.py",
            None,
        ),
        (
            "Phase 10 Corpus Outlier Cleanup",
            "python scripts/cleanup_corpus_db_outliers.py",
            None,
        ),
        (
            "Phase 10 Document Index Rebuild",
            "python scripts/rebuild_corpus_document_index.py --clear-existing",
            None,
        ),
        (
            "Phase 10 Corpus Reconciliation Gate",
            "python scripts/verify_corpus_db_reconciliation.py "
            "--fail-on-extra-db "
            "--fail-on-index-extras "
            "--fail-on-type-mismatch",
            None,
        ),
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
            "tests/unit/test_bond_corpus_drift.py "
            "tests/unit/test_bond_corpus_alert_routing.py "
            "tests/unit/test_age_weighting_policy_assessment.py "
            "tests/unit/test_advisory_cohort_inference_assessment.py "
            "tests/unit/test_advisory_package_smoke_assessment.py "
            "tests/unit/test_ops1003_m5_readiness_assessment.py "
            "tests/unit/test_ops1003_regression_gates.py "
            "tests/unit/test_ops1001_telemetry_trends_assessment.py "
            "tests/unit/test_ops1001_telemetry_alert_routing.py "
            "tests/unit/test_corpus_db_outlier_cleanup.py "
            "tests/unit/test_corpus_document_index_rebuild.py "
            "tests/unit/test_corpus_db_reconciliation.py "
            "tests/unit/test_advisory_package_service.py "
            "tests/unit/test_fact_service.py "
            "-p no:cacheprovider",
            default_env,
        ),
        (
            "Frontend Tests",
            "npm --prefix frontend run test",
            default_env,
        ),
        (
            "Frontend Production Build",
            "npm --prefix frontend run build",
            default_env,
        ),
        (
            "Auth+Tenant+Risk Stability Slice",
            "pytest -q "
            "tests/integration/test_auth_enforcement_routes.py "
            "tests/integration/test_security_integration.py "
            "tests/integration/test_tenant_isolation.py "
            "tests/integration/test_tenant_isolation_jwt_mode.py "
            "tests/integration/test_risk_reporting_foundation.py "
            "tests/unit/test_auth_dependencies.py "
            "tests/unit/test_risk_reporting_service.py",
            default_env,
        ),
        (
            "OPS-1001 Telemetry Trend Assessment",
            "python scripts/assess_ops1001_telemetry_trends.py",
            default_env,
        ),
        (
            "OPS-1001 Telemetry Alert Routing",
            "python scripts/route_ops1001_telemetry_alerts.py --fail-on-critical",
            default_env,
        ),
        (
            "Healthcare Corpus Readiness Snapshot",
            "python scripts/assess_healthcare_corpus_readiness.py",
            default_env,
        ),
        (
            "Bond Corpus Calibration Snapshot",
            "python scripts/assess_bond_corpus_calibration.py",
            default_env,
        ),
        (
            "Advisory Cohort Inference Assessment",
            "python scripts/assess_advisory_cohort_inference.py",
            default_env,
        ),
        (
            "Advisory Package Smoke Assessment",
            "python scripts/assess_advisory_package_smoke.py --mode asgi",
            default_env,
        ),
        (
            "Age Weighting Policy Assessment",
            "python scripts/assess_age_weighting_policy.py",
            default_env,
        ),
        (
            "Bond Corpus Drift Snapshot",
            "python scripts/assess_bond_corpus_drift.py",
            default_env,
        ),
        (
            "Bond Corpus Drift Alert Routing",
            "python scripts/route_bond_corpus_drift_alerts.py --fail-on-critical",
            default_env,
        ),
        (
            "OPS-1003 M5 Readiness Review",
            "python scripts/assess_ops1003_m5_readiness.py",
            default_env,
        ),
        (
            "OPS-1003 Regression Gate",
            "python scripts/enforce_ops1003_regression_gates.py "
            "--reports-dir reports/phase10_postlaunch "
            "--max-residual-risks 1 "
            "--require-m5-go",
            default_env,
        ),
    ]

    results: list[CommandResult] = []
    for name, command, extra_env in commands:
        print(f"[phase10-postlaunch] running: {name}")
        result = _run_command(
            name=name,
            command=command,
            repo_root=repo_root,
            logs_dir=logs_dir,
            extra_env=extra_env,
        )
        results.append(result)
        if name in {
            "Phase 10 Corpus Provision",
            "Phase 10 Corpus Preflight",
            "Phase 10 Corpus Outlier Cleanup",
            "Phase 10 Document Index Rebuild",
            "Phase 10 Corpus Reconciliation Gate",
        } and result.returncode != 0:
            print("[phase10-postlaunch] corpus setup failed; skipping remaining checks")
            break

    finished_at = datetime.now(UTC).isoformat()
    overall_status = "pass" if all(result.returncode == 0 for result in results) else "fail"

    json_report_path = report_root / f"phase10_postlaunch_{stamp}.json"
    md_report_path = report_root / f"phase10_postlaunch_{stamp}.md"

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

    print(f"[phase10-postlaunch] overall={overall_status}")
    print(f"[phase10-postlaunch] markdown={md_report_path.relative_to(repo_root).as_posix()}")
    print(f"[phase10-postlaunch] json={json_report_path.relative_to(repo_root).as_posix()}")
    if overall_status != "pass":
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
