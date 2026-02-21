# Phase 9 Release Cutover Backlog

Phase window: 2 weeks

## Objective

Convert Phase 8 readiness into a controlled external-launch decision by closing residual governance debt, enforcing production identity posture, and validating cutover/rollback operations.

## Scope Lock

In scope:
- Baseline and security sign-off closure required for release governance
- JWT-enforced tenant identity posture for external launch context
- Production cutover rehearsal, observability, and go/no-go packet

Out of scope:
- New product features unrelated to launch readiness
- Broad schema/model changes outside identity, operations, or release controls
- Analytics contract expansion beyond current Phase 7/8 interfaces

## Backlog (Ordered)

| ID | Task | Deliverable | Acceptance Criteria | Depends On |
|---|---|---|---|---|
| REL-901 | Baseline governance closeout | Signed `BASELINE_PACK_20260218` with owners/dates/rollback owner | Phase 0 sign-off fields complete and approved | Phase 8 complete |
| REL-902 | Security rollout evidence closeout | Completed `SECURITY_HARDENING_ROLLOUT_CHECKLIST` evidence + GO decision | SEC-008 checklist all `PASS`, timestamps filled, GO/NO-GO recorded | REL-901 |
| REL-903 | Enforced auth posture in staging | `AUTH_ENFORCEMENT_V2=true`, `ROLE_ENFORCEMENT_V2=true` validated | Core + security suites pass under enforced mode; no compat-only dependency for critical paths | REL-902 |
| REL-904 | JWT tenant-claim cutover | Tenant identity sourced from JWT claims in staging launch profile | Tenant isolation validated with JWT claims (`tenant_id`/`tenant`/`org`), header-only fallback not required for launch path | REL-903 |
| REL-905 | Launch observability pack | 401/403/cross-tenant denial dashboards + alert thresholds + on-call runbook refs | Alerting and log queries documented and tested with sample events | REL-904 |
| REL-906 | Production cutover rehearsal | End-to-end dry run with rollback validation | Cutover + rollback executed in staging with timestamps and evidence | REL-905 |
| REL-907 | External launch decision packet | Signed release packet with pass/fail on all gates | Product/Engineering/QA sign-off and explicit external exposure decision captured | REL-906 |

## Definition of Done (Phase 9)

1. Phase 0 and Phase 1 governance artifacts are fully signed and no longer pending.
2. External-launch auth posture is JWT-enforced and tenant isolation is validated in that mode.
3. Cutover/rollback rehearsal evidence is complete and reproducible.
4. External launch decision is documented as explicit `GO` or `NO-GO` with approver signatures.
