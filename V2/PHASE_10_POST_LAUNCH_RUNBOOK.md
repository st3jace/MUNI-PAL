# Phase 10 Post-Launch Operations Runbook

Last updated: 2026-02-21

## Goal

Run post-launch operational checks and capture evidence for production stability and expansion readiness.

## One-Command Local Execution

From repo root:

```powershell
python scripts/run_phase10_postlaunch_bundle.py
python scripts/assess_healthcare_corpus_readiness.py
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
- `reports/phase10_postlaunch/WEEKLY_EVIDENCE_TEMPLATE.md`

## Weekly Execution Sequence

1. Execute automation bundle and archive artifacts.
2. Fill `reports/phase10_postlaunch/WEEKLY_EVIDENCE_TEMPLATE.md`.
3. Review 401/403/cross-tenant denied trendlines.
4. Confirm open incidents, SLA breaches, and alert quality.
5. Record tenant onboarding rehearsal status (if scheduled).
6. Run healthcare corpus readiness assessment and archive generated reports.
7. Capture incident drill details in `reports/phase10_postlaunch/INCIDENT_DRILL_TEMPLATE.md` when executed.
8. Update `V2/EXECUTION_TRACKER.md` with week summary.

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
