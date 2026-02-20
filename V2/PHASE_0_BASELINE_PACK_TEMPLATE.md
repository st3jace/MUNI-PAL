# Phase 0 Baseline Pack Template

Last updated: 2026-02-18

## Purpose

Capture a frozen, reviewable "known-good" reference for current Muni-Pal behavior before V2 changes.

## How to Use

1. Copy this file to `V2/BASELINE_PACK_YYYYMMDD.md`.
2. Fill every section.
3. Store referenced artifacts in `reports/` or a dedicated baseline folder.
4. Link the completed baseline pack in `V2/EXECUTION_TRACKER.md`.

## Baseline Metadata

- Baseline ID:
- Date captured:
- Captured by:
- Environment:
- Commit/reference snapshot:
- Notes:

## Reference Baseline Datasets (3 slots)

| Dataset ID | Name | Classification | Sector | Why Included | Data Completeness |
|---|---|---|---|---|---|
|  |  | Live project or Non-production control |  |  |  |
|  |  | Live project or Non-production control |  |  |  |
|  |  | Live project or Non-production control |  |  |  |

Selection rule:
- Include at least one legitimate live project.
- If only one live project exists, fill remaining slots with non-production controls (fixture, incomplete project, or orphan corpus).
- Label each dataset explicitly as `Live project` or `Non-production control`.

## Core Flow Baseline Results

Record pass/fail and evidence for each dataset.

| Step | Project 1 | Project 2 | Project 3 | Evidence Link |
|---|---|---|---|---|
| Create/retrieve project |  |  |  |  |
| Upload/process artifacts |  |  |  |  |
| Run extraction and review facts |  |  |  |  |
| Compute readiness/checklist/gaps |  |  |  |  |
| Generate reports/deliverables |  |  |  |  |

Gate:
- All core steps must pass for live project datasets before risky refactors proceed.
- Non-production control failures require review and triage but are not automatic release blockers.

## Output Snapshot (Freeze)

For each project, capture:
- Readiness score output (raw and rendered summary)
- Checklist summary and outstanding items
- Facts status counts and conflict markers
- Generated report artifacts (file names + checksums)
- Any advisory/deliverable package output currently in use

| Project ID | Artifact Type | File/Path | Checksum | Notes |
|---|---|---|---|---|
|  |  |  |  |  |
|  |  |  |  |  |
|  |  |  |  |  |

## API/Contract Snapshot

- OpenAPI spec version/path:
- Frontend client version/hash:
- Known endpoint deviations (if any):

## Comparison Rubric for Future Changes

Classify differences versus baseline:

- `Acceptable`: formatting-only or approved model improvements with no business meaning change.
- `Review Required`: score or checklist deltas within expected tolerance.
- `Blocker`: missing report output, broken core flow step, unauthorized access behavior, or unexplained score delta.

Tolerance policy:
- Readiness score delta threshold (if allowed): ______
- Checklist delta policy: ______
- Facts extraction delta policy: ______

## Rollback Readiness Check

- Previous release artifact/branch identified:
- Feature flags documented:
- DB migration rollback or recovery procedure linked:
- Rollback owner assigned:

## Sign-Off

| Role | Name | Decision | Date | Notes |
|---|---|---|---|---|
| Product/Domain |  |  |  |  |
| Engineering |  |  |  |  |
| QA/Validation |  |  |  |  |

Decision rule:
- Baseline pack is "Approved" only when all sign-off rows are complete.
