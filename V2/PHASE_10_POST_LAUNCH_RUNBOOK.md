# Phase 10 Post-Launch Operations Runbook

Last updated: 2026-02-22

## Goal

Run post-launch operational checks and capture evidence for production stability and expansion readiness.

## One-Command Local Execution

From repo root:

```powershell
python scripts/run_phase10_postlaunch_bundle.py
python scripts/cleanup_corpus_db_outliers.py
python scripts/rebuild_corpus_document_index.py --clear-existing
python scripts/verify_corpus_db_reconciliation.py --fail-on-extra-db --fail-on-index-extras --fail-on-type-mismatch
python scripts/assess_healthcare_corpus_readiness.py
python scripts/backfill_healthcare_obligor_profile.py
python scripts/backfill_healthcare_research_corpus.py
python scripts/backfill_waste_feedstock_mitigants.py
python scripts/assess_bond_corpus_calibration.py
python scripts/assess_advisory_cohort_inference.py
python scripts/assess_advisory_package_smoke.py --mode asgi
python scripts/assess_age_weighting_policy.py
python scripts/assess_bond_corpus_drift.py
python scripts/route_bond_corpus_drift_alerts.py --fail-on-critical
python scripts/assess_ops1003_m5_readiness.py
python scripts/enforce_ops1003_regression_gates.py --reports-dir reports/phase10_postlaunch --max-residual-risks 1 --require-m5-go
```

Note: `assess_advisory_package_smoke.py --mode asgi` now defaults to an isolated ephemeral sqlite DB so local stale schemas do not affect smoke outcomes. Use `--asgi-sqlite-path <path>` only when you intentionally want a persistent DB for debugging.

Staging/live API smoke mode:

```powershell
python scripts/assess_advisory_package_smoke.py --mode http --base-url http://127.0.0.1:8000 --project-id <project_uuid>
```

## GitHub Workflow Dispatch

Workflow: `.github/workflows/phase10-postlaunch-dispatch.yml`

1. Open Actions tab.
2. Select **Phase 10 Post-Launch Bundle**.
3. Click **Run workflow** and set optional note/week label.
4. Download artifact `phase10-postlaunch-<run_id>`.

## Outputs

Each run writes:

- `reports/phase10_postlaunch/phase10_postlaunch_<timestamp>.md`
- `reports/phase10_postlaunch/phase10_postlaunch_<timestamp>.json`
- `reports/phase10_postlaunch/logs_<timestamp>/`
- `reports/phase10_postlaunch/healthcare_readiness_<timestamp>.md`
- `reports/phase10_postlaunch/healthcare_readiness_<timestamp>.json`
- `reports/phase10_postlaunch/bond_corpus_calibration_<timestamp>.md`
- `reports/phase10_postlaunch/bond_corpus_calibration_<timestamp>.json`
- `reports/phase10_postlaunch/advisory_cohort_inference_<timestamp>.md`
- `reports/phase10_postlaunch/advisory_cohort_inference_<timestamp>.json`
- `reports/phase10_postlaunch/advisory_package_smoke_<timestamp>.md`
- `reports/phase10_postlaunch/advisory_package_smoke_<timestamp>.json`
- `reports/phase10_postlaunch/age_weighting_policy_<timestamp>.md`
- `reports/phase10_postlaunch/age_weighting_policy_<timestamp>.json`
- `reports/phase10_postlaunch/bond_corpus_drift_<timestamp>.md`
- `reports/phase10_postlaunch/bond_corpus_drift_<timestamp>.json`
- `reports/phase10_postlaunch/bond_corpus_alert_routing_<timestamp>.md`
- `reports/phase10_postlaunch/bond_corpus_alert_routing_<timestamp>.json`
- `reports/phase10_postlaunch/ops1003_m5_readiness_<timestamp>.md`
- `reports/phase10_postlaunch/ops1003_m5_readiness_<timestamp>.json`
- `reports/phase10_postlaunch/WEEKLY_EVIDENCE_TEMPLATE.md`

## Weekly Execution Sequence

1. Execute automation bundle and archive artifacts.
2. Fill `reports/phase10_postlaunch/WEEKLY_EVIDENCE_TEMPLATE.md`.
3. Review 401/403/cross-tenant denied trendlines.
4. Confirm open incidents, SLA breaches, and alert quality.
5. Record tenant onboarding rehearsal status (if scheduled).
6. Run healthcare corpus readiness assessment and archive generated reports.
7. Apply healthcare evidence backfill utilities when new obligor/research corpus inputs are available.
8. Apply waste feedstock mitigant backfill utility when updated implementation-guide evidence is available.
9. Run bond corpus calibration assessment and record CDR-3 coverage gaps by sector/cohort.
10. Run advisory cohort inference assessment and record inferred sector/deal-type profile validation for package generation.
11. Run advisory package smoke assessment and record internal/external generation API evidence.
12. Run age-weighting policy assessment and record CDR-2 staged enable/tuning recommendation.
13. Run bond corpus drift assessment and record pair-completeness transitions / recommendation deltas.
14. Run drift alert routing and review incident/hold recommendations in `bond_corpus_alert_routing_<timestamp>.md/.json`.
15. Run OPS-1003 M5 readiness assessment and record go/no-go with residual risks in `ops1003_m5_readiness_<timestamp>.md/.json`.
16. Run OPS-1003 regression gate enforcement (`enforce_ops1003_regression_gates.py`) and fail weekly bundle if CDR-1/CDR-4 regress or residual risks exceed threshold.
17. Review external/BFMS interpretation-guide and compliance-check fields for disclosure-safe narrative consistency.
18. Capture incident drill details in `reports/phase10_postlaunch/INCIDENT_DRILL_TEMPLATE.md` when executed.
19. Update `V2/EXECUTION_TRACKER.md` with week summary.

## Incident Escalation

Escalate immediately when:

- 401/403 spikes exceed threshold window
- Cross-tenant-denied events present unexpected patterns
- Core flow regression is observed in production telemetry

Escalation actions:

1. Open incident with timestamp and owner.
2. Capture representative request IDs/log entries.
3. Execute rollback toggles per impacted control path.
4. Validate recovery endpoints and summarize impact.
