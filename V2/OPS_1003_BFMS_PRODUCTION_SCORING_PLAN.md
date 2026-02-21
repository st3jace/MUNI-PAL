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

## M1: Calibration Dataset Requirements

Status: **In Progress**

### Current Confidence Model

The reliability engine (`_compute_confidence`) uses three weighted inputs:

```
base_score = (sample_score * 0.45) + (source_quality * 0.40) + ((1 - conflict_rate) * 0.15)
```

Band thresholds: HIGH >= 0.80, MEDIUM >= 0.55, LOW < 0.55.
Hard overrides: sample_size < 20 forces LOW; conflict_rate >= 0.35 downgrades one band.

### Calibration Dataset Requirements

#### CDR-1: Minimum Sample Size per Dimension

| Requirement | Value | Rationale |
|---|---|---|
| Minimum for LOW band | 1+ approved facts | Current: any non-zero evidence yields LOW |
| Minimum for MEDIUM band | 20 approved facts | Current: `_sample_score(20)` returns 0.60 |
| Minimum for HIGH band | 50+ approved facts | Current: `_sample_score(50)` returns 0.80 |
| Target for production | 100+ per dimension | `_sample_score(100)` returns 1.0 (full weight) |
| Acceptance: full-mode | All 5 dimensions >= MEDIUM | Any LOW forces fallback mode |

**Current state**: Live UCS baseline has ~239 total facts across all schema paths. Most risk dimensions have < 20 approved facts per dimension, which forces LOW reliability and fallback mode unless synthetic seed facts are used.

**Gap**: Need to define a fact generation or ingestion strategy to sustainably reach 20+ approved facts per risk dimension from real evidence (not synthetic seeds).

#### CDR-2: Recency Bounds

| Requirement | Value | Rationale |
|---|---|---|
| Maximum fact age for full weight | 365 days | Facts older than 1 year should carry reduced influence |
| Stale fact warning threshold | 180 days | Alert when >50% of dimension facts are older than 6 months |
| Expiry policy | None (retain all) | Archived facts already excluded; stale facts flagged but kept |

**Implementation note**: The current engine does not discount by fact age. This is an additive enhancement for M2/M3.

#### CDR-3: Cohort Coverage

| Requirement | Value | Rationale |
|---|---|---|
| Minimum dimensions with evidence | 5/5 | All dimensions must have at least 1 approved fact |
| Minimum dimensions at MEDIUM+ | 5/5 for full mode | Fallback triggers on any LOW dimension |
| Cross-dimension conflict ceiling | 35% per dimension | Matches existing downgrade threshold |
| Exposure + mitigant pair completeness | Both required for LOW gap severity | PARTIAL gap = only exposure or only mitigant present |

#### CDR-4: Source Quality Requirements

| Requirement | Value | Rationale |
|---|---|---|
| Minimum evidence_count for quality score | 2 facts | `_source_quality_score` saturates at `evidence_count / 2.0` |
| Source diversity target | >= 2 distinct source artifacts | Single-source evidence is fragile |
| Confidence score floor for approved facts | 0.50 | Facts below 0.50 confidence should require explicit review |

#### CDR-5: Drift Detection Diagnostics

| Metric | Threshold | Action |
|---|---|---|
| Reliability band change (any dimension) | Any transition | Log governance event + alert |
| Overall posture score delta week-over-week | > 0.10 | Flag for review |
| New conflict rate spike | > 0.20 increase in any dimension | Alert + hold advisory generation |
| Evidence count drop | > 30% in any dimension | Alert + investigate archival/deletion |

### Calibration Acceptance Criteria

M1 is complete when:

1. CDR-1 through CDR-5 are documented and approved (this section).
2. Current live baseline is assessed against each CDR.
3. Gap remediation path is identified for any CDR not met.
4. Drift detection diagnostic checks are specified for WS-1 implementation in M2.

### Current Baseline Assessment

| CDR | Met? | Evidence |
|---|---|---|
| CDR-1 (sample size) | Partial | 239 total facts, but most risk dimensions < 20 without synthetic seeds |
| CDR-2 (recency) | N/A | No age-based weighting implemented yet |
| CDR-3 (cohort coverage) | Partial | Depends on seed facts; organic coverage gaps in feedstock/construction |
| CDR-4 (source quality) | Partial | Most facts sourced from single playbook evaluation |
| CDR-5 (drift detection) | Not started | No week-over-week tracking implemented |

### Remediation Path

1. **Short-term** (Week 2): Add drift detection logging for reliability band transitions and posture score delta. No code changes to scoring logic.
2. **Medium-term** (Week 3): Implement source diversity check in `_compute_confidence()` as additive diagnostic field (non-breaking).
3. **Long-term** (Week 4+): Add fact age weighting as opt-in enhancement behind feature flag. Evaluate recency bounds against healthcare sector expansion data.

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
