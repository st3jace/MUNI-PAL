# Security Hardening Rollout Checklist (SEC-008)

Last updated: 2026-02-18

## Purpose

Provide a mandatory go/no-go checklist and rollback runbook for Phase 1 security rollout.

## Scope

Controls covered by this checklist:
- `AUTH_ENFORCEMENT_V2`
- `ROLE_ENFORCEMENT_V2`
- Project/object authorization checks
- Security audit event emission

## Release Metadata

- Release ID: MP-P1-SEC-2026-02-18-01
- Environment: Internal Staging (Pre-Production)
- Release owner: Stephen Peterson
- Technical approver: Stephen Peterson
- Product approver: Stephen Peterson
- Planned start (UTC): 2026-02-19T15:00:00Z (Tentative)
- Planned end (UTC): 2026-02-19T17:00:00Z (Tentative)

## Go/No-Go Checklist

Mark each item `PASS` before rollout.

1. Code and tests
- [ ] `PASS` security-focused suite is green (`42 passed` baseline or better).
- [ ] `PASS` lint checks pass for changed files (`ruff check --select I,F ...`).
- [ ] `PASS` no unresolved critical vulnerabilities in dependency/security scan.

2. Core flow non-regression
- [ ] `PASS` project create/get flow validated.
- [ ] `PASS` artifact upload/process validated.
- [ ] `PASS` extraction + fact review flow validated.
- [ ] `PASS` readiness/checklist/report generation validated.
- [ ] `PASS` baseline comparison for UCS WTE Facility reviewed and accepted.

3. Environment and config
- [ ] `PASS` `JWT_SECRET_KEY` set from secure secret store (not default/dev value).
- [ ] `PASS` `JWT_ALGORITHM` validated with issued tokens.
- [ ] `PASS` `AUTH_ENFORCEMENT_V2` rollout sequence approved.
- [ ] `PASS` `ROLE_ENFORCEMENT_V2` rollout sequence approved.
- [ ] `PASS` CORS and debug settings reviewed for target environment.

4. Observability and operations
- [ ] `PASS` authentication failures (401) monitored.
- [ ] `PASS` authorization failures (403) monitored.
- [ ] `PASS` `security_audit_event` log stream visible and queryable.
- [ ] `PASS` on-call owner assigned during rollout window.

5. Sign-off
- [ ] `PASS` release owner sign-off.
- [ ] `PASS` technical approver sign-off.
- [ ] `PASS` product approver sign-off.

### Sign-off Record

- Release owner name: Stephen Peterson
- Release owner sign-off timestamp (UTC):
- Technical approver name: Stephen Peterson
- Technical approver sign-off timestamp (UTC):
- Product approver name: Stephen Peterson
- Product approver sign-off timestamp (UTC):

Go/No-Go Decision:
- [ ] `GO`
- [ ] `NO-GO`

Decision timestamp (UTC):

## Rollout Plan (Phased)

1. Pre-rollout
- Run and archive:
  - `pytest -q tests/integration/test_auth_enforcement_routes.py tests/integration/test_project_authorization.py tests/integration/test_object_authorization.py tests/integration/test_role_policy.py tests/integration/test_security_integration.py tests/unit/test_auth_dependencies.py tests/unit/test_audit_service.py tests/unit/test_audit_route_events.py -p no:cacheprovider`
- Capture baseline API health/readiness snapshots.

2. Step A: Auth enforcement
- Set `AUTH_ENFORCEMENT_V2=true`.
- Keep `ROLE_ENFORCEMENT_V2=false` for first pass.
- Monitor 401 rate and critical path success for 30-60 minutes.

3. Step B: Role enforcement
- Set `ROLE_ENFORCEMENT_V2=true`.
- Validate admin/analyst/viewer behavior on key endpoints.
- Monitor 403 rate and user-impact reports for 30-60 minutes.

4. Step C: Audit verification
- Execute approve/reject/delete/export sample operations.
- Confirm `security_audit_event` records for actor/action/target/project.

5. Finalize
- Mark rollout complete in `V2/EXECUTION_TRACKER.md`.
- Store evidence links (logs, test run IDs, screenshots if needed).

## Rollback Runbook

Trigger rollback immediately if:
- sustained authentication failures block intended users;
- authorization policy blocks legitimate operational workflows;
- core flow regression detected in production-like environment.

1. Immediate rollback switches
- Set `ROLE_ENFORCEMENT_V2=false`.
- If impact remains, set `AUTH_ENFORCEMENT_V2=false`.

2. Service recovery checks (within 10 minutes)
- Validate:
  - `GET /health`
  - project list/get
  - artifact list/get
  - readiness endpoint

3. Incident capture
- Record exact rollback timestamp (UTC).
- Record config values before and after rollback.
- Capture representative failing request IDs and impacted user roles.

4. Stabilization
- Reproduce in lower environment.
- Patch and retest against SEC-007 suite.
- Re-run checklist before next rollout attempt.

## Evidence Log

- Test run link / command output reference:
  - Security suite command:
    - `pytest -q tests/integration/test_auth_enforcement_routes.py tests/integration/test_project_authorization.py tests/integration/test_object_authorization.py tests/integration/test_role_policy.py tests/integration/test_security_integration.py tests/unit/test_auth_dependencies.py tests/unit/test_audit_service.py tests/unit/test_audit_route_events.py -p no:cacheprovider`
  - Result summary:
  - Timestamp (UTC):
- Lint command / output reference:
  - `ruff check --select I,F src/munipal/api src/munipal/services tests`
  - Result summary:
  - Timestamp (UTC):
- Log dashboard link:
  - 401 monitor:
  - 403 monitor:
  - `security_audit_event` stream:
- Rollout notes:
  - Step A result:
  - Step B result:
  - Step C result:
- Rollback notes (if applicable):
  - Trigger:
  - Actions taken:
  - Recovery confirmation timestamp (UTC):
