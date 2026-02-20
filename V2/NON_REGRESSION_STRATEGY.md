# Non-Regression Strategy

Last updated: 2026-02-18

## Goal

Improve architecture and quality without losing currently working readiness and report functionality.

## Reality Check

No team can guarantee zero defects. We can make regressions unlikely, quickly detectable, and reversible.

## Rules of Execution

1. Baseline before change
- Freeze representative baseline outputs for at least 3 reference datasets (at least 1 live project; remaining slots may be non-production controls).
- Save readiness scores, checklist summaries, and generated report artifacts.

2. Contract-first changes
- Backend OpenAPI is source of truth.
- Frontend uses generated client types only (`frontend/src/types/openapi.generated.ts`).
- OpenAPI snapshot drift is enforced by `tests/contract/test_openapi_contract.py` against `contracts/openapi.v1.json`.
- Any API breaking change requires explicit versioning or migration path.

3. Feature flags for risky changes
- New auth enforcement, extraction behavior, and scoring logic changes are gated.
- Default production behavior stays on known-good path until validation completes.

4. Dual-run for sensitive logic
- For readiness/extraction refactors, run old and new logic in parallel on baseline datasets.
- Compare outputs and require explicit sign-off for deltas.

5. Test pyramid for confidence
- Unit tests for deterministic business rules.
- Integration tests for end-to-end core flow.
- Contract tests to catch frontend/backend mismatch.
- Regression snapshots for report generation.

6. Safe delivery process
- Small PRs, single concern each.
- CI must pass before merge.
- Staging validation before production.
- Canary release + monitoring for first rollout.

7. Rollback always ready
- Every release has a documented rollback command/procedure.
- DB migrations must include backward plan or clear recovery runbook.

## Core Flow Regression Gate

A change is blocked if any of these fail:

1. Project creation and retrieval
2. Artifact upload and processing
3. Extraction run and fact review
4. Readiness/checklist/gaps computation
5. Internal report and advisory package generation

## Metrics We Track Weekly

- Core flow pass rate
- API contract test pass rate
- Number of regressions found post-merge
- Mean time to recover from regression
- Percentage of changes behind feature flags

## Escalation Rule

If two consecutive releases regress core flow, pause feature work and run stabilization sprint.
