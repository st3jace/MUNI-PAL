"""
Verify frontend OpenAPI-generated artifacts are in sync with contracts/openapi.v1.json.

Usage:
    python scripts/verify_openapi_generated_artifacts.py
    python scripts/verify_openapi_generated_artifacts.py --fail-on-mismatch
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass
class VerificationResult:
    report_json_path: Path
    report_md_path: Path
    status: str
    mismatches: list[str]
    command_failures: list[str]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _default_reports_dir() -> Path:
    return _repo_root() / "reports" / "phase2_6_closeout"


def _timestamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%d_%H%M%S")


def _normalized_text(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _read_text_normalized(path: Path) -> str:
    return _normalized_text(path.read_text(encoding="utf-8"))


def compare_text_files(expected: Path, generated: Path, *, label: str) -> list[str]:
    mismatches: list[str] = []
    if not expected.exists():
        mismatches.append(f"{label}: expected file missing: {expected.as_posix()}")
        return mismatches
    if not generated.exists():
        mismatches.append(f"{label}: generated file missing: {generated.as_posix()}")
        return mismatches
    if _read_text_normalized(expected) != _read_text_normalized(generated):
        mismatches.append(f"{label}: content differs from generated output.")
    return mismatches


def _collect_files(root: Path) -> dict[str, Path]:
    if not root.exists():
        return {}
    return {
        str(path.relative_to(root)).replace("\\", "/"): path
        for path in root.rglob("*")
        if path.is_file()
    }


def compare_directories(expected_root: Path, generated_root: Path, *, label: str) -> list[str]:
    mismatches: list[str] = []
    expected_files = _collect_files(expected_root)
    generated_files = _collect_files(generated_root)

    expected_set = set(expected_files.keys())
    generated_set = set(generated_files.keys())

    missing_in_generated = sorted(expected_set - generated_set)
    extra_in_generated = sorted(generated_set - expected_set)

    for rel in missing_in_generated:
        mismatches.append(f"{label}: missing generated file: {rel}")
    for rel in extra_in_generated:
        mismatches.append(f"{label}: unexpected generated file: {rel}")

    for rel in sorted(expected_set & generated_set):
        expected_text = _read_text_normalized(expected_files[rel])
        generated_text = _read_text_normalized(generated_files[rel])
        if expected_text != generated_text:
            mismatches.append(f"{label}: content differs: {rel}")
    return mismatches


def _run_command(command: list[str], *, cwd: Path) -> tuple[int, str]:
    resolved = list(command)
    if os.name == "nt" and resolved and resolved[0] == "npm":
        resolved[0] = "npm.cmd"
    proc = subprocess.run(
        resolved,
        cwd=cwd,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
    output = (
        f"$ {' '.join(resolved)}\n"
        f"returncode={proc.returncode}\n\n"
        "--- STDOUT ---\n"
        f"{proc.stdout}\n"
        "--- STDERR ---\n"
        f"{proc.stderr}\n"
    )
    return proc.returncode, output


def _write_markdown(path: Path, payload: dict[str, Any]) -> None:
    recommendation = payload["recommendation"]
    lines = [
        "# OpenAPI Generated Artifact Verification",
        "",
        f"- Generated (UTC): `{payload['generated_at_utc']}`",
        f"- Contract source: `{payload['contract_source']}`",
        f"- Recommendation status: `{recommendation['status']}`",
        "",
        "## Command Results",
        "",
        f"- types generator return code: `{payload['command_results']['types_generator_returncode']}`",
        f"- client generator return code: `{payload['command_results']['client_generator_returncode']}`",
        "",
        "## Mismatches",
        "",
    ]
    mismatches = recommendation["mismatches"]
    if mismatches:
        for mismatch in mismatches:
            lines.append(f"- {mismatch}")
    else:
        lines.append("- None.")

    lines.extend(["", "## Command Failures", ""])
    failures = recommendation["command_failures"]
    if failures:
        for failure in failures:
            lines.append(f"- {failure}")
    else:
        lines.append("- None.")

    path.write_text("\n".join(lines), encoding="utf-8")


def verify_openapi_generated_artifacts(
    *,
    reports_dir: Path,
) -> VerificationResult:
    reports_dir.mkdir(parents=True, exist_ok=True)
    stamp = _timestamp()
    output_json = reports_dir / f"openapi_generated_artifacts_{stamp}.json"
    output_md = reports_dir / f"openapi_generated_artifacts_{stamp}.md"

    repo_root = _repo_root()
    expected_types = repo_root / "frontend" / "src" / "types" / "openapi.generated.ts"
    expected_client = repo_root / "frontend" / "src" / "generated" / "api-client"
    contract_source = repo_root / "contracts" / "openapi.v1.json"

    mismatches: list[str] = []
    command_failures: list[str] = []

    with tempfile.TemporaryDirectory(prefix="openapi-verify-") as temp_dir:
        temp_root = Path(temp_dir)
        generated_types = temp_root / "openapi.generated.ts"
        generated_client = temp_root / "api-client"

        types_command = [
            "npm",
            "--prefix",
            "frontend",
            "exec",
            "--",
            "openapi-typescript",
            "contracts/openapi.v1.json",
            "-o",
            str(generated_types),
        ]
        types_returncode, types_log = _run_command(types_command, cwd=repo_root)
        if types_returncode != 0:
            command_failures.append("openapi-typescript command failed.")

        client_command = [
            "npm",
            "--prefix",
            "frontend",
            "exec",
            "--",
            "openapi",
            "--input",
            "contracts/openapi.v1.json",
            "--output",
            str(generated_client),
            "--client",
            "axios",
        ]
        client_returncode, client_log = _run_command(client_command, cwd=repo_root)
        if client_returncode != 0:
            command_failures.append("openapi client codegen command failed.")

        if not command_failures:
            mismatches.extend(
                compare_text_files(
                    expected_types,
                    generated_types,
                    label="frontend openapi types",
                )
            )
            mismatches.extend(
                compare_directories(
                    expected_client,
                    generated_client,
                    label="frontend openapi client",
                )
            )

        status = "pass" if not mismatches and not command_failures else "fail"
        payload = {
            "generated_at_utc": datetime.now(UTC).isoformat(),
            "contract_source": str(contract_source.relative_to(repo_root)).replace("\\", "/"),
            "expected_artifacts": {
                "types": str(expected_types.relative_to(repo_root)).replace("\\", "/"),
                "client_dir": str(expected_client.relative_to(repo_root)).replace("\\", "/"),
            },
            "recommendation": {
                "status": status,
                "mismatches": mismatches,
                "command_failures": command_failures,
            },
            "command_results": {
                "types_generator_returncode": types_returncode,
                "client_generator_returncode": client_returncode,
                "types_generator_log": types_log,
                "client_generator_log": client_log,
            },
        }

    output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    _write_markdown(output_md, payload)
    return VerificationResult(
        report_json_path=output_json,
        report_md_path=output_md,
        status=payload["recommendation"]["status"],
        mismatches=mismatches,
        command_failures=command_failures,
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Verify frontend OpenAPI-generated artifacts are in sync with contract snapshot.",
    )
    parser.add_argument(
        "--reports-dir",
        type=Path,
        default=_default_reports_dir(),
        help="Directory for verification artifacts.",
    )
    parser.add_argument(
        "--fail-on-mismatch",
        action="store_true",
        help="Exit non-zero when mismatch or generation failure is detected.",
    )
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    result = verify_openapi_generated_artifacts(
        reports_dir=args.reports_dir.resolve(),
    )
    print(f"[openapi-generated-artifacts] status={result.status}")
    print(f"[openapi-generated-artifacts] markdown={result.report_md_path.as_posix()}")
    print(f"[openapi-generated-artifacts] json={result.report_json_path.as_posix()}")
    if result.command_failures:
        print("[openapi-generated-artifacts] command_failures:")
        for failure in result.command_failures:
            print(f"- {failure}")
    if result.mismatches:
        print("[openapi-generated-artifacts] mismatches:")
        for mismatch in result.mismatches:
            print(f"- {mismatch}")
    if args.fail_on_mismatch and (result.mismatches or result.command_failures):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
