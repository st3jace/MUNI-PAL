# Phase 10 Weekly Post-Launch Evidence Template

Week: 2026-W08
Date range: 2026-02-21 to 2026-02-21

## Automated Bundle Evidence

- Workflow/script: `.github/workflows/phase10-postlaunch-dispatch.yml`
- Run URL (if CI): `https://github.com/st3jace/MUNI-PAL/actions/runs/22258099077`
- Commit SHA: `a9c0ca9f`
- Overall result: `pass`

| Gate | Status | Duration |
|---|---|---:|
| Backend CI-Equivalent Gate | `pass` | ~17s |
| Frontend Tests (vitest) | `pass` | ~2s |
| Frontend Production Build | `pass` | ~8s |
| Auth+Tenant+Risk Stability Slice | `pass` | ~6s |

### CI Fix Notes

Contract test (`test_openapi_contract_snapshot_is_current`) failed on initial dispatch (`22257991564`) due to Pydantic binary format schema drift (`format: binary` vs `contentMediaType: application/octet-stream`). Fixed by adding `_canonicalize_binary_format()` recursive normalizer to `tests/contract/test_openapi_contract.py`. All 5 CI workflows also updated from Python 3.12 to 3.14 to match local environment.

- Core Security Risk Gate run: `https://github.com/st3jace/MUNI-PAL/actions/runs/22258095603` (pass)
- Local test suite: 199 passed (0 failed)

## OPS-1001 Telemetry Baseline

- 401 trend summary: `Baseline established. Missing/invalid JWT tokens correctly return 401 with WWW-Authenticate: Bearer header. Verified via test_auth_enforcement_routes.py + live API smoke (7 checks).`
- 403 trend summary: `Baseline established. Cross-tenant access returns 403 "Forbidden: cross-tenant access denied". Same-tenant non-owner non-superuser access returns 403 "insufficient access to project". Both confirmed via OPS-1002 rehearsal.`
- Cross-tenant-denied trend summary: `Baseline established. JWT tenant_id claim drives tenant scoping. X-Tenant-Id header ignored under enforced auth. Cross-tenant GET returns 403. Validated via 15/15 JWT tenant test suite.`
- Alert thresholds tuned this week: `no`
- Notes: `Week 1 baseline only. Structured log events emitted for 401/403/audit actions. No production traffic yet (staging validation only).`

## OPS-1002 Tenant Onboarding Rehearsal

- Rehearsal executed this week: `yes`
- Tenant ID tested: `acme-corp`
- Provisioning + access checks result: `7/9 passed. Provisioned 3 acme-corp users (admin, analyst, viewer). Created project under acme-corp tenant. Verified: (1) acme-corp admin can create project (201), (2) acme-corp admin can list own projects (1 result), (3) default tenant cannot see acme-corp projects (0 results), (4) cross-tenant GET returns 403, (5) acme-corp admin can read own project (200), (6) acme-corp listing returns only own tenant projects, (7) default listing returns only default projects. Steps 7-8 (analyst/viewer read) returned 403 -- expected behavior per authorization model (requires owner_id match or superuser).`
- Rollback notes (if used): `Rollback executed successfully. Deleted acme-corp project via API (204). Verified: acme-corp listing shows 0 projects, default listing shows 3 projects (unchanged). Clean rollback confirmed.`

### Authorization Model Finding

Same-tenant non-owner access requires superuser privilege. Analyst and viewer users within `acme-corp` cannot read projects they don't own, even within the same tenant. This is correct per current `can_read_project()` logic (`owner_id == user_id` OR `is_superuser`). Future enhancement: consider adding team/org-level read permissions for same-tenant members.

## OPS-1003 BFMS Hardening Progress

- Reliability/calibration work completed: `Not started (Week 1 focus was CI stabilization and tenant rehearsal)`
- Validation updates: `None this week`
- Risks/blockers: `None identified`

## OPS-1004 Healthcare Readiness Progress

- Corpus intake checks run: `no`
- Data quality/compliance findings: `Not started (Week 1 focus was CI stabilization and tenant rehearsal)`
- Go/no-go status: `pending`

## OPS-1005 Incident Drill Progress

- Drill executed this week: `no`
- Detection time: `N/A`
- Recovery time: `N/A`
- Lessons learned: `Scheduled for future week. Week 1 focused on CI stabilization and OPS-1002 rehearsal.`

## Sign-off

- Product/Domain: `Stephen Peterson` / `2026-02-21`
- Engineering: `Stephen Peterson` / `2026-02-21`
- QA/Validation: `Stephen Peterson` / `2026-02-21`
