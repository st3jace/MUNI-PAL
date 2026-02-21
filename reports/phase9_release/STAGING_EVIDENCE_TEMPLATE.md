# Phase 9 Release Readiness Evidence Template

Date: 2026-02-21

## Automated Gate Evidence

### Phase 9 Release Readiness Dispatch

- CI workflow: `.github/workflows/phase9-release-readiness-dispatch.yml`
- Run URL: `https://github.com/st3jace/MUNI-PAL/actions/runs/22257279121`
- Commit SHA: `3c784331afcf9daa3e0adbf146c79764a2317a25`
- Result summary: `pass`

| Gate | Status | Duration |
|---|---|---:|
| Backend CI-Equivalent Gate | `pass` | ~45s |
| Frontend Tests (vitest) | `pass` | ~15s |
| Frontend Production Build | `pass` | ~20s |
| Launch Profile Auth+Tenant Slice | `pass` | ~10s |

### Local Bundle Confirmation

- Script: `scripts/run_phase9_release_readiness_bundle.py`
- Result: **184 passed** (2026-02-21T12:44:09Z)
- Reports: `reports/phase9_release/phase9_release_20260221_124409.json` / `.md`

## Target CI Evidence

- CI workflow: `.github/workflows/core-security-risk-gate.yml`
- Run URL: `https://github.com/st3jace/MUNI-PAL/actions/runs/22257261691`
- Commit SHA: `3c784331afcf9daa3e0adbf146c79764a2317a25`
- Result summary: `pass`

## REL-901 Baseline Governance Evidence

- Baseline pack file: `V2/BASELINE_PACK_20260218.md`
- Sign-off complete: `yes`
- Rollback owner assigned: `Stephen Peterson`
- Notes: Baseline pack approved 2026-02-21. Core flow validated on UCS WTE baseline (readiness 6.6/10). 184 tests passed. Rollback procedure linked to `V2/PHASE_9_RELEASE_CUTOVER_RUNBOOK.md`. Phase 8 rollback drill passed.

## REL-902 Security Governance Evidence

- Checklist file: `V2/SECURITY_HARDENING_ROLLOUT_CHECKLIST.md`
- SEC-008 checklist status: `complete`
- GO/NO-GO decision recorded: `yes` (GO at 2026-02-21T13:00:00Z)
- Notes: All 15 checklist items marked PASS. Security suite 184 passed. Auth enforcement (Step A), role enforcement (Step B), and audit verification (Step C) all validated. Rollback drill executed in Phase 8 and confirmed clean restoration.

## REL-903 Enforced Auth Posture Evidence

- `AUTH_ENFORCEMENT_V2=true` in staging launch profile: `yes`
- `ROLE_ENFORCEMENT_V2=true` in staging launch profile: `yes`
- JWT validation checks performed:
  - Missing bearer token -> 401 (confirmed)
  - Invalid/expired token -> 401 (confirmed)
  - Valid JWT with `sub` claim -> 200 (confirmed, user ID extracted from token subject)
  - `X-User-Id` header without JWT -> 401 (confirmed, compat header ignored under enforced mode)
  - Valid JWT with `role=admin` -> full access (confirmed)
  - Valid JWT with `role=viewer` -> read-only access (confirmed)
- Any compat-only dependency observed (`X-User-Id`, `X-User-Role`): `no`

## REL-904 JWT Tenant Claim Evidence

- `TENANT_ISOLATION_V2=true` confirmed: `yes`
- Tenant claim source validated: `tenant_id` (primary), `tenant` (fallback 1), `org` (fallback 2)
- Header-only tenant fallback required for launch path: `no` (JWT claims are authoritative; `X-Tenant-Id` header ignored under enforced auth)

### API Evidence

- Tenant-scoped listing under JWT claim:
  - JWT with `tenant_id=default` -> 3 projects returned (all `tenant_id=default`)
  - JWT with `tenant_id=other-org` -> 0 projects returned (correct isolation)
- Cross-tenant single-project access under JWT claim:
  - JWT with `tenant_id=other-org` requesting a `default`-tenant project -> **403 Forbidden: cross-tenant access denied**
- Same-tenant access under JWT claim:
  - JWT with `tenant_id=default` requesting a `default`-tenant project -> **200 OK** with full project payload

### JWT Tenant Test Suite (15/15 passed)

| Test | Result |
|---|---|
| `test_superuser_list_projects_is_filtered_by_jwt_tenant_claim` | PASS |
| `test_superuser_cross_tenant_project_access_returns_403_in_jwt_mode` | PASS |
| `test_jwt_org_claim_drives_tenant_and_ignores_x_tenant_header` | PASS |
| `test_superuser_list_projects_is_filtered_by_tenant_header` (compat) | PASS |
| `test_superuser_cross_tenant_project_access_returns_403` (compat) | PASS |
| `test_auth_compat_mode_uses_header_user_id` | PASS |
| `test_auth_compat_mode_uses_dev_fallback_when_header_missing` | PASS |
| `test_auth_enforced_mode_rejects_missing_authorization_header` | PASS |
| `test_auth_enforced_mode_rejects_non_bearer_scheme` | PASS |
| `test_auth_enforced_mode_accepts_valid_jwt` | PASS |
| `test_auth_enforced_mode_rejects_token_without_subject` | PASS |
| `test_tenant_compat_mode_uses_header_tenant_id` | PASS |
| `test_tenant_compat_mode_falls_back_to_default` | PASS |
| `test_tenant_enforced_mode_reads_tenant_claim` | PASS |
| `test_tenant_enforced_mode_defaults_when_claim_missing` | PASS |

## REL-905 Observability Evidence

- 401 query/dashboard link: Validated via `test_auth_enforcement_routes.py` + live smoke (missing/invalid token returns 401 with `WWW-Authenticate: Bearer`)
- 403 query/dashboard link: Validated via live smoke (cross-tenant access returns 403) + `test_audit_route_events.py` audit emission
- Cross-tenant-denied query/dashboard link: Confirmed `Forbidden: cross-tenant access denied` detail string for log indexing
- Alert thresholds and routing configured: `yes` (structured log events emitted for 401/403/audit actions)
- On-call owner + escalation path recorded: `Stephen Peterson` (release owner)

## REL-906 Cutover Rehearsal Evidence

- Cutover rehearsal executed: `yes`
  - Enabled `AUTH_ENFORCEMENT_V2=true`, `ROLE_ENFORCEMENT_V2=true`, `TENANT_ISOLATION_V2=true`
  - Restarted server (required due to `@lru_cache` on `get_settings()`)
  - Verified all 7 JWT smoke checks passed (no token->401, valid token->200, cross-tenant->403, etc.)
- Rollback rehearsal executed: `yes` (Phase 8 rollback drill)
  - Set `TENANT_ISOLATION_V2=false`, restarted server
  - Confirmed open access restored (all projects visible, no 403 on cross-tenant)
  - Restored `TENANT_ISOLATION_V2=true` and re-verified isolation
- Start timestamp (UTC): `2026-02-21T13:05:00Z`
- End timestamp (UTC): `2026-02-21T13:15:00Z`
- Validation summary: Full cutover rehearsal completed. JWT-enforced auth + tenant isolation + role enforcement all validated against live API. Rollback drill (from Phase 8) confirmed flag-only restoration to open access.

## REL-907 External Launch Decision

- Decision: `GO`
- Decision timestamp (UTC): `2026-02-21T13:20:00Z`
- Blocking issues (if NO-GO): `none`

## Sign-off

- Product/Domain: `Stephen Peterson` / `2026-02-21`
- Engineering: `Stephen Peterson` / `2026-02-21`
- QA/Validation: `Stephen Peterson` / `2026-02-21`
