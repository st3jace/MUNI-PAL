# Phase 8 Staging Evidence Template

Date: YYYY-MM-DD

## Automated Gate Evidence

### Phase 8 Closeout Dispatch

- CI workflow: `.github/workflows/phase8-closeout-dispatch.yml`
- Run URL: `<paste-url>`
- Commit SHA: `<paste-sha>`
- Result summary: `pass|fail`

| Gate | Status | Duration |
|---|---|---:|
| Backend CI-Equivalent Gate |  |  |
| Frontend Tests (vitest) |  |  |
| Frontend Production Build |  |  |
| Tenant Isolation Regression Slice |  |  |

## Target CI Evidence

- CI workflow: `.github/workflows/core-security-risk-gate.yml`
- Run URL: `<paste-url>`
- Commit SHA: `<paste-sha>`
- Result summary: `pass|fail`

## Migration + Backfill Evidence

- Migration ID: `b8c9d0e1f2a3`
- Command: `alembic upgrade b8c9d0e1f2a3`
- Result: `pass|fail`
- `missing_tenant_rows` query output: `<value>`
- Tenant distribution query output link/screenshot: `<reference>`

## Staging Config Evidence

- `TENANT_ISOLATION_V2=true` confirmed: `yes|no`
- Auth mode used for validation: `compat|enforced`
- Tenant source: `X-Tenant-Id|JWT claim`

## Staging API Evidence

### Tenant-Scoped Listing

- Endpoint: `GET /api/v1/projects`
- Tenant A response summary: `<summary>`
- Tenant B response summary: `<summary>`
- Cross-tenant leakage observed: `yes|no`

### Cross-Tenant Access Denial

- Endpoint: `GET /api/v1/projects/{project_id}`
- Attempted tenant mismatch: `<tenant_a -> tenant_b>`
- Response code: `<code>`
- Response body summary: `<summary>`

## Staging UI Evidence

- Projects list reflects tenant scope: `yes|no`
- Cross-tenant project access blocked in UI flows: `yes|no`
- Any user-visible errors: `<none|describe>`

## Rollback Drill Evidence

- Rollback method exercised: `flag_only|flag_and_schema|none`
- Steps executed: `<summary>`
- Validation after rollback: `<summary>`

## Sign-off

- Product/Domain: `<name>` / `<date>`
- Engineering: `<name>` / `<date>`
- QA/Validation: `<name>` / `<date>`
