# Phase 4-6 Closeout Runbook

Last updated: 2026-02-25

## Goal

Close remaining implementation gates for:

- Phase 4 ingestion/extraction hardening
- Phase 5 readiness/reporting quality gates
- Phase 6 analytics engine hardening

## One-Command Local Execution

From repo root:

```powershell
python scripts/run_phase4_6_closeout_bundle.py
```

## Workflow Dispatch

Workflow: `.github/workflows/phase4-6-closeout-dispatch.yml`

UI:

1. Open Actions tab.
2. Select **Phase 4-6 Closeout Bundle**.
3. Click **Run workflow** and set optional note.
4. Download artifact `phase4-6-closeout-<run_id>`.

CLI fallback (no `gh` required):

```powershell
python scripts/dispatch_github_workflow.py --workflow-id phase4-6-closeout-dispatch.yml --ref master --input note="phase4-6 closeout" --wait --require-success
```

## Outputs

Each run writes:

- `reports/phase4_6_closeout/phase4_6_closeout_<timestamp>.md`
- `reports/phase4_6_closeout/phase4_6_closeout_<timestamp>.json`
- `reports/phase4_6_closeout/analytics_portability_<timestamp>.md`
- `reports/phase4_6_closeout/analytics_portability_<timestamp>.json`
- `reports/phase4_6_closeout/analytics_reproducibility_<timestamp>.md`
- `reports/phase4_6_closeout/analytics_reproducibility_<timestamp>.json`
- `reports/phase4_6_closeout/analytics_reproducibility_logs_<timestamp>/`
- `reports/phase4_6_closeout/logs_<timestamp>/`

## Exit Criteria Mapping

Phase 4 closes when:
- Async orchestration gate passes (`tests/integration/test_artifacts_api.py`, `tests/unit/test_artifact_dispatch.py`).
- Canonical/archive provenance gate passes (`tests/integration/test_facts_api.py`, `tests/unit/test_fact_service.py`, `tests/unit/test_audit_route_events.py`).

Phase 5 closes when:
- Scoring validation gate passes (`tests/integration/test_risk_reporting_foundation.py`, `tests/unit/test_risk_reporting_service.py`).
- Report quality gate passes (`tests/integration/test_advisory_packages_api.py`, `tests/unit/test_advisory_package_service.py`, `tests/unit/test_audit_route_events.py`).

Phase 6 closes when:
- Hardcoded-path portability gate passes (`scripts/verify_phase6_analytics_portability.py --fail-on-hardcoded`).
- Reproducibility gate passes (`scripts/assess_phase6_analytics_reproducibility.py --fail-on-drift`).

