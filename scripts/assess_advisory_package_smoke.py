"""
Assess internal/external advisory package generation via API smoke checks.

Usage:
    python scripts/assess_advisory_package_smoke.py
    python scripts/assess_advisory_package_smoke.py --mode http --base-url http://127.0.0.1:8000
    python scripts/assess_advisory_package_smoke.py --mode asgi --asgi-sqlite-path ./tmp/phase10_smoke.db
"""

from __future__ import annotations

import argparse
import asyncio
import importlib
import json
import os
import sys
import tempfile
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx
from jose import jwt

DEFAULT_BASE_URL = "http://127.0.0.1:8000"
DEFAULT_USER_ID = "00000000-0000-0000-0000-000000000001"
DEFAULT_TENANT_ID = "default"
DEFAULT_ROLE = "admin"

REQUIRED_ASSERTION_KEYS = (
    "project_id_resolved",
    "internal_generate_ok",
    "internal_report_fetch_ok",
    "external_generate_ok",
    "external_package_fetch_ok",
    "external_validate_ok",
)


@dataclass
class StepResult:
    name: str
    method: str
    path: str
    status_code: int | None
    ok: bool
    duration_seconds: float
    error: str | None
    response_excerpt: str | None


@dataclass
class AssessmentResult:
    report_json_path: Path
    report_md_path: Path
    recommendation: str
    reasons: list[str]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _default_output_dir() -> Path:
    return _repo_root() / "reports" / "phase10_postlaunch"


def _timestamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%d_%H%M%S")


def _truncate(value: str, *, max_len: int = 500) -> str:
    text = value.strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def _safe_json_loads(response: httpx.Response) -> dict[str, Any] | list[Any] | None:
    try:
        parsed: Any = response.json()
    except Exception:  # noqa: BLE001
        return None
    if isinstance(parsed, (dict, list)):
        return parsed
    return None


def _excerpt_from_payload(
    *,
    payload: dict[str, Any] | list[Any] | None,
    fallback_text: str,
) -> str:
    if payload is not None:
        return _truncate(json.dumps(payload, ensure_ascii=True))
    return _truncate(fallback_text)


def _latest_artifact_name(*, output_dir: Path, pattern: str) -> str | None:
    candidates = sorted(output_dir.glob(pattern))
    if not candidates:
        return None
    return candidates[-1].name


def _build_bearer_token(
    *,
    explicit_token: str | None,
    user_id: str,
    role: str,
    tenant_id: str,
    tenant_claim_key: str,
    secret_key: str | None,
    algorithm: str,
    ttl_minutes: int,
) -> tuple[str | None, str]:
    token = (explicit_token or os.getenv("MUNIPAL_API_TOKEN") or "").strip()
    if token:
        return token, "provided"

    secret = (secret_key or os.getenv("JWT_SECRET_KEY") or "").strip()
    if not secret:
        try:
            from munipal.config import get_settings

            secret = str(get_settings().jwt_secret_key or "").strip()
        except Exception:  # noqa: BLE001
            secret = ""
    if not secret:
        return None, "none"

    payload: dict[str, Any] = {
        "sub": user_id,
        "role": role,
        "exp": datetime.now(UTC) + timedelta(minutes=max(1, ttl_minutes)),
    }
    if tenant_claim_key.strip():
        payload[tenant_claim_key.strip()] = tenant_id
    token = jwt.encode(payload, secret, algorithm=algorithm)
    return token, "generated"


def _build_headers(
    *,
    bearer_token: str | None,
    user_id: str,
    role: str,
    tenant_id: str,
) -> dict[str, str]:
    headers = {
        "Accept": "application/json",
        "X-User-Id": user_id,
        "X-User-Role": role,
        "X-Tenant-Id": tenant_id,
    }
    if bearer_token:
        headers["Authorization"] = f"Bearer {bearer_token}"
    return headers


def _recommendation_from_assertions(assertions: dict[str, bool]) -> tuple[str, list[str]]:
    failed = [key for key in REQUIRED_ASSERTION_KEYS if not assertions.get(key, False)]
    if not failed:
        return "go", []
    reasons = [f"{key} failed." for key in failed]
    return "no-go", reasons


async def _request_step(
    *,
    client: httpx.AsyncClient,
    name: str,
    method: str,
    path: str,
    headers: dict[str, str],
    expected_statuses: tuple[int, ...] = (200,),
    json_body: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
) -> tuple[StepResult, dict[str, Any] | list[Any] | None]:
    started = time.perf_counter()
    status_code: int | None = None
    error: str | None = None
    payload: dict[str, Any] | list[Any] | None = None
    response_excerpt = ""
    try:
        response = await client.request(
            method=method,
            url=path,
            headers=headers,
            json=json_body,
            params=params,
        )
        status_code = response.status_code
        payload = _safe_json_loads(response)
        response_excerpt = _excerpt_from_payload(
            payload=payload,
            fallback_text=response.text,
        )
    except Exception as exc:  # noqa: BLE001
        error = str(exc)
        response_excerpt = _truncate(error)

    duration = time.perf_counter() - started
    ok = status_code in expected_statuses if error is None else False
    result = StepResult(
        name=name,
        method=method.upper(),
        path=path,
        status_code=status_code,
        ok=ok,
        duration_seconds=duration,
        error=error,
        response_excerpt=response_excerpt,
    )
    return result, payload


async def _resolve_client_mode(
    *,
    requested_mode: str,
    base_url: str,
    timeout_seconds: float,
) -> str:
    if requested_mode in {"http", "asgi"}:
        return requested_mode

    probe_timeout = min(timeout_seconds, 3.0)
    try:
        async with httpx.AsyncClient(base_url=base_url, timeout=probe_timeout) as client:
            response = await client.get("/health")
            if response.status_code < 500:
                return "http"
    except Exception:  # noqa: BLE001
        pass
    return "asgi"


async def _create_client(
    *,
    mode: str,
    base_url: str,
    timeout_seconds: float,
    asgi_sqlite_path: str | None,
) -> tuple[httpx.AsyncClient, str]:
    if mode == "http":
        return (
            httpx.AsyncClient(
                base_url=base_url.rstrip("/"),
                timeout=timeout_seconds,
            ),
            "http",
        )

    if asgi_sqlite_path:
        os.environ["USE_SQLITE"] = "true"
        os.environ["SQLITE_PATH"] = asgi_sqlite_path

    importlib.invalidate_caches()
    for module_name in tuple(sys.modules.keys()):
        if module_name == "munipal" or module_name.startswith("munipal."):
            del sys.modules[module_name]

    from munipal.config import get_settings
    from munipal.db.session import init_db
    from munipal.main import app

    get_settings.cache_clear()
    settings = get_settings()
    if settings.use_sqlite:
        await init_db()

    transport = httpx.ASGITransport(app=app)
    return (
        httpx.AsyncClient(
            transport=transport,
            base_url="http://test",
            timeout=timeout_seconds,
        ),
        "asgi",
    )


async def _ensure_asgi_user_exists(*, user_id: str, tenant_id: str) -> bool:
    try:
        from munipal.core.models.user import User
        from munipal.db.session import AsyncSessionLocal

        async with AsyncSessionLocal() as session:
            existing = await session.get(User, user_id)
            if existing:
                return False
            session.add(
                User(
                    id=user_id,
                    email=f"{user_id}@phase10-smoke.local",
                    hashed_password="phase10-smoke",
                    is_superuser=True,
                    organization=tenant_id,
                )
            )
            await session.commit()
            return True
    except Exception:  # noqa: BLE001
        return False


async def _run_smoke(
    *,
    mode: str,
    base_url: str,
    timeout_seconds: float,
    asgi_sqlite_path: str | None,
    project_id: str | None,
    generated_for: str,
    title: str,
    include_disclosure: bool,
    auth_headers: dict[str, str],
) -> dict[str, Any]:
    steps: list[StepResult] = []
    effective_project_id: str | None = project_id
    created_project_id: str | None = None
    report_id: str | None = None
    package_id: str | None = None
    internal_report_payload: dict[str, Any] | None = None
    external_package_payload: dict[str, Any] | None = None
    external_validate_payload: dict[str, Any] | None = None

    client_mode = await _resolve_client_mode(
        requested_mode=mode,
        base_url=base_url.rstrip("/"),
        timeout_seconds=timeout_seconds,
    )
    effective_asgi_sqlite_path = asgi_sqlite_path
    if client_mode == "asgi" and not effective_asgi_sqlite_path:
        fd, generated_db_path = tempfile.mkstemp(
            prefix="munipal_advisory_smoke_",
            suffix=".db",
        )
        os.close(fd)
        Path(generated_db_path).unlink(missing_ok=True)
        effective_asgi_sqlite_path = generated_db_path

    client, resolved_mode = await _create_client(
        mode=client_mode,
        base_url=base_url.rstrip("/"),
        timeout_seconds=timeout_seconds,
        asgi_sqlite_path=effective_asgi_sqlite_path,
    )

    async with client:
        health_step, _ = await _request_step(
            client=client,
            name="Health Check",
            method="GET",
            path="/health",
            headers=auth_headers,
            expected_statuses=(200,),
        )
        steps.append(health_step)

        default_playbook_id: str | None = None
        default_playbook_step, default_playbook_payload = await _request_step(
            client=client,
            name="Get Default Playbook",
            method="GET",
            path="/api/v1/playbooks/default",
            headers=auth_headers,
            expected_statuses=(200, 404),
        )
        steps.append(default_playbook_step)

        if default_playbook_step.status_code == 404:
            seed_step, _ = await _request_step(
                client=client,
                name="Seed Default Playbook",
                method="POST",
                path="/api/v1/playbooks/seed",
                headers=auth_headers,
                expected_statuses=(201, 200),
            )
            steps.append(seed_step)
            if seed_step.ok:
                default_playbook_step, default_playbook_payload = await _request_step(
                    client=client,
                    name="Get Default Playbook (After Seed)",
                    method="GET",
                    path="/api/v1/playbooks/default",
                    headers=auth_headers,
                    expected_statuses=(200,),
                )
                steps.append(default_playbook_step)

        if isinstance(default_playbook_payload, dict):
            raw_playbook_id = default_playbook_payload.get("id")
            if isinstance(raw_playbook_id, str) and raw_playbook_id.strip():
                default_playbook_id = raw_playbook_id.strip()

        if not effective_project_id:
            list_projects_step, list_projects_payload = await _request_step(
                client=client,
                name="List Projects",
                method="GET",
                path="/api/v1/projects/",
                headers=auth_headers,
                expected_statuses=(200,),
                params={"limit": 1, "skip": 0},
            )
            steps.append(list_projects_step)

            if (
                list_projects_step.ok
                and isinstance(list_projects_payload, dict)
                and isinstance(list_projects_payload.get("projects"), list)
                and list_projects_payload.get("projects")
            ):
                first_project = list_projects_payload["projects"][0]
                if isinstance(first_project, dict):
                    raw_project_id = first_project.get("id")
                    if isinstance(raw_project_id, str) and raw_project_id.strip():
                        effective_project_id = raw_project_id.strip()

        if not effective_project_id:
            if resolved_mode == "asgi":
                await _ensure_asgi_user_exists(
                    user_id=auth_headers.get("X-User-Id", DEFAULT_USER_ID),
                    tenant_id=auth_headers.get("X-Tenant-Id", DEFAULT_TENANT_ID),
                )
            create_project_payload: dict[str, Any] = {
                "name": f"Phase10 Advisory Smoke {_timestamp()}",
                "description": "Automated advisory package smoke validation project.",
                "issuer_name": "Phase10 Smoke Issuer",
                "project_location": "AZ",
                "target_bond_amount": 75_000_000,
            }
            if default_playbook_id:
                create_project_payload["playbook_id"] = default_playbook_id

            create_project_step, create_project_response = await _request_step(
                client=client,
                name="Create Smoke Project",
                method="POST",
                path="/api/v1/projects/",
                headers=auth_headers,
                expected_statuses=(201,),
                json_body=create_project_payload,
            )
            steps.append(create_project_step)
            if create_project_step.ok and isinstance(create_project_response, dict):
                raw_created_id = create_project_response.get("id")
                if isinstance(raw_created_id, str) and raw_created_id.strip():
                    created_project_id = raw_created_id.strip()
                    effective_project_id = created_project_id

        if effective_project_id:
            internal_generate_step, internal_generate_payload = await _request_step(
                client=client,
                name="Generate Internal Advisory Report",
                method="POST",
                path="/api/v1/advisory-packages/internal/generate",
                headers=auth_headers,
                expected_statuses=(200,),
                json_body={
                    "project_id": effective_project_id,
                    "force_regenerate": False,
                },
            )
            steps.append(internal_generate_step)
            if internal_generate_step.ok and isinstance(internal_generate_payload, dict):
                raw_report_id = internal_generate_payload.get("report_id")
                if isinstance(raw_report_id, str) and raw_report_id.strip():
                    report_id = raw_report_id.strip()

            if report_id:
                internal_fetch_step, internal_fetch_payload = await _request_step(
                    client=client,
                    name="Fetch Internal Advisory Report",
                    method="GET",
                    path=f"/api/v1/advisory-packages/internal/{report_id}",
                    headers=auth_headers,
                    expected_statuses=(200,),
                )
                steps.append(internal_fetch_step)
                if isinstance(internal_fetch_payload, dict):
                    internal_report_payload = internal_fetch_payload

                internal_export_step, _ = await _request_step(
                    client=client,
                    name="Export Internal Advisory Report (MD)",
                    method="GET",
                    path=f"/api/v1/advisory-packages/internal/{report_id}/export",
                    headers=auth_headers,
                    params={"format": "md"},
                    expected_statuses=(200,),
                )
                steps.append(internal_export_step)

            external_generate_step, external_generate_payload = await _request_step(
                client=client,
                name="Generate External Advisory Package",
                method="POST",
                path="/api/v1/advisory-packages/external/generate",
                headers=auth_headers,
                expected_statuses=(200,),
                json_body={
                    "project_id": effective_project_id,
                    "title": title,
                    "generated_for": generated_for,
                    "include_disclosure": include_disclosure,
                    "force_regenerate": False,
                },
            )
            steps.append(external_generate_step)
            if external_generate_step.ok and isinstance(external_generate_payload, dict):
                raw_package_id = external_generate_payload.get("package_id")
                if isinstance(raw_package_id, str) and raw_package_id.strip():
                    package_id = raw_package_id.strip()

            if package_id:
                external_fetch_step, external_fetch_payload = await _request_step(
                    client=client,
                    name="Fetch External Advisory Package",
                    method="GET",
                    path=f"/api/v1/advisory-packages/external/{package_id}",
                    headers=auth_headers,
                    expected_statuses=(200,),
                )
                steps.append(external_fetch_step)
                if isinstance(external_fetch_payload, dict):
                    external_package_payload = external_fetch_payload

                external_validate_step, external_validate_response = await _request_step(
                    client=client,
                    name="Validate External Advisory Package",
                    method="GET",
                    path=f"/api/v1/advisory-packages/external/{package_id}/validate",
                    headers=auth_headers,
                    expected_statuses=(200,),
                )
                steps.append(external_validate_step)
                if isinstance(external_validate_response, dict):
                    external_validate_payload = external_validate_response

                external_export_step, _ = await _request_step(
                    client=client,
                    name="Export External Advisory Package (MD)",
                    method="GET",
                    path=f"/api/v1/advisory-packages/external/{package_id}/export",
                    headers=auth_headers,
                    params={"format": "md"},
                    expected_statuses=(200,),
                )
                steps.append(external_export_step)

    by_name = {step.name: step for step in steps}
    assertions = {
        "project_id_resolved": bool(effective_project_id),
        "internal_generate_ok": by_name.get("Generate Internal Advisory Report", StepResult("", "", "", None, False, 0, None, None)).ok,
        "internal_report_fetch_ok": by_name.get("Fetch Internal Advisory Report", StepResult("", "", "", None, False, 0, None, None)).ok,
        "external_generate_ok": by_name.get("Generate External Advisory Package", StepResult("", "", "", None, False, 0, None, None)).ok,
        "external_package_fetch_ok": by_name.get("Fetch External Advisory Package", StepResult("", "", "", None, False, 0, None, None)).ok,
        "external_validate_ok": by_name.get("Validate External Advisory Package", StepResult("", "", "", None, False, 0, None, None)).ok,
    }

    recommendation, reasons = _recommendation_from_assertions(assertions)
    risk_integration_mode = None
    if isinstance(external_package_payload, dict):
        summary = external_package_payload.get("executive_summary")
        if isinstance(summary, dict):
            key_metrics = summary.get("key_metrics")
            if isinstance(key_metrics, dict):
                raw_mode = key_metrics.get("Risk Integration Mode")
                if isinstance(raw_mode, str) and raw_mode.strip():
                    risk_integration_mode = raw_mode.strip()

    summary_payload = {
        "internal_report_id": report_id,
        "external_package_id": package_id,
        "internal_overall_score": (
            internal_report_payload.get("overall_score")
            if isinstance(internal_report_payload, dict)
            else None
        ),
        "external_ready_for_distribution": (
            external_package_payload.get("ready_for_distribution")
            if isinstance(external_package_payload, dict)
            else None
        ),
        "external_distribution_issue_count": (
            len(external_validate_payload.get("issues", []))
            if isinstance(external_validate_payload, dict)
            and isinstance(external_validate_payload.get("issues"), list)
            else None
        ),
        "risk_integration_mode": risk_integration_mode,
    }

    return {
        "mode": resolved_mode,
        "base_url": base_url.rstrip("/"),
        "asgi_sqlite_path": (
            effective_asgi_sqlite_path if resolved_mode == "asgi" else None
        ),
        "project_id_input": project_id,
        "project_id_resolved": effective_project_id,
        "project_id_created": created_project_id,
        "assertions": assertions,
        "summary": summary_payload,
        "steps": [asdict(step) for step in steps],
        "recommendation": {
            "status": recommendation,
            "reasons": reasons,
        },
    }


def _write_markdown(path: Path, payload: dict[str, Any]) -> None:
    recommendation = payload["recommendation"]
    summary = payload["summary"]
    assertions = payload["assertions"]
    lines = [
        "# Advisory Package Smoke Assessment",
        "",
        f"- Generated (UTC): `{payload['generated_at_utc']}`",
        f"- Mode: `{payload['mode']}`",
        f"- Base URL: `{payload['base_url']}`",
        f"- ASGI sqlite path: `{payload.get('asgi_sqlite_path')}`",
        f"- Recommendation: `{recommendation['status']}`",
        f"- Project used: `{payload.get('project_id_resolved')}`",
        f"- Project created by script: `{payload.get('project_id_created')}`",
        "",
        "## Step Results",
        "",
        "| Step | Method | Path | Status | Duration (s) |",
        "|---|---|---|---:|---:|",
    ]
    for step in payload.get("steps", []):
        lines.append(
            f"| {step['name']} | {step['method']} | {step['path']} | "
            f"{step['status_code']} | {step['duration_seconds']:.2f} |"
        )

    lines.extend(
        [
            "",
            "## Assertions",
            "",
            "| Assertion | Result |",
            "|---|---|",
        ]
    )
    for key, value in assertions.items():
        lines.append(f"| {key} | {value} |")

    lines.extend(
        [
            "",
            "## Summary",
            "",
            f"- Internal report id: `{summary.get('internal_report_id')}`",
            f"- External package id: `{summary.get('external_package_id')}`",
            f"- Internal overall score: `{summary.get('internal_overall_score')}`",
            f"- External ready_for_distribution: `{summary.get('external_ready_for_distribution')}`",
            f"- External distribution issue count: `{summary.get('external_distribution_issue_count')}`",
            f"- External risk integration mode: `{summary.get('risk_integration_mode')}`",
            "",
            "## Recommendation Notes",
            "",
        ]
    )
    if recommendation["reasons"]:
        for reason in recommendation["reasons"]:
            lines.append(f"- {reason}")
    else:
        lines.append("- No blocking smoke issues detected.")

    linked = payload.get("linked_artifacts", {})
    if linked:
        lines.extend(["", "## Linked Artifacts", ""])
        for key, value in linked.items():
            lines.append(f"- {key}: `{value}`")

    path.write_text("\n".join(lines), encoding="utf-8")


def assess_advisory_package_smoke(
    *,
    output_dir: Path,
    mode: str,
    base_url: str,
    timeout_seconds: float,
    asgi_sqlite_path: str | None,
    project_id: str | None,
    title: str,
    generated_for: str,
    include_disclosure: bool,
    bearer_token: str | None,
    jwt_secret_key: str | None,
    jwt_algorithm: str,
    token_ttl_minutes: int,
    user_id: str,
    role: str,
    tenant_id: str,
    tenant_claim_key: str,
) -> AssessmentResult:
    output_dir.mkdir(parents=True, exist_ok=True)
    token, token_mode = _build_bearer_token(
        explicit_token=bearer_token,
        user_id=user_id,
        role=role,
        tenant_id=tenant_id,
        tenant_claim_key=tenant_claim_key,
        secret_key=jwt_secret_key,
        algorithm=jwt_algorithm,
        ttl_minutes=token_ttl_minutes,
    )
    headers = _build_headers(
        bearer_token=token,
        user_id=user_id,
        role=role,
        tenant_id=tenant_id,
    )

    smoke_payload = asyncio.run(
        _run_smoke(
            mode=mode,
            base_url=base_url,
            timeout_seconds=timeout_seconds,
            asgi_sqlite_path=asgi_sqlite_path,
            project_id=project_id,
            generated_for=generated_for,
            title=title,
            include_disclosure=include_disclosure,
            auth_headers=headers,
        )
    )

    advisory_cohort_artifact = _latest_artifact_name(
        output_dir=output_dir,
        pattern="advisory_cohort_inference_*.json",
    )
    payload = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "mode": smoke_payload["mode"],
        "base_url": smoke_payload["base_url"],
        "asgi_sqlite_path": smoke_payload.get("asgi_sqlite_path"),
        "auth": {
            "token_mode": token_mode,
            "user_id": user_id,
            "role": role,
            "tenant_id": tenant_id,
            "tenant_claim_key": tenant_claim_key,
        },
        "project_id_input": smoke_payload.get("project_id_input"),
        "project_id_resolved": smoke_payload.get("project_id_resolved"),
        "project_id_created": smoke_payload.get("project_id_created"),
        "assertions": smoke_payload["assertions"],
        "summary": smoke_payload["summary"],
        "steps": smoke_payload["steps"],
        "linked_artifacts": {
            "latest_advisory_cohort_inference_json": advisory_cohort_artifact,
        },
        "recommendation": smoke_payload["recommendation"],
    }

    stamp = _timestamp()
    report_json_path = output_dir / f"advisory_package_smoke_{stamp}.json"
    report_md_path = output_dir / f"advisory_package_smoke_{stamp}.md"
    report_json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    _write_markdown(report_md_path, payload)

    recommendation = payload["recommendation"]["status"]
    reasons = list(payload["recommendation"]["reasons"])
    return AssessmentResult(
        report_json_path=report_json_path,
        report_md_path=report_md_path,
        recommendation=recommendation,
        reasons=reasons,
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run advisory package generation smoke assessment.",
    )
    parser.add_argument(
        "--mode",
        choices=("auto", "http", "asgi"),
        default="auto",
        help="Client mode: auto (try http then fallback asgi), http, or asgi.",
    )
    parser.add_argument(
        "--base-url",
        default=os.getenv("MUNIPAL_API_BASE_URL", DEFAULT_BASE_URL),
        help="Base URL for live API calls in http mode.",
    )
    parser.add_argument(
        "--asgi-sqlite-path",
        default=None,
        help="Optional sqlite path override for ASGI mode; defaults to ephemeral temp DB.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=30.0,
        help="Request timeout in seconds.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=_default_output_dir(),
        help="Output directory for markdown/json report artifacts.",
    )
    parser.add_argument(
        "--project-id",
        default=None,
        help="Optional explicit project UUID; if omitted the script resolves or creates one.",
    )
    parser.add_argument(
        "--title",
        default="Phase 10 Advisory Package Smoke",
        help="External package title used for generation.",
    )
    parser.add_argument(
        "--generated-for",
        default="Municipal Advisor",
        help="External package audience.",
    )
    parser.add_argument(
        "--include-disclosure",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Whether to include disclosure synthesis during external package generation.",
    )
    parser.add_argument(
        "--bearer-token",
        default=None,
        help="Optional pre-issued bearer token. If omitted, token may be generated from JWT secret.",
    )
    parser.add_argument(
        "--jwt-secret-key",
        default=None,
        help="JWT secret for generated bearer token (fallback: JWT_SECRET_KEY env).",
    )
    parser.add_argument(
        "--jwt-algorithm",
        default=os.getenv("JWT_ALGORITHM", "HS256"),
        help="JWT algorithm for generated token.",
    )
    parser.add_argument(
        "--token-ttl-minutes",
        type=int,
        default=15,
        help="Generated token TTL in minutes.",
    )
    parser.add_argument(
        "--user-id",
        default=DEFAULT_USER_ID,
        help="User id claim/header used for auth.",
    )
    parser.add_argument(
        "--role",
        default=DEFAULT_ROLE,
        help="Role claim/header used for auth.",
    )
    parser.add_argument(
        "--tenant-id",
        default=DEFAULT_TENANT_ID,
        help="Tenant claim/header used for auth.",
    )
    parser.add_argument(
        "--tenant-claim-key",
        default="tenant_id",
        help="Tenant claim key in generated JWT (e.g., tenant_id, tenant, org).",
    )
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    result = assess_advisory_package_smoke(
        output_dir=args.output_dir.resolve(),
        mode=args.mode,
        base_url=str(args.base_url),
        timeout_seconds=float(args.timeout_seconds),
        asgi_sqlite_path=(
            str(args.asgi_sqlite_path).strip() if args.asgi_sqlite_path else None
        ),
        project_id=str(args.project_id).strip() if args.project_id else None,
        title=str(args.title),
        generated_for=str(args.generated_for),
        include_disclosure=bool(args.include_disclosure),
        bearer_token=args.bearer_token,
        jwt_secret_key=args.jwt_secret_key,
        jwt_algorithm=str(args.jwt_algorithm),
        token_ttl_minutes=int(args.token_ttl_minutes),
        user_id=str(args.user_id),
        role=str(args.role).strip().lower(),
        tenant_id=str(args.tenant_id),
        tenant_claim_key=str(args.tenant_claim_key),
    )
    print(f"[advisory-package-smoke] recommendation={result.recommendation}")
    print(f"[advisory-package-smoke] markdown={result.report_md_path.as_posix()}")
    print(f"[advisory-package-smoke] json={result.report_json_path.as_posix()}")
    if result.reasons:
        print("[advisory-package-smoke] reasons:")
        for reason in result.reasons:
            print(f"- {reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
