"""
Assess core test-suite health to guard against coverage staleness regression.

Usage:
    python scripts/assess_test_suite_health.py
    python scripts/assess_test_suite_health.py --enforce
"""

from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REQUIRED_TEST_MODULES = (
    "tests/contract/test_openapi_contract.py",
    "tests/integration/test_readiness_api.py",
    "tests/integration/test_checklist_api.py",
    "tests/integration/test_facts_api.py",
    "tests/integration/test_projects_api.py",
    "tests/integration/test_playbooks_api.py",
    "tests/integration/test_auth_enforcement_routes.py",
    "tests/integration/test_project_authorization.py",
    "tests/integration/test_object_authorization.py",
    "tests/integration/test_role_policy.py",
    "tests/integration/test_security_integration.py",
    "tests/integration/test_tenant_isolation.py",
    "tests/integration/test_tenant_isolation_jwt_mode.py",
    "tests/integration/test_risk_reporting_foundation.py",
    "tests/integration/test_advisory_packages_api.py",
    "tests/unit/test_auth_dependencies.py",
    "tests/unit/test_audit_service.py",
    "tests/unit/test_audit_route_events.py",
    "tests/unit/test_risk_reporting_service.py",
    "tests/unit/test_advisory_package_service.py",
    "tests/unit/test_fact_service.py",
)


@dataclass
class TestSuiteHealthResult:
    report_json_path: Path
    report_md_path: Path
    status: str
    total_collected: int
    issues: list[str]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _default_reports_dir() -> Path:
    return _repo_root() / "reports" / "phase2_6_closeout"


def _timestamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%d_%H%M%S")


def _normalize_path(path: str) -> str:
    return path.replace("\\", "/")


def parse_collected_nodeids(stdout: str) -> list[str]:
    nodeids: list[str] = []
    for raw_line in stdout.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if "::" not in line:
            continue
        normalized = _normalize_path(line)
        if normalized.startswith("tests/"):
            nodeids.append(normalized)
    return nodeids


def _write_markdown(path: Path, payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    recommendation = payload["recommendation"]
    lines = [
        "# Test Suite Health Assessment",
        "",
        f"- Generated (UTC): `{payload['generated_at_utc']}`",
        f"- Recommendation status: `{recommendation['status']}`",
        f"- Total collected tests: `{summary['total_collected']}`",
        f"- Minimum expected tests: `{summary['min_expected_tests']}`",
        "",
        "## Required Modules",
        "",
        f"- Required module count: `{summary['required_module_count']}`",
        f"- Modules with collected tests: `{summary['modules_with_collected_tests']}`",
        f"- Missing modules: `{summary['missing_module_count']}`",
        "",
        "## Issues",
        "",
    ]
    issues = recommendation["issues"]
    if issues:
        for issue in issues:
            lines.append(f"- {issue}")
    else:
        lines.append("- None.")

    path.write_text("\n".join(lines), encoding="utf-8")


def assess_test_suite_health(
    *,
    reports_dir: Path,
    min_expected_tests: int,
) -> TestSuiteHealthResult:
    reports_dir.mkdir(parents=True, exist_ok=True)
    stamp = _timestamp()
    output_json = reports_dir / f"test_suite_health_{stamp}.json"
    output_md = reports_dir / f"test_suite_health_{stamp}.md"

    repo_root = _repo_root()
    test_targets = [module for module in REQUIRED_TEST_MODULES]
    command = ["pytest", "-q", "--collect-only", *test_targets, "-p", "no:cacheprovider"]
    proc = subprocess.run(
        command,
        cwd=repo_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    nodeids = parse_collected_nodeids(proc.stdout)
    total_collected = len(nodeids)

    issues: list[str] = []
    if proc.returncode != 0:
        issues.append("Pytest collection command failed.")

    module_counts: dict[str, int] = {}
    missing_modules: list[str] = []
    for module in REQUIRED_TEST_MODULES:
        prefix = _normalize_path(module) + "::"
        count = sum(1 for nodeid in nodeids if nodeid.startswith(prefix))
        module_counts[module] = count
        if count == 0:
            missing_modules.append(module)

    if total_collected < min_expected_tests:
        issues.append(
            f"Collected test count {total_collected} is below minimum threshold {min_expected_tests}."
        )
    if missing_modules:
        issues.append(
            f"{len(missing_modules)} required test modules collected zero tests."
        )

    status = "pass" if not issues else "fail"

    payload = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "command": " ".join(command),
        "summary": {
            "total_collected": total_collected,
            "min_expected_tests": int(min_expected_tests),
            "required_module_count": len(REQUIRED_TEST_MODULES),
            "modules_with_collected_tests": len(REQUIRED_TEST_MODULES) - len(missing_modules),
            "missing_module_count": len(missing_modules),
            "missing_modules": missing_modules,
        },
        "module_counts": module_counts,
        "recommendation": {
            "status": status,
            "issues": issues,
        },
        "command_output": {
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        },
    }
    output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    _write_markdown(output_md, payload)
    return TestSuiteHealthResult(
        report_json_path=output_json,
        report_md_path=output_md,
        status=status,
        total_collected=total_collected,
        issues=issues,
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Assess core test suite health for staleness regression.",
    )
    parser.add_argument(
        "--reports-dir",
        type=Path,
        default=_default_reports_dir(),
        help="Directory where assessment artifacts are written.",
    )
    parser.add_argument(
        "--min-expected-tests",
        type=int,
        default=120,
        help="Minimum collected test threshold for this assessment.",
    )
    parser.add_argument(
        "--enforce",
        action="store_true",
        help="Exit non-zero when assessment status is fail.",
    )
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    result = assess_test_suite_health(
        reports_dir=args.reports_dir.resolve(),
        min_expected_tests=max(int(args.min_expected_tests), 1),
    )
    print(f"[test-suite-health] status={result.status}")
    print(f"[test-suite-health] total_collected={result.total_collected}")
    print(f"[test-suite-health] markdown={result.report_md_path.as_posix()}")
    print(f"[test-suite-health] json={result.report_json_path.as_posix()}")
    if result.issues:
        print("[test-suite-health] issues:")
        for issue in result.issues:
            print(f"- {issue}")
    if args.enforce and result.status != "pass":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
