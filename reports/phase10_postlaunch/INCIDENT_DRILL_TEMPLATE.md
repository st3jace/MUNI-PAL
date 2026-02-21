# Phase 10 Incident Drill Template

Date: YYYY-MM-DD
Drill ID: OPS-1005-YYYYMMDD-01

## Scenario

- Incident type: `auth_spike|tenant_isolation_breach|core_flow_regression|other`
- Trigger summary: `<summary>`
- Expected impact: `<summary>`

## Timeline (UTC)

| Time | Event | Owner | Notes |
|---|---|---|---|
|  | Detection |  |  |
|  | Triage start |  |  |
|  | Mitigation action 1 |  |  |
|  | Mitigation action 2 |  |  |
|  | Recovery confirmed |  |  |
|  | Incident close |  |  |

## Detection and Signals

- Primary signal (dashboard/query/alert): `<link or reference>`
- Secondary signal: `<link or reference>`
- False positives observed: `yes|no`

## Mitigation Actions

1. `<action>`
2. `<action>`
3. `<action>`

## Recovery Validation

- Core flow checks after mitigation: `<summary>`
- Tenant isolation checks after mitigation: `<summary>`
- Auth checks after mitigation: `<summary>`

## Metrics

- Time to detect (TTD): `<minutes>`
- Time to mitigate (TTM): `<minutes>`
- Time to recovery (TTR): `<minutes>`

## Lessons Learned

- What worked: `<summary>`
- What failed/needs improvement: `<summary>`
- Follow-up actions: `<summary>`

## Sign-off

- Product/Domain: `<name>` / `<date>`
- Engineering: `<name>` / `<date>`
- QA/Validation: `<name>` / `<date>`
