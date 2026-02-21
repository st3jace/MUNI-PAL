# Phase 9 Release Cutover Runbook

Last updated: 2026-02-21

## Goal

Execute Phase 9 release-governance closure and launch-readiness validation for external exposure decisioning.

## Scope

This runbook covers:

- `REL-901` baseline governance sign-off
- `REL-902` security rollout governance sign-off
- `REL-903` enforced auth posture validation
- `REL-904` JWT tenant-claim validation
- `REL-905` observability readiness checks
- `REL-906` cutover + rollback rehearsal
- `REL-907` final launch decision packet

## One-Command Local Execution

From repo root:

```powershell
python scripts/run_phase9_release_readiness_bundle.py
```

## Target CI Dispatch (Recommended)

Workflow: `.github/workflows/phase9-release-readiness-dispatch.yml`

1. Open repository Actions tab.
2. Select **Phase 9 Release Readiness Bundle**.
3. Click **Run workflow**.
4. Select branch/commit and optional note.
5. Wait for completion and download artifact `phase9-release-readiness-<run_id>`.

## Outputs

Each run writes timestamped artifacts to:

- `reports/phase9_release/phase9_release_<timestamp>.md`
- `reports/phase9_release/phase9_release_<timestamp>.json`
- `reports/phase9_release/logs_<timestamp>/`
- `reports/phase9_release/STAGING_EVIDENCE_TEMPLATE.md` (manual sign-off template)

## Manual Staging Checklist

1. Fill and sign `V2/BASELINE_PACK_20260218.md` (`REL-901`).
2. Fill and sign `V2/SECURITY_HARDENING_ROLLOUT_CHECKLIST.md` (`REL-902`).
3. Enable launch profile flags:
   - `AUTH_ENFORCEMENT_V2=true`
   - `ROLE_ENFORCEMENT_V2=true`
   - `TENANT_ISOLATION_V2=true`
4. Validate JWT-only auth flows (no header-only dependency for launch path).
5. Validate tenant isolation with JWT tenant claims (`tenant_id`/`tenant`/`org`).
6. Validate observability dashboards/alerts for 401, 403, and cross-tenant denials.
7. Run cutover + rollback rehearsal with timestamps and recovery checks.
8. Complete `reports/phase9_release/STAGING_EVIDENCE_TEMPLATE.md`.
9. Record CI run links and evidence in `V2/EXECUTION_TRACKER.md`.

## Rollback Guidance

If launch-profile validation fails:

1. Set `ROLE_ENFORCEMENT_V2=false` and validate impact.
2. If required, set `AUTH_ENFORCEMENT_V2=false`.
3. If tenant breakage persists, set `TENANT_ISOLATION_V2=false`.
4. Restart API and confirm core flow health.
5. Capture incident timeline and retain failing request samples.

## Exit Criteria

Phase 9 is complete only when:

1. `REL-901` through `REL-907` all show pass/approved state.
2. Product/Engineering/QA sign-off are recorded in Phase 9 evidence template.
3. External launch decision (`GO` or `NO-GO`) is explicitly documented.
