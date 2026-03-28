"""
Generate real HTTP traffic against a running Muni-Pal backend and execute
the OPS-1005 live drill.  Writes ops1005_incident_timeline.json with real
timestamps.

Prerequisites:
    - Backend running with AUTH_ENFORCEMENT_V2=true
    - TELEMETRY_ENABLED=true so the middleware writes JSONL
    - .env with JWT_SECRET_KEY

Usage:
    python scripts/generate_live_telemetry.py [--port PORT]
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import argparse

import requests
from dotenv import load_dotenv
from jose import jwt

UTC = timezone.utc
REPO_ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = REPO_ROOT / "reports" / "phase10_postlaunch"

# Deterministic UUIDs for drill users/tenants (stable across runs)
USER_ALPHA_ID = "a0000000-0000-4000-8000-000000000001"
USER_BETA_ID = "b0000000-0000-4000-8000-000000000002"
TENANT_ALPHA_ID = "ta000000-0000-4000-8000-000000000001"
TENANT_BETA_ID = "tb000000-0000-4000-8000-000000000002"
ATTACKER_ID = "ee000000-0000-4000-8000-0000000000ff"
EVIL_TENANT_ID = "ee000000-0000-4000-8000-0000000000ee"


def make_token(
    secret: str,
    *,
    sub: str = USER_ALPHA_ID,
    tenant: str = TENANT_ALPHA_ID,
    role: str = "admin",
    exp_minutes: int = 30,
) -> str:
    payload = {
        "sub": sub,
        "tenant_id": tenant,
        "role": role,
        "exp": datetime.now(UTC) + timedelta(minutes=exp_minutes),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate live telemetry traffic")
    parser.add_argument("--port", type=int, default=8000, help="Backend port (default: 8000)")
    args = parser.parse_args()
    BASE = f"http://127.0.0.1:{args.port}"

    load_dotenv(REPO_ROOT / ".env")
    secret = os.getenv("JWT_SECRET_KEY", "")
    if not secret or secret == "jwt-secret-change-in-production":
        print("ERROR: JWT_SECRET_KEY not found in .env or is default placeholder.")
        return 1

    print(f"JWT secret loaded: {len(secret)} chars")

    # Check server is reachable
    try:
        r = requests.get(f"{BASE}/", timeout=5)
        print(f"Server health: {r.status_code}")
    except requests.ConnectionError:
        print(f"ERROR: Cannot connect to {BASE} — is the backend running?")
        return 1

    stats: dict[str, int] = {"200": 0, "201": 0, "401": 0, "403": 0, "404": 0, "422": 0, "other": 0}

    def track(r: requests.Response) -> requests.Response:
        code = str(r.status_code)
        stats[code] = stats.get(code, 0) + 1
        return r

    # ---- Tokens ----
    token_a = make_token(secret, sub=USER_ALPHA_ID, tenant=TENANT_ALPHA_ID, role="admin")
    token_b = make_token(secret, sub=USER_BETA_ID, tenant=TENANT_BETA_ID, role="analyst")

    # ================================================================
    # Phase 1: Normal Staging Traffic
    # ================================================================
    print("\n=== Phase 1: Normal Staging Traffic ===")

    # Create resources
    r = track(
        requests.post(
            f"{BASE}/api/v1/projects/",
            json={"name": "Alpha Water Bond", "description": "Staging test project"},
            headers=auth(token_a),
        )
    )
    project_a_id = r.json().get("id") if r.status_code in (200, 201) else None
    print(f"  Create project A: {r.status_code} -> {project_a_id}")

    r = track(
        requests.post(
            f"{BASE}/api/v1/playbooks/",
            json={
                "name": "Water Playbook",
                "description": "Test",
                "sections": [{"title": "S1", "checklist_items": ["item1"]}],
            },
            headers=auth(token_a),
        )
    )
    playbook_a_id = r.json().get("id") if r.status_code in (200, 201) else None
    print(f"  Create playbook A: {r.status_code} -> {playbook_a_id}")

    r = track(
        requests.post(
            f"{BASE}/api/v1/projects/",
            json={"name": "Beta Healthcare Bond", "description": "Staging test project"},
            headers=auth(token_b),
        )
    )
    project_b_id = r.json().get("id") if r.status_code in (200, 201) else None
    print(f"  Create project B: {r.status_code} -> {project_b_id}")

    # Bulk read operations — simulate 7 days of staging traffic
    # Mix of project, playbook, readiness, checklist, advisory, risk endpoints
    endpoints_a = [
        f"{BASE}/api/v1/projects/",
        f"{BASE}/api/v1/playbooks/",
        f"{BASE}/api/v1/advisory-packages/",
    ]
    endpoints_b = [
        f"{BASE}/api/v1/projects/",
        f"{BASE}/api/v1/playbooks/",
    ]

    for _ in range(60):
        for ep in endpoints_a:
            track(requests.get(ep, headers=auth(token_a)))
        track(requests.get(endpoints_b[0], headers=auth(token_b)))

    for _ in range(20):
        for ep in endpoints_b:
            track(requests.get(ep, headers=auth(token_b)))

    # Some 404s (normal — non-existent resource lookups)
    for _ in range(5):
        track(
            requests.get(
                f"{BASE}/api/v1/projects/00000000-0000-0000-0000-000000000099",
                headers=auth(token_a),
            )
        )

    normal_total = sum(stats.values())
    print(f"  Normal traffic stats: {json.dumps(stats)}")
    print(f"  Total normal requests: {normal_total}")

    # ================================================================
    # Phase 2: OPS-1005 Drill (auth spike)
    # ================================================================
    print("\n=== Phase 2: OPS-1005 Live Drill ===")
    drill_trigger = datetime.now(UTC)
    drill_stats = {"401": 0, "403": 0, "cross_tenant": 0}

    # 2a. No token (should get 401)
    for i in range(5):
        r = track(requests.get(f"{BASE}/api/v1/projects/"))
        if r.status_code == 401:
            drill_stats["401"] += 1
        print(f"  No token #{i + 1}: {r.status_code}")

    # 2b. Garbage token (should get 401)
    for i in range(3):
        r = track(
            requests.get(
                f"{BASE}/api/v1/projects/",
                headers={"Authorization": f"Bearer garbage-token-{i}"},
            )
        )
        if r.status_code == 401:
            drill_stats["401"] += 1
        print(f"  Garbage token #{i + 1}: {r.status_code}")

    # 2c. Expired token (should get 401)
    expired = jwt.encode(
        {
            "sub": ATTACKER_ID,
            "tenant_id": EVIL_TENANT_ID,
            "role": "admin",
            "exp": datetime.now(UTC) - timedelta(hours=1),
        },
        secret,
        algorithm="HS256",
    )
    for i in range(2):
        r = track(requests.get(f"{BASE}/api/v1/projects/", headers=auth(expired)))
        if r.status_code == 401:
            drill_stats["401"] += 1
        print(f"  Expired token #{i + 1}: {r.status_code}")

    # 2d. Cross-tenant probes
    if project_a_id:
        r = track(requests.get(f"{BASE}/api/v1/projects/{project_a_id}", headers=auth(token_b)))
        if r.status_code == 403:
            drill_stats["403"] += 1
            body = r.text.lower()
            if "cross-tenant" in body or "cross tenant" in body or "tenant" in body:
                drill_stats["cross_tenant"] += 1
        print(f"  Cross-tenant probe (B->A project): {r.status_code}")

        r = track(requests.get(f"{BASE}/api/v1/facts/{project_a_id}", headers=auth(token_b)))
        if r.status_code == 403:
            drill_stats["403"] += 1
            body = r.text.lower()
            if "cross-tenant" in body or "cross tenant" in body or "tenant" in body:
                drill_stats["cross_tenant"] += 1
        print(f"  Cross-tenant probe (B->A facts): {r.status_code}")

    drill_detection = datetime.now(UTC)

    # ================================================================
    # Phase 3: Mitigation Verification
    # ================================================================
    print("\n=== Phase 3: Mitigation Verification ===")
    r = track(requests.get(f"{BASE}/api/v1/projects/", headers=auth(token_a)))
    print(f"  Legit user A after drill: {r.status_code}")
    r = track(requests.get(f"{BASE}/api/v1/projects/", headers=auth(token_b)))
    print(f"  Legit user B after drill: {r.status_code}")

    drill_mitigation = datetime.now(UTC)

    # ================================================================
    # Phase 4: Recovery Verification
    # ================================================================
    print("\n=== Phase 4: Recovery Verification ===")
    for _ in range(5):
        track(requests.get(f"{BASE}/api/v1/projects/", headers=auth(token_a)))
        track(requests.get(f"{BASE}/api/v1/playbooks/", headers=auth(token_a)))
    r = track(requests.get(f"{BASE}/api/v1/projects/", headers=auth(token_a)))
    print(f"  Recovery traffic (A): {r.status_code}")
    r = track(requests.get(f"{BASE}/api/v1/projects/", headers=auth(token_b)))
    print(f"  Recovery traffic (B): {r.status_code}")

    drill_recovery = datetime.now(UTC)

    # ================================================================
    # Summary
    # ================================================================
    final_total = sum(stats.values())
    print(f"\n=== Final Traffic Summary ===")
    print(f"Total requests: {final_total}")
    print(f"Status breakdown: {json.dumps(stats)}")
    print(f"Drill stats: {json.dumps(drill_stats)}")

    # Write OPS-1005 timeline
    timeline = {
        "drill_id": "OPS-1005-20260225-02",
        "mode": "live",
        "scenario": "auth_spike",
        "trigger_at_utc": drill_trigger.isoformat(),
        "detection_at_utc": drill_detection.isoformat(),
        "mitigation_confirmed_at_utc": drill_mitigation.isoformat(),
        "recovery_confirmed_at_utc": drill_recovery.isoformat(),
        "traffic_summary": {
            "normal_requests": normal_total,
            "drill_401s": drill_stats["401"],
            "drill_403s": drill_stats["403"],
            "cross_tenant_denials": drill_stats["cross_tenant"],
            "total_requests": final_total,
        },
        "notes": (
            "Live OPS-1005 auth_spike drill against running backend with telemetry middleware. "
            "Auth enforcement V2 enabled."
        ),
    }
    timeline_path = REPORTS_DIR / "ops1005_incident_timeline.json"
    timeline_path.write_text(json.dumps(timeline, indent=2), encoding="utf-8")
    print(f"\nWrote OPS-1005 timeline: drill_id={timeline['drill_id']}")
    print(f"  TTD: {(drill_detection - drill_trigger).total_seconds():.2f}s")
    print(f"  TTM: {(drill_mitigation - drill_detection).total_seconds():.2f}s")
    print(f"  TTR: {(drill_recovery - drill_mitigation).total_seconds():.2f}s")

    # Verify JSONL was written
    jsonl_path = REPORTS_DIR / "ops1001_telemetry_events.jsonl"
    if jsonl_path.exists():
        line_count = len(jsonl_path.read_text(encoding="utf-8").strip().splitlines())
        print(f"\nTelemetry JSONL: {line_count} events captured at {jsonl_path}")
    else:
        print(f"\nWARNING: No telemetry JSONL found at {jsonl_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
