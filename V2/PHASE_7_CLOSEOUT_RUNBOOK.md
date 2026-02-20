# Phase 7 Closeout Runbook

Last updated: 2026-02-19

## Goal

Generate one evidence bundle that captures local CI-equivalent validation for Phase 7 and provides a checklist for final target CI/staging closeout.

## One-Command Execution

Run from repo root:

```powershell
python scripts/run_phase7_closeout_bundle.py
```

## GitHub Workflow Dispatch (Recommended for Target CI)

Use workflow: `.github/workflows/phase7-closeout-dispatch.yml`

1. Open GitHub repository -> **Actions**.
2. Select **Phase 7 Closeout Bundle** workflow.
3. Click **Run workflow**.
4. Choose branch/commit context and optionally add a note.
5. Start run and wait for completion.
6. Download artifact `phase7-closeout-<run_id>` from the workflow run.
7. Use the artifact markdown/json/log files to populate `reports/phase7_closeout/STAGING_EVIDENCE_TEMPLATE.md`.

## Outputs

Each run writes timestamped artifacts to:

- `reports/phase7_closeout/phase7_closeout_<timestamp>.md`
- `reports/phase7_closeout/phase7_closeout_<timestamp>.json`
- `reports/phase7_closeout/logs_<timestamp>/`
- `reports/phase7_closeout/STAGING_EVIDENCE_TEMPLATE.md` (manual evidence capture)

The Markdown report includes:

- automated gate results and pass/fail status
- links to command logs
- a manual target CI/staging closeout checklist

## Scope of Automated Checks

1. Backend CI-equivalent gate (matches `.github/workflows/core-security-risk-gate.yml`)
2. Frontend test suite (`vitest`)
3. Frontend production build
4. Risk-focused regression slice (`risk_reporting` + `advisory_package_service`)

## Final Target Closeout (Manual)

After the script passes locally:

1. Confirm first green run of `.github/workflows/core-security-risk-gate.yml` in target CI.
2. Validate BFMS integration endpoint full and fallback mode behavior in staging.
3. Validate Readiness and Advisory Packages UI mode/fallback rendering in staging.
4. Confirm external package generation carries BFMS integration context in summary/assumptions.
5. Attach CI run URL and staging evidence references in `V2/EXECUTION_TRACKER.md`.
