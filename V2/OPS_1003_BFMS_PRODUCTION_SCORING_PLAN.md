# OPS-1003 BFMS Production-Grade Scoring Hardening Plan

Last updated: 2026-02-21

## Objective

Advance BFMS integration from stable foundation scoring to production-grade, calibrated, and governable risk scoring without breaking current contracts.

## Current Baseline

- Contract: `risk-bfms-integration-v1`
- Current mode: deterministic rule-based posture with reliability gating and fallback behavior
- Validation baseline: core gate green with Phase 9/10 security + tenant isolation coverage

## Scope

In scope:

- Reliability calibration and confidence governance
- Quantitative metric robustness checks
- Versioned scoring profile management
- Explainability and auditability improvements

Out of scope:

- Breaking API response shape changes without version bump
- Replacing existing fallback semantics
- Frontend redesign unrelated to score quality

## Workstreams

### WS-1 Calibration and Reliability

1. Define calibration dataset requirements (minimum sample size, recency bounds, cohort coverage).
2. Add calibration diagnostics for dimension reliability drift.
3. Publish reliability acceptance thresholds (`high`/`medium`/`low`) with tuning rationale.

Deliverable:

- Calibration report format + weekly drift monitor references.

### WS-2 Quantitative Scoring Robustness

1. Add scenario sensitivity checks (base/stress boundary handling).
2. Add guardrail consistency checks across related ratios.
3. Add deterministic tie-break and normalization rules for any new score aggregations.

Deliverable:

- Scoring robustness checklist and regression test expansion.

### WS-3 Versioning and Governance

1. Introduce internal scoring profile version metadata (non-breaking additive field).
2. Add explicit governance event for scoring profile changes.
3. Maintain backward-compatible `risk-bfms-integration-v1` payload until formal v2 decision.

Deliverable:

- Versioning/governance runbook addendum and audit event map.

### WS-4 Explainability and Consumer Readiness

1. Improve `key_assumptions` quality and source traceability consistency.
2. Define consumer interpretation guide for posture and fallback reasons.
3. Add validation checks for externally safe narrative output.

Deliverable:

- Consumer interpretation reference + regression tests.

## Milestones

| Milestone | Target | Exit Criteria |
|---|---|---|
| M1: Calibration baseline defined | Week 2 | Dataset requirements documented and approved |
| M2: Robustness checks implemented | Week 3 | New robustness tests green in CI |
| M3: Governance/versioning controls added | Week 3 | Audit + metadata controls verified |
| M4: Explainability hardening complete | Week 4 | External narrative validation pass |
| M5: Production-grade readiness review | Week 4 | Go/no-go recorded with residual risks |

## Validation Plan

- Expand unit coverage in `tests/unit/test_risk_reporting_service.py`
- Expand integration coverage in `tests/integration/test_risk_reporting_foundation.py`
- Add targeted regression slice for scoring profile and calibration checks
- Keep compatibility guarantees validated via contract test + snapshot

## Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Overfitting calibration to sparse cohorts | Medium | Enforce minimum sample and recency policy |
| Contract drift from incremental fields | High | Additive-only changes + snapshot gate |
| Lower explainability under new scoring complexity | Medium | Mandatory assumptions/traceability checks |

## Sign-off

- Product/Domain: Pending
- Engineering: Pending
- QA/Validation: Pending
