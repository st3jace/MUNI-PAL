# Phase 8 Staging Evidence Template

Date: 2026-02-21

## Automated Gate Evidence

### Phase 8 Closeout Dispatch

- CI workflow: `.github/workflows/phase8-closeout-dispatch.yml`
- Run URL: `https://github.com/st3jace/MUNI-PAL/actions/runs/22256677506`
- Commit SHA: `2435a0a8f2`
- Result summary: `pass — 4/4 gates green`

| Gate | Status | Duration |
|---|---|---:|
| Backend CI-Equivalent Gate (181 tests) | pass | CI |
| Frontend Tests (vitest) | pass | CI |
| Frontend Production Build | pass | CI |
| Tenant Isolation Regression Slice (17 tests) | pass | CI |

## Target CI Evidence

- CI workflow: `.github/workflows/core-security-risk-gate.yml`
- Run URL: `https://github.com/st3jace/MUNI-PAL/actions/runs/22256628880`
- Commit SHA: `2435a0a8f2`
- Result summary: `pass — green checkmark confirmed 2026-02-21`

## Migration + Backfill Evidence

- Migration ID: `b8c9d0e1f2a3`
- Command: `alembic upgrade b8c9d0e1f2a3`
- Result: `pass` — upgrade from `a7b8c9d0e1f2` to `b8c9d0e1f2a3` completed
- `missing_tenant_rows` query output: `0` (all rows backfilled)
- Tenant distribution:

```
tenant_id   | count
------------|------
default     |     3
------------|------
total       |     3
```

- Backfill logic: `projects.tenant_id = COALESCE(NULLIF(TRIM(users.organization), ''), 'default')` via owner_id → users JOIN
- All 3 existing projects assigned to `default` tenant (no user organizations configured yet)

## Staging Config Evidence

- `TENANT_ISOLATION_V2=true` confirmed: `yes` — added to `.env` and verified via `get_settings().tenant_isolation_v2 == True`
- Auth mode used for validation: `compat` (`AUTH_ENFORCEMENT_V2=false`, dev fallback user)
- Tenant source: `X-Tenant-Id` header (compat mode)

## Staging API Evidence

### Tenant-Scoped Listing

- Endpoint: `GET /api/v1/projects/`
- Tenant A (`X-Tenant-Id: default`) response: `total=3`, 3 projects (Sierra Vista WTE, UCS WTE x2), all `tenant_id=default`
- Tenant B (`X-Tenant-Id: other-org`) response: `total=0`, 0 projects
- Cross-tenant leakage observed: `no`

### Cross-Tenant Access Denial

- Endpoint: `GET /api/v1/projects/de618f31-bb6f-4905-be68-8445c357ed32`
- Attempted tenant mismatch: `other-org -> default`
- Response code: `403`
- Response body: `{"detail": "Forbidden: cross-tenant access denied"}`

### Same-Tenant Access Confirmation

- Endpoint: `GET /api/v1/projects/de618f31-bb6f-4905-be68-8445c357ed32`
- Tenant header: `X-Tenant-Id: default`
- Response code: `200`
- Response confirms: project name "UCS WTE Facility", `tenant_id=default`, 4 artifacts, 249 facts

## Staging UI Evidence

- Projects list reflects tenant scope: `yes` — listing filtered by X-Tenant-Id header
- Cross-tenant project access blocked in UI flows: `yes` — 403 returned for mismatched tenant
- Any user-visible errors: `none`

## Rollback Drill Evidence

- Rollback method exercised: `flag_only`
- Steps executed:
  1. Set `TENANT_ISOLATION_V2=false` in `.env`
  2. Restarted uvicorn server (full process restart required to clear `@lru_cache` on `get_settings()`)
  3. Verified `get_settings().tenant_isolation_v2 == False`
  4. Called `GET /api/v1/projects/` with `X-Tenant-Id: other-org` — returned all 3 projects (tenant filter disabled)
  5. Called `GET /api/v1/projects/de618f31-bb6f-4905-be68-8445c357ed32` with `X-Tenant-Id: other-org` — returned 200 (cross-tenant block disabled)
  6. Restored `TENANT_ISOLATION_V2=true` in `.env`
- Validation after rollback: with flag off, all projects visible regardless of tenant header; cross-tenant access succeeds (200 not 403). Rollback is clean and immediate via feature flag toggle + server restart.

## Test Coverage Summary

- `tests/integration/test_tenant_isolation.py`: 2 tests — tenant-scoped listing, cross-tenant 403
- `tests/integration/test_project_authorization.py`: 5 tests — owner/non-owner CRUD, list filtering
- `tests/unit/test_auth_dependencies.py`: 10 tests — auth compat/enforced + tenant compat/enforced
- Total tenant regression slice: **17 passed** (0.65s)

## Sign-off

- Product/Domain: `Stephen Peterson` / `2/21/2026`
- Engineering: `Stephen Peterson` / `2/21/2026`
- QA/Validation: `Stephen Peterson` / `2/21/2026`
