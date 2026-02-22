# Phase 10 Weekly Post-Launch Evidence Template

Week: 2026-W08
Date range: 2026-02-21 to 2026-02-22

## Automated Bundle Evidence

- Workflow/script: `.github/workflows/phase10-postlaunch-dispatch.yml`
- Run URL (if CI): `https://github.com/st3jace/MUNI-PAL/actions/runs/22280881561`
- Commit SHA: `7fa502c6`
- Overall result: `pass`
- Local bundle verification run: `reports/phase10_postlaunch/phase10_postlaunch_20260222_164741.json`
- Local archived bundle verification: `reports/phase10_postlaunch/phase10_postlaunch_20260222_164741_archive.zip`

| Gate | Status | Duration |
|---|---|---:|
| Backend CI-Equivalent Gate | `pass` | 45.61s |
| Frontend Tests (vitest) | `pass` | 43.51s |
| Frontend Production Build | `pass` | 17.49s |
| Auth+Tenant+Risk Stability Slice | `pass` | 20.50s |
| Healthcare Corpus Readiness Snapshot | `pass` | 0.33s |
| Bond Corpus Calibration Snapshot | `pass` | 0.24s |
| Advisory Cohort Inference Assessment | `pass` | 5.22s |
| Advisory Package Smoke Assessment | `pass` | 5.84s |
| Age Weighting Policy Assessment | `pass` | 0.20s |
| Bond Corpus Drift Snapshot | `pass` | 0.18s |
| Bond Corpus Drift Alert Routing | `pass` | 0.19s |
| OPS-1003 M5 Readiness Review | `pass` | 0.19s |
| OPS-1003 Regression Gate | `pass` | 0.17s |

### Phase E Gate Wiring Notes

- Added strict OPS-1003 regression gate command for CI/bundle enforcement: `python scripts/enforce_ops1003_regression_gates.py --reports-dir reports/phase10_postlaunch --max-residual-risks 0 --require-m5-go`.
- Local validation: `9 passed` (`tests/unit/test_ops1003_regression_gates.py` + `tests/unit/test_ops1003_m5_readiness_assessment.py`).
- Local gate status against latest artifacts: `pass` (`cdr1_medium_coverage_met=true`, `cdr4_source_diversity_met=true`, `residual_risk_count=0`).

## OPS-1001 Telemetry Baseline

- 401 trend summary: `Baseline established. Missing/invalid JWT tokens correctly return 401 with WWW-Authenticate: Bearer header; validated through auth enforcement suites and staged smoke.`
- 403 trend summary: `Baseline established. Cross-tenant access returns 403 and same-tenant non-owner access follows current ownership/superuser policy.`
- Cross-tenant-denied trend summary: `Baseline established. JWT tenant claims drive tenant scoping under enforced mode; cross-tenant reads block with 403.`
- Alert thresholds tuned this week: `no`
- Notes: `No production traffic profile change yet; maintain weekly trend capture and incident routing checks.`

## OPS-1002 Tenant Onboarding Rehearsal

- Rehearsal executed this week: `yes`
- Tenant ID tested: `acme-corp`
- Provisioning + access checks result: `7/9 passed; the 2 non-owner read denials were expected under current authorization model.`
- Rollback notes (if used): `Rollback executed cleanly; test project removed and tenant/project counts restored.`

## OPS-1003 BFMS Hardening Progress

- Reliability/calibration work completed: `CDR-1/CDR-3/CDR-4/CDR-5 are currently met in latest all-cohort snapshot after Phase B backfill.`
- Validation updates: `M5 readiness latest is go with blockers=0 and residual_risk_count=0.`
- Risks/blockers: `No blockers. CDR-2 remains policy hold (healthy recency baseline), so age-weighting stays default-off pending future staleness shift.`
- Plan/reference artifact: `V2/OPS_1003_BFMS_PRODUCTION_SCORING_PLAN.md`
- Calibration snapshot report path: `reports/phase10_postlaunch/bond_corpus_calibration_20260222_164949.md`
- Advisory cohort inference report path: `reports/phase10_postlaunch/advisory_cohort_inference_20260222_164954.md`
- Advisory package smoke report path: `reports/phase10_postlaunch/advisory_package_smoke_20260222_164959.md`
- Age-weighting policy report path: `reports/phase10_postlaunch/age_weighting_policy_20260222_165000.md`
- Drift snapshot report path: `reports/phase10_postlaunch/bond_corpus_drift_20260222_165000.md`
- Alert routing report path: `reports/phase10_postlaunch/bond_corpus_alert_routing_20260222_165001.md`
- OPS-1003 M5 readiness report path: `reports/phase10_postlaunch/ops1003_m5_readiness_20260222_165001.md`

## OPS-1004 Healthcare Readiness Progress

- Corpus intake checks run: `yes`
- Data quality/compliance findings: `363 files discovered and parsed (100.0% parse success), 362 unique CUSIPs, no parse errors.`
- Go/no-go status: `go`
- Assessment report path: `reports/phase10_postlaunch/healthcare_readiness_20260222_164949.md`
- Staging package cohort validation path: `reports/phase10_postlaunch/advisory_cohort_inference_20260222_164954.md`
- Staging package generation smoke path: `reports/phase10_postlaunch/advisory_package_smoke_20260222_164959.md`
- Backfill utilities used (if any): `scripts/backfill_healthcare_obligor_profile.py`, `scripts/backfill_healthcare_research_corpus.py`, `scripts/backfill_waste_feedstock_mitigants.py`, `scripts/backfill_phaseb_cdr_coverage.py`

## OPS-1005 Incident Drill Progress

- Drill executed this week: `yes`
- Detection time: `0.1 min`
- Recovery time: `0.1 min`
- Lessons learned: `JWT secret consistency across drill scripts is required; alerting automation remains a follow-up item.`
- Drill report path: `reports/phase10_postlaunch/INCIDENT_DRILL_TEMPLATE.md`

## Sign-off

- Product/Domain: `Stephen Peterson` / `2026-02-22`
- Engineering: `Stephen Peterson` / `2026-02-22`
- QA/Validation: `Stephen Peterson` / `2026-02-22`
