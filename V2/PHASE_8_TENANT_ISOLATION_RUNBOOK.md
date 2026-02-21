# Phase 8 Tenant Isolation Runbook

Last updated: 2026-02-20

## Goal

Roll out tenant isolation safely using migration `b8c9d0e1f2a3`, feature flag `TENANT_ISOLATION_V2`, and explicit staging evidence before external exposure.

## Scope

This runbook covers:

- `EXT-806`: tenant operations, incident handling, rollback
- `EXT-807`: staging validation evidence collection and sign-off

## Preconditions

1. Phase 7 closeout is complete and signed off.
2. Core CI gate is currently green.
3. Target environment has a recent DB backup/snapshot.
4. Auth mode and tenant resolution mode are decided:
- Compatibility mode: tenant from `X-Tenant-Id` header
- Enforcement mode: tenant from JWT claims (`tenant_id`, `tenant`, `org`)

## Rollout Steps

### 1. Preflight Validation

Run from repo root:

```powershell
pytest -q tests/integration/test_tenant_isolation.py tests/unit/test_auth_dependencies.py
```

Expected:

- All tests pass
- No unreviewed migration drift in `alembic/versions/`

### 2. Apply Migration in Target DB

Run:

```powershell
alembic upgrade b8c9d0e1f2a3
```

Migration outcome:

- Adds `projects.tenant_id`
- Backfills existing projects from `users.organization` when available, else `default`
- Creates index `ix_projects_tenant_id`

### 3. Validate Backfill Output

Run SQL checks in target DB:

```sql
SELECT COUNT(*) AS missing_tenant_rows
FROM projects
WHERE tenant_id IS NULL OR tenant_id = '';
```

```sql
SELECT tenant_id, COUNT(*) AS project_count
FROM projects
GROUP BY tenant_id
ORDER BY project_count DESC, tenant_id ASC;
```

Expected:

- `missing_tenant_rows = 0`
- Distribution aligns with expected organizations/tenants

### 4. Enable Tenant Isolation in Staging

Set environment variable:

```env
TENANT_ISOLATION_V2=true
```

Restart API service after env update.

### 5. Staging Smoke Validation

1. Create or identify at least two projects with different `tenant_id` values.
2. Validate same-tenant access succeeds.
3. Validate cross-tenant access is denied (`403`).
4. Validate project listing is tenant-scoped even for elevated roles when isolation is enabled.

Recommended API checks:

- `GET /api/v1/projects`
- `GET /api/v1/projects/{project_id}`
- `PATCH /api/v1/projects/{project_id}`
- `DELETE /api/v1/projects/{project_id}`

### 6. Capture Automated Evidence Bundle

Local:

```powershell
python scripts/run_phase8_closeout_bundle.py
```

Target CI:

- Dispatch `.github/workflows/phase8-closeout-dispatch.yml`
- Download uploaded artifact `phase8-closeout-<run_id>`

### 7. Record Staging Evidence and Sign-off

Populate:

- `reports/phase8_closeout/STAGING_EVIDENCE_TEMPLATE.md`
- `V2/EXECUTION_TRACKER.md` (run IDs, links, date, owner)

## Rollback Procedure

### Immediate rollback (safe first action)

1. Set `TENANT_ISOLATION_V2=false`
2. Restart API service
3. Confirm normal project access behavior is restored

### Schema rollback (only if required)

Prerequisite: confirm application no longer depends on `projects.tenant_id`.

```powershell
alembic downgrade a7b8c9d0e1f2
```

Then re-run smoke checks and document incident timeline.

## Incident Response

| Symptom | Likely Cause | Action |
|---|---|---|
| Unexpected 403 on valid tenant access | Tenant resolution mismatch (JWT/header) | Verify auth mode and tenant claim/header source |
| Empty project lists for active users | Missing tenant mapping or wrong default | Validate `projects.tenant_id` values and request tenant context |
| Elevated users still see cross-tenant data | Flag disabled or route not tenant-wired | Verify `TENANT_ISOLATION_V2=true`, then check endpoint wiring |
| Migration fails | DB permissions or schema drift | Restore backup, inspect migration logs, rerun in controlled window |

## Approval Checklist

- [ ] Product owner approves tenant behavior in staging
- [ ] Engineering approves migration + rollback evidence
- [ ] QA approves tenant isolation smoke checks
- [ ] Tracker updated with run IDs, artifact links, and sign-off date
