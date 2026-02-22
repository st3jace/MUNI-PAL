# Phase 10 Post-Launch Operations Backlog

Phase window: 4 weeks

## Objective

Stabilize external launch operations with production telemetry discipline, tenant onboarding confidence, and analytics roadmap hardening.

## Scope Lock

In scope:
- Post-launch monitoring and alert tuning
- Multi-tenant onboarding rehearsal and evidence
- BFMS analytics hardening plan from foundation to production-grade scoring
- Sector expansion readiness for healthcare corpus intake

Out of scope:
- Breaking API contract changes without versioning
- Unbounded model/schema redesign
- New UI redesign unrelated to launch operations

## Backlog (Ordered)

| ID | Task | Deliverable | Acceptance Criteria | Depends On |
|---|---|---|---|---|
| OPS-1001 | Launch telemetry baseline | 7-day dashboard + alert threshold report for 401/403/cross-tenant-denied | Alert thresholds documented and tuned with observed data; no blind spots on authz failures | Phase 9 complete |
| OPS-1002 | Second-tenant onboarding rehearsal | Tenant onboarding runbook execution evidence on non-default tenant | End-to-end tenant provisioning + access validation succeeds with rollback notes | OPS-1001 |
| OPS-1003 | BFMS production-grade scoring plan | Roadmap addendum for reliability, calibration, and governance controls | Plan approved with milestones, data needs, and validation strategy | OPS-1001 |
| OPS-1004 | Healthcare corpus readiness | Intake assessment for EMMA healthcare corpus with quality and compliance checks | Go/no-go assessment recorded with remediation list (if needed) | OPS-1003 |
| OPS-1005 | Post-launch incident drill | Simulated auth/tenant incident timeline with detection and recovery evidence | Detection-to-recovery flow validated with timestamps and owner handoffs | OPS-1002 |

## Definition of Done (Phase 10)

1. Production monitoring thresholds are calibrated from real traffic.
2. Multi-tenant onboarding is rehearsed and documented.
3. BFMS analytics hardening plan is approved and sequenced.
4. Healthcare corpus expansion readiness is explicitly assessed.
5. Incident response drill evidence is captured and reviewed.

## Current Progress (2026-02-22)

- `OPS-1001`: Week 1 telemetry baseline captured and signed in `reports/phase10_postlaunch/WEEKLY_EVIDENCE_TEMPLATE.md`.
- `OPS-1002`: Week 1 second-tenant onboarding rehearsal completed (`acme-corp`) with clean rollback.
- `OPS-1003`: M1 documented, M2 implemented, M3 governance controls delivered, M4 explainability hardening delivered, and M5 routing hardening advanced: cohort-aware profile adjustments + source-diversity/recency diagnostics shipped, extractor-driven calibration/drift automation in place, waste feedstock mitigant backfill utility added/applied (`scripts/backfill_waste_feedstock_mitigants.py`), DSCR robustness guardrails extended (`guardrail.dscr.scenario_sensitivity`, `guardrail.dscr.ratio_consistency`), scoring profile governance metadata/audit mapping added (`scoring_profile_version`, `scoring_profile_checksum`, override `governance_scope`), external/BFMS interpretation guide + traceability compliance checks added, advisory cohort inference validation automation shipped for package-generation profiles (`scripts/assess_advisory_cohort_inference.py`), advisory package generation smoke automation shipped for API-level internal/external generation evidence (`scripts/assess_advisory_package_smoke.py`), CDR-5 alert routing/escalation automation now covers posture/conflict/evidence thresholds via bootstrap-safe proxy series (`scripts/assess_bond_corpus_drift.py`, `scripts/route_bond_corpus_drift_alerts.py`, bundle `--fail-on-critical`), feature-flagged CDR-2 age-weighting landed (`RISK_REPORTING_V2_AGE_WEIGHTING*`) with staged-tuning assessor automation (`scripts/assess_age_weighting_policy.py`), OPS-1003 M5 readiness review automation added (`scripts/assess_ops1003_m5_readiness.py`), Phase B calibration backfill completed (`scripts/backfill_phaseb_cdr_coverage.py`) for CDR-1/CDR-4 closure, and Phase E regression-gate enforcement wired into bundle execution (`scripts/enforce_ops1003_regression_gates.py`). Current calibration baseline: `go` with waste + healthcare all-cohort CDR-1/CDR-3/CDR-4 at 5/5; latest advisory cohort recommendation: `go`; latest advisory package smoke recommendation: `go`; latest age-weighting recommendation: `hold` with healthy recency baseline; latest M5 readiness recommendation: `go` with 0 residual risks (`ops1003_m5_readiness_20260222_165001.json`); latest local bundle: `phase10_postlaunch_20260222_164741.{md,json}`; latest local archive: `phase10_postlaunch_20260222_164741_archive.zip`; latest CI dispatch: `https://github.com/st3jace/MUNI-PAL/actions/runs/22280881561` (`success`).
- `OPS-1004`: Automated readiness assessor added (`scripts/assess_healthcare_corpus_readiness.py`) and baseline report generated (`recommendation=go`); healthcare backfill utilities shipped/applied for obligor profile + research corpus (`scripts/backfill_healthcare_obligor_profile.py`, `scripts/backfill_healthcare_research_corpus.py`) with healthcare CDR-3 all-cohort now 5/5 pair-complete.
- `OPS-1005`: First incident drill completed (`OPS-1005-20260221-01`) and evidence captured in `reports/phase10_postlaunch/INCIDENT_DRILL_TEMPLATE.md`.
