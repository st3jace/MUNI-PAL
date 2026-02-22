# OPS-1003 BFMS Production-Grade Scoring Hardening Plan

Last updated: 2026-02-22

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
| M5: Production-grade readiness review | Week 4 | Go/no-go recorded with blockers/residual-risk register and sign-off package |

## M1: Calibration Dataset Requirements

Status: **In Progress (CDR-1/CDR-3/CDR-4/CDR-5 met; CDR-2 held by policy pending recency shift)**

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

**Current state**: Latest calibration snapshot reports both sectors meeting CDR-1 MEDIUM thresholds across all five dimensions (`bond_corpus_calibration_20260222_164949.json`) after Phase B evidence backfill from local waste + healthcare corpora.

**Gap**: Sustain these thresholds with recurring ingest cadence so CDR-1 does not regress between weekly snapshots.

#### CDR-2: Recency Bounds

| Requirement | Value | Rationale |
|---|---|---|
| Maximum fact age for full weight | 365 days | Facts older than 1 year should carry reduced influence |
| Stale fact warning threshold | 180 days | Alert when >50% of dimension facts are older than 6 months |
| Expiry policy | None (retain all) | Archived facts already excluded; stale facts flagged but kept |

**Implementation note**: Feature-flagged age weighting is implemented and assessed weekly; current policy remains `hold` while stale ratios remain low.

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
| CDR-1 (sample size) | Met (all-cohort rollup) | Latest calibration snapshot reports waste + healthcare each at 5/5 dimensions meeting MEDIUM threshold (`bond_corpus_calibration_20260222_164949.json`). |
| CDR-2 (recency) | Partial (policy hold) | Recency diagnostics emitted (`stale_ratio_180`, `stale_ratio_365`), feature-flagged age weighting implemented (`RISK_REPORTING_V2_AGE_WEIGHTING`, `RISK_REPORTING_V2_AGE_WEIGHTING_FULL_WEIGHT_DAYS`, `RISK_REPORTING_V2_AGE_WEIGHTING_MAX_PENALTY`), and staged-tuning assessor automation added (`scripts/assess_age_weighting_policy.py` -> `age_weighting_policy_<timestamp>.md/.json`). Current recommendation: `hold` due low staleness baseline (latest stale ratios 0.0/0.0). |
| CDR-3 (cohort coverage) | Met (all-cohort rollup) | Latest calibration snapshot reports waste + healthcare at 5/5 pair-complete dimensions (`bond_corpus_calibration_20260222_164949.json`). |
| CDR-4 (source quality) | Met (all-cohort rollup) | Latest calibration snapshot reports waste + healthcare each at 5/5 dimensions meeting source-diversity target (`bond_corpus_calibration_20260222_164949.json`). |
| CDR-5 (drift detection) | Met (proxy-series mode) | Drift snapshots + routed escalation artifacts evaluate all four thresholds in automation with critical gate enforcement (`scripts/assess_bond_corpus_drift.py`, `scripts/route_bond_corpus_drift_alerts.py`, `--fail-on-critical`); latest routing highest severity `none`, critical count `0`. |

### M2 Progress Update (2026-02-21)

Implemented (non-breaking, additive):

1. Cohort-aware mitigation baseline adjustments by `sector + deal_type` in `src/munipal/services/risk_reporting_service.py`.
2. Sector-conditional semantics for `risk.feedstock` context (e.g., healthcare -> demand/reimbursement continuity) while preserving contract dimension IDs.
3. Evidence diagnostics in dimension metrics:
   - `source_artifact_count`
   - `source_type_count`
   - `stale_ratio_180`
   - `stale_ratio_365`
4. Confidence uncertainty notes now include source-diversity and recency warnings when thresholds are missed.
5. Calibration evidence automation from extractor corpora:
   - `scripts/assess_bond_corpus_calibration.py`
   - outputs `reports/phase10_postlaunch/bond_corpus_calibration_<timestamp>.md/.json`
6. Waste feedstock mitigant backfill utility added/applied from implementation-guide evidence:
   - `scripts/backfill_waste_feedstock_mitigants.py`
   - CDR-3 all-cohort waste coverage moved from 4/5 to 5/5 pair-complete.
7. Added quantitative robustness checks (WS-2) for DSCR:
   - `guardrail.dscr.scenario_sensitivity`
   - `guardrail.dscr.ratio_consistency`
   - validated via unit + integration regression updates.

### M3 Progress Update (2026-02-21)

Implemented (non-breaking, additive):

1. Scoring profile governance metadata scaffolded in risk service:
   - `scoring_profile_version`
   - `scoring_profile_checksum`
   - `governance_policy_version`
2. Added override governance scope mapping for audit traceability:
   - `dimension`
   - `guardrail`
   - `scoring_profile`
   - `other`
3. Enriched risk route audit events (diagnostics/internal/external/BFMS/sync/override/accept)
   with scoring profile governance metadata.
4. Added governance regression tests:
   - `tests/unit/test_risk_reporting_service.py`
   - `tests/unit/test_audit_route_events.py`

### M4 Progress Update (2026-02-21)

Implemented (non-breaking, additive):

1. Consumer interpretation guide contract fields added for external/BFMS outputs:
   - `interpretation_guide_version`
   - `consumer_interpretation_guide`
2. Scoring profile metadata exposed on external/BFMS contracts:
   - `scoring_profile_version`
   - `scoring_profile_checksum`
   - `governance_policy_version`
3. Key assumption source traceability standardized with inline references:
   - format: `[ref: <schema_path_or_evidence_path>]`
4. External narrative compliance checks made dynamic:
   - `assumption_traceability_tags_present`
   - `consumer_interpretation_guide_present`
5. OpenAPI contract snapshot updated for additive schema fields:
   - `contracts/openapi.v1.json`

### M5 Progress Update (2026-02-22)

Implemented (non-breaking, additive):

1. Operational CDR-5 routing pipeline added:
   - `scripts/route_bond_corpus_drift_alerts.py`
   - severity-based routed events (`info`/`warning`/`critical`)
   - incident and advisory-hold recommendations when critical events exist
2. Phase 10 automation/CI now executes drift routing with critical fail gate:
   - `scripts/run_phase10_postlaunch_bundle.py`
   - `.github/workflows/phase10-postlaunch-dispatch.yml`
3. Drift snapshot schema expanded for routing-relevant metrics:
   - sample reliability band transitions (sample-size proxy)
   - exposure/mitigant/source-document drop percentages
   - posture/conflict proxy time-series deltas with bootstrap-safe history handling
4. Regression coverage added for alert routing:
   - `tests/unit/test_bond_corpus_alert_routing.py`
   - `tests/unit/test_bond_corpus_drift.py`
5. Added feature-flagged recency age-weighting in confidence scoring:
   - `src/munipal/services/risk_reporting_service.py`
   - `src/munipal/config.py`
   - `.env.example`
   - regression coverage in `tests/unit/test_risk_reporting_service.py`
6. Added CDR-2 staged-tuning assessment automation and gate coverage:
   - `scripts/assess_age_weighting_policy.py`
   - `tests/unit/test_age_weighting_policy_assessment.py`
   - integrated into `scripts/run_phase10_postlaunch_bundle.py` and CI artifact retention
7. Added advisory cohort inference validation automation for package-generation profile behavior:
   - `scripts/assess_advisory_cohort_inference.py`
   - `tests/unit/test_advisory_cohort_inference_assessment.py`
   - validates healthcare + waste sector inference across revenue/conduit/private-activity cohorts
   - integrated into `scripts/run_phase10_postlaunch_bundle.py` and CI artifact retention
8. Added API-level advisory package smoke assessment for staging evidence:
   - `scripts/assess_advisory_package_smoke.py`
   - `tests/unit/test_advisory_package_smoke_assessment.py`
   - validates internal/external generation, fetch, validate, and export endpoints in one artifact
   - integrated into `scripts/run_phase10_postlaunch_bundle.py` and CI artifact retention
9. Added OPS-1003 M5 readiness synthesis automation:
   - `scripts/assess_ops1003_m5_readiness.py`
   - `tests/unit/test_ops1003_m5_readiness_assessment.py`
   - consumes latest calibration/cohort/smoke/age-weighting/drift/routing artifacts and records one go/no-go output with blockers + residual risks
   - latest run: `ops1003_m5_readiness_20260222_165001.json` recommendation `go`, blockers `0`, residual risks `0`
10. Added and executed Phase B CDR closure backfill:
   - `scripts/backfill_phaseb_cdr_coverage.py`
   - dry-run + apply evidence: `44` waste rows and `27` healthcare rows inserted from local source corpora
   - post-backfill calibration confirms CDR-1/CDR-4 closure in both sectors (`bond_corpus_calibration_20260222_164949.json`)
11. Added strict regression-gate enforcement for post-M5 operation:
   - `scripts/enforce_ops1003_regression_gates.py`
   - fails on CDR-1 regression, CDR-4 regression, residual-risk count threshold breach, or non-`go` M5 recommendation
   - wired into `scripts/run_phase10_postlaunch_bundle.py` and covered by `tests/unit/test_ops1003_regression_gates.py`

### Remediation Path

1. **Short-term** (Week 3/4): Run weekly CDR-2 assessor and archive `age_weighting_policy_<timestamp>.md/.json` in CI/staging evidence bundle.
2. **Medium-term** (Week 4): Stage-enable age weighting only when assessor status moves to `staged_enable`; otherwise hold default-off and re-evaluate after new ingest.
3. **Long-term** (Week 4+): Sustain CDR-1/CDR-4 coverage with periodic backfill or ingestion automation and optionally upgrade CDR-5 proxies to model-derived posture/conflict telemetry once stable historical series is available.

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
