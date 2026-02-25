# Phase 2-6 Risk Closeout Runbook

Last updated: 2026-02-25

## Goal

Close active non-Phase-10 risks with repeatable evidence:

- `R-001` API contract drift
- `R-002` Core flow regression during refactor
- `R-003` Test suite staleness

## One-Command Local Execution

From repo root:

```powershell
python scripts/run_phase2_6_risk_closeout_bundle.py
```

## Workflow Dispatch

Workflow: `.github/workflows/phase2-6-risk-closeout-dispatch.yml`

UI:

1. Open Actions tab.
2. Select **Phase 2-6 Risk Closeout Bundle**.
3. Click **Run workflow** and set optional note.
4. Download artifact `phase2-6-risk-closeout-<run_id>`.

CLI fallback (no `gh` required):

```powershell
python scripts/dispatch_github_workflow.py --workflow-id phase2-6-risk-closeout-dispatch.yml --ref master --input note="phase2-6 risk closeout" --wait --require-success
```

## Outputs

Each run writes:

- `reports/phase2_6_closeout/phase2_6_closeout_<timestamp>.md`
- `reports/phase2_6_closeout/phase2_6_closeout_<timestamp>.json`
- `reports/phase2_6_closeout/openapi_generated_artifacts_<timestamp>.md`
- `reports/phase2_6_closeout/openapi_generated_artifacts_<timestamp>.json`
- `reports/phase2_6_closeout/test_suite_health_<timestamp>.md`
- `reports/phase2_6_closeout/test_suite_health_<timestamp>.json`
- `reports/phase2_6_closeout/logs_<timestamp>/`

## Risk Closure Criteria

`R-001` closes when:
- OpenAPI snapshot contract gate passes.
- Generated frontend OpenAPI artifacts match contract snapshot (`verify_openapi_generated_artifacts.py` pass).

`R-002` closes when:
- Core flow regression slice passes (`readiness/checklist/facts/projects/playbooks`).
- Security/tenant/risk regression slice passes.

`R-003` closes when:
- Test suite health gate passes minimum collected threshold.
- All required module watchlist entries collect non-zero tests.
