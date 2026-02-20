# Phase 1 Security Foundations Backlog

Phase window: 2 weeks

## Objective

Implement authentication, authorization, and audit controls without breaking existing readiness/report generation behavior.

## Scope Lock

In scope:
- Authn and authz foundations
- Project-scoped access enforcement
- Security tests

Out of scope:
- UI redesign
- Analytics algorithm changes
- Non-security feature expansion

## Backlog (Ordered)

| ID | Task | Deliverable | Acceptance Criteria | Depends On |
|---|---|---|---|---|
| SEC-001 | Replace dev auth fallback | JWT validation dependency and config wiring | Requests without valid token return `401`; no default dev user fallback in runtime path | None |
| SEC-002 | Enforce auth on all API route groups | Auth dependency applied to facts/readiness/checklist/disclosure/information requests/deliverables/advisory routes | Protected endpoints uniformly require auth | SEC-001 |
| SEC-003 | Add authorization service for project ownership | Shared authz utility (`can_read_project`, `can_write_project`) | Cross-project access returns `403`; owner access remains functional | SEC-002 |
| SEC-004 | Apply object-level checks in services/routes | Project, artifact, extraction, fact operations gated by ownership | IDOR test suite passes | SEC-003 |
| SEC-005 | Introduce basic roles | Role model (`admin`, `analyst`, `viewer`) with route-level policy | Role-based tests pass; least privilege enforced | SEC-002 |
| SEC-006 | Security audit events | Structured audit events for approve/reject/delete/export actions | Events emitted with actor, target, action, timestamp | SEC-002 |
| SEC-007 | Security integration tests | New tests for 401/403 scenarios and happy-path ownership | CI has passing security test module | SEC-004 |
| SEC-008 | Hardening review and rollout checklist | Security release checklist and rollback plan | Signed checklist before merge/release | SEC-007 |

## Non-Regression Safeguards (Mandatory During Phase 1)

1. Keep existing extraction/readiness/report code paths intact unless directly required for authz enforcement.
2. Use feature flag `AUTH_ENFORCEMENT_V2` for staged rollout.
3. Run core flow smoke tests on every PR.
4. Validate existing report generation against baseline projects before merge.

## Definition of Done (Phase 1)

1. All protected endpoints require auth.
2. Project/object ownership enforced with passing tests.
3. Core flow smoke tests remain green.
4. Rollback switch and procedure documented.
