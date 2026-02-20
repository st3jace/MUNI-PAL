# Phase 5 Sprint 1: Risk Reporting Foundation (RISK-501 to RISK-503)

Last updated: 2026-02-18

Sprint window: 2 weeks

## Objective

Implement the minimum production-safe foundation for confidence-aware risk reporting:
- canonical risk data model,
- benchmark cohort metadata,
- reliability/confidence layer.

This sprint does not change external report formatting or advisor-facing narrative templates.

## Scope Lock

In scope:
- `RISK-501` Canonical risk data model
- `RISK-502` Benchmark cohort framework
- `RISK-503` Confidence and reliability layer
- Unit/integration tests for new model + scoring metadata

Out of scope:
- Full risk posture scoring engine (`RISK-504+`)
- Action synthesis engine (`RISK-506+`)
- External advisory risk brief contract (`RISK-508`)
- Advanced analytics bridge (`RISK-512`)

## Work Breakdown

| ID | Task | Implementation Notes | Deliverable |
|---|---|---|---|
| S5S1-01 | Define risk domain schema | Add typed structures for dimension-level risk state, benchmark stats, and confidence metadata | New schema module + docs |
| S5S1-02 | Canonical risk assembler | Build service method that maps approved facts into canonical risk dimension records | Service layer function returning deterministic structure |
| S5S1-03 | Cohort metadata contract | Add cohort descriptor fields (sector, size band, recency window, sample size) and validation | Cohort config + validator |
| S5S1-04 | Reliability scoring | Compute reliability band from sample size, source quality, and conflict rate | Reliability function + thresholds |
| S5S1-05 | Risk API/internal contract endpoint | Expose internal-only risk diagnostics payload (feature-flagged) | API endpoint and response model |
| S5S1-06 | Test suite | Add unit tests and integration tests for deterministic outputs and threshold behavior | Passing tests in CI |
| S5S1-07 | Documentation | Update V2 artifacts and service docs with model definitions and caveats | Updated docs/checklists |

## Acceptance Criteria

1. Each risk dimension payload includes:
- `dimension_id`
- `project_status`
- `gap_severity`
- `benchmark_stats` (`n_issuances`, `n_disclosures`, `mitigation_rate`, `severity_distribution`)
- `confidence` (`score`, `reliability_band`, `uncertainty_note`)

2. Cohort metadata is mandatory in all benchmark responses:
- `sector`
- `issuer_size_band`
- `deal_type`
- `recency_window`
- `sample_size`

3. Reliability layer behavior:
- sample size below threshold => `low` reliability
- high conflict rate => reliability downgrade by one band
- missing source quality inputs => explicit uncertainty note

4. Determinism:
- same input facts + same cohort config => same payload and reliability outputs

5. Safety:
- all new behavior behind feature flag (`RISK_REPORTING_V2_FOUNDATION=true`)
- default runtime path unchanged when flag is false

## Test Plan

1. Unit tests:
- risk schema serialization/deserialization
- reliability band threshold tests
- cohort validator tests

2. Integration tests:
- project with complete risk facts returns all five dimensions
- project with partial facts returns expected missing/partial statuses
- low-sample cohort returns low reliability with uncertainty note

3. Non-regression suite:
- run existing security/auth/authz/audit suite
- run core readiness/checklist/report endpoints smoke checks

## Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Overfitting thresholds to limited corpus | Misleading reliability signals | Start conservative; calibrate with historical replay in Sprint 2 |
| Schema churn across services | Contract instability | Versioned internal schema and backward-compatible fields |
| Hidden coupling with advisory generation | Runtime regressions | Feature flag + no external contract changes in Sprint 1 |

## Exit Criteria

Sprint is complete when:
1. `RISK-501`/`RISK-502`/`RISK-503` deliverables are merged.
2. New tests pass in CI.
3. No regressions in protected core flow/security suites.
4. Execution tracker updated with evidence links.

## Definition of Ready for Sprint 2

Sprint 2 can start when:
1. Reliability thresholds are validated against baseline corpus runs.
2. Internal payload is accepted by readiness/advisory service owners.
3. Feature flag rollout plan is approved.
