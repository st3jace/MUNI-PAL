# Phase 8 External Readiness Backlog

Phase window: 2 weeks

## Objective

Establish tenant-safe operating boundaries and production readiness controls before any external exposure.

## Scope Lock

In scope:
- Tenant isolation foundation and enforcement controls
- Ops runbooks and rollback procedures for external readiness
- Staging sign-off evidence and release gates

Out of scope:
- New analytics features
- UI redesign unrelated to tenant/ops readiness
- Broad data model refactors outside tenant readiness scope

## Backlog (Ordered)

| ID | Task | Deliverable | Acceptance Criteria | Depends On |
|---|---|---|---|---|
| EXT-801 | Tenant identity plumbing | Tenant context dependency (`CurrentTenantId`) with JWT/header resolution and config flag | Tenant context resolves deterministically across auth + compat modes; unit tests pass | Phase 7 complete |
| EXT-802 | Project tenant partitioning | `projects.tenant_id` model + migration + service wiring | New projects stamped with tenant ID; legacy rows backfilled; migration reversible | EXT-801 |
| EXT-803 | Tenant-aware authorization checks | Cross-tenant guardrails in project read/write paths | Cross-tenant access denied when tenant isolation enabled; integration tests pass | EXT-802 |
| EXT-804 | Tenant-aware listing controls | Tenant filter enforced for project listing under tenant isolation mode | Superuser/project listings remain scoped by tenant; integration tests pass | EXT-803 |
| EXT-805 | CI gate expansion | Add tenant-isolation integration tests to core gate | CI gate includes tenant coverage and remains green | EXT-804 |
| EXT-806 | External readiness runbooks | Tenant ops runbook + rollback/incident procedures | Runbook approved and linked from tracker | EXT-805 |
| EXT-807 | Staging external readiness validation | Signed staging evidence pack for tenant isolation + ops controls | Staging checklist complete with links/screenshots/logs and sign-off | EXT-806 |

## Definition of Done (Phase 8)

1. Tenant isolation controls are implemented and verified in CI.
2. External readiness runbooks are documented and reviewed.
3. Staging validation evidence is complete and signed off.
4. Release gate for external exposure is explicitly documented as pass/fail.
