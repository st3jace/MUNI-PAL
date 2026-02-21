# Phase 10 Incident Drill Template

Date: 2026-02-21
Drill ID: OPS-1005-20260221-01

## Scenario

- Incident type: `auth_spike`
- Trigger summary: `Simulated external probing: 14 requests with no token, garbage tokens, expired tokens, and cross-tenant stolen tokens against /api/v1/projects/ and /api/v1/projects/{id} endpoints`
- Expected impact: `Auth enforcement should reject all invalid tokens (401), tenant isolation should block cross-tenant access (403), no data exfiltration`

## Timeline (UTC)

| Time | Event | Owner | Notes |
|---|---|---|---|
| 14:26:20 | Detection | Stephen Peterson | Drill trigger start -- 14 malicious requests injected |
| 14:26:45 | Triage start | Stephen Peterson | 12x 401 (no token, garbage, expired), 2x cross-tenant probes. All rejected. |
| 14:27:39 | Mitigation action 1 | Stephen Peterson | Verified auth enforcement active (no-auth -> 401), known-good tokens still work (200), tenant isolation active (0 cross-tenant projects) |
| 14:28:06 | Mitigation action 2 | Stephen Peterson | Verified cross-tenant project read returns 403. Rollback toggle available but not exercised (no breach). |
| 14:28:06 | Recovery confirmed | Stephen Peterson | Core flows pass (3 projects, 1 playbook), auth still enforced (401), tenant isolation still active (0 cross-tenant). All checks green. |
| 14:28:06 | Incident close | Stephen Peterson | No breach detected. All defensive controls functioning correctly. Drill complete. |

## Detection and Signals

- Primary signal (dashboard/query/alert): `HTTP 401 response with detail "Missing bearer token" and "Invalid or expired token" -- structured log events`
- Secondary signal: `HTTP 403 response with detail "Forbidden: cross-tenant access denied" on single-project cross-tenant read`
- False positives observed: `no`

## Mitigation Actions

1. `Confirmed 12x 401 rejections for invalid/missing/expired tokens (no false negatives)`
2. `Verified cross-tenant isolation: attacker-org listing returns 0 projects, single project read returns 403`
3. `Verified rollback mechanism available (AUTH_ENFORCEMENT_V2 flag toggle + server restart) -- not exercised (no breach)`

## Recovery Validation

- Core flow checks after mitigation: `PASS -- list projects returns 200 with 3 projects, list playbooks returns 200 with 1 playbook`
- Tenant isolation checks after mitigation: `PASS -- cross-tenant listing returns 0 projects, cross-tenant single read returns 403`
- Auth checks after mitigation: `PASS -- unauthenticated request returns 401, valid token returns 200`

## Metrics

- Time to detect (TTD): `0.1 minutes (6 seconds from trigger end to detection confirmation)`
- Time to mitigate (TTM): `0.5 minutes (27 seconds from detection to mitigation confirmation)`
- Time to recovery (TTR): `0.1 minutes (6 seconds from mitigation to recovery validation)`

## Lessons Learned

- What worked: `All three defensive layers (auth enforcement, role enforcement, tenant isolation) correctly rejected malicious probes. 401/403 detail strings are clear and indexable for log monitoring. Flag-only rollback mechanism is confirmed available. JWT secret rotation would instantly invalidate all stolen tokens.`
- What failed/needs improvement: `Initial drill attempt used wrong JWT secret ("test-secret" vs actual server secret) -- need to document that drill scripts must load .env for correct JWT_SECRET_KEY. Also: no automated alerting pipeline exists yet (detection was manual API probing, not automated threshold breach notification).`
- Follow-up actions: `(1) Implement automated 401/403 spike alerting with configurable threshold windows. (2) Add drill script to CI or scripts/ for repeatable execution. (3) Document JWT secret rotation procedure in ops runbook.`

## Sign-off

- Product/Domain: `Stephen Peterson` / `2026-02-21`
- Engineering: `Stephen Peterson` / `2026-02-21`
- QA/Validation: `Stephen Peterson` / `2026-02-21`
