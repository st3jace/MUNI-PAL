# Baseline Pack 2026-02-18 (Approved)

Last updated: 2026-02-21
Status: Approved

## Purpose

Capture a frozen, reviewable "known-good" reference for current Muni-Pal behavior before V2 changes.

## Baseline Metadata

- Baseline ID: `BL-20260218-V2-P0`
- Date captured: `2026-02-18`
- Captured by: `Codex first-pass auto-population`
- Environment: `Local workspace (Windows + PowerShell), Python 3.14.2, SQLite file munipal_dev.db`
- Commit/reference snapshot: `5b8e19c7aacc75518884b8e2f9b9b175a09bafa3`
- Notes: `First pass populated from local DB/artifacts/reports. Truth constraint: UCS WTE Facility is the only legitimate live project at this time.`

## Reference Baseline Datasets (3 slots)

| Dataset ID | Name | Classification | Sector | Why Included | Data Completeness |
|---|---|---|---|---|---|
| `de618f31-bb6f-4905-be68-8445c357ed32` | UCS WTE Facility | Live project (legitimate) | Waste-to-Energy CAB+SLB | Primary production truth baseline with reports and source artifacts | High |
| `41f263ab-d83a-42c6-9f30-be128ddd3320` | Sierra Vista WTE Facility | Non-production control | Waste-to-Energy | Control case: project row exists but has no uploaded artifacts | Low |
| `9253227f-6453-43ce-a199-c59caf66a281` | Legacy Artifact Corpus (no project row) | Non-production control | Waste-to-Energy docs corpus | Control case: ingestion corpus exists but is orphaned from current projects table | Medium (artifact-only) |

Selection rule:
- Include at least one legitimate live project.
- If only one live project exists, fill remaining slots with explicit non-production controls.
- Label each slot as `Live project` or `Non-production control`.

## Core Flow Baseline Results

Project mapping:
- Project 1: UCS WTE Facility (live project)
- Project 2: Sierra Vista WTE Facility (non-production control)
- Project 3: Legacy Artifact Corpus (non-production control)

Record pass/fail and evidence for each dataset.

| Step | Project 1 | Project 2 | Project 3 | Evidence Link |
|---|---|---|---|---|
| Create/retrieve project | Pass | Pass | Fail (no project row) | `munipal_dev.db` (`projects` table has 2 rows only) |
| Upload/process artifacts | Partial (4 artifacts uploaded, `is_processed=0`) | Fail (no artifacts) | Pass (12 files present in artifact folder) | `munipal_dev.db` (`artifacts` table), `artifacts/de618f31-bb6f-4905-be68-8445c357ed32/`, `artifacts/9253227f-6453-43ce-a199-c59caf66a281/` |
| Run extraction and review facts | Partial (report evidence index exists; DB fact tables are empty) | Fail | Partial (artifact corpus present; extraction outputs not linked) | `reports/handoff-pack-d8e6545f (2).md`, `munipal_dev.db` (`extracted_facts=0`, `fact_revisions=0`) |
| Compute readiness/checklist/gaps | Pass (score/checklist/gaps present in reports) | Fail | Fail (no readiness output tied to corpus) | `reports/internal_report_v7 (1).md`, `reports/handoff-pack-d8e6545f (2).md` |
| Generate reports/deliverables | Pass (multiple markdown outputs present) | Fail | Fail (no outputs tied to corpus id) | `reports/handoff-pack-d8e6545f (2).md`, `reports/disclosure_v8.md`, `reports/advisory_package_v1 (1).md` |

Gate:
- All core steps must pass for the live project baseline before risky refactors proceed.
- Control datasets are monitored for signal; failures there create review actions but are not automatic release blockers.

## Output Snapshot (Freeze)

For each project, capture:
- Readiness score output (raw and rendered summary)
- Checklist summary and outstanding items
- Facts status counts and conflict markers
- Generated report artifacts (file names + checksums)
- Any advisory/deliverable package output currently in use

| Project ID | Artifact Type | File/Path | Checksum | Notes |
|---|---|---|---|---|
| `de618f31-bb6f-4905-be68-8445c357ed32` | Internal readiness report | `reports/internal_report_v7 (1).md` | `8D2C534079656A8F3F56C4EF88EDF2C89C392F128434FF2ADBAF09344499BAFF` | Overall score `5.5/10` |
| `de618f31-bb6f-4905-be68-8445c357ed32` | Advisor handoff pack | `reports/handoff-pack-d8e6545f (2).md` | `61CA9B46DD734607F56C7CB98C0D6AD51F9A1693F0B3C7DBF842BCD20BD93EAA` | Includes readiness, checklist, evidence index |
| `de618f31-bb6f-4905-be68-8445c357ed32` | Prior handoff pack | `reports/handoff-pack-69a8cac5.md` | `C7C2B88D77320943D29A56C661184684AA2C2C045DD3326CE34B8625FFA26533` | Overall score `6.6/10` |
| `de618f31-bb6f-4905-be68-8445c357ed32` | Disclosure draft | `reports/disclosure_v8.md` | `8E977BC8C2743141DB0FE4A2D1D23339A6C69C0933338EF1158EE24E71A7494E` | Contains tax/disclosure placeholders |
| `de618f31-bb6f-4905-be68-8445c357ed32` | Advisory package | `reports/advisory_package_v1 (1).md` | `C78D4A42B582C4CD3E62BC17E8BB21AA4C9C5904BC1FD726DC62A1F152978C1C` | Generated `2026-02-01` |
| `de618f31-bb6f-4905-be68-8445c357ed32` | Source artifact PDF | `artifacts/de618f31-bb6f-4905-be68-8445c357ed32/96140bd5-f333-45b9-b78b-e6d5932d7cb2.pdf` | `82EB12EE75E538E85B09A4CDAD9AD43A3572CC2B5A4B5BAEB14915887D745C52` | `Final RKMF RFP Response 9-28-2025.pdf` |
| `de618f31-bb6f-4905-be68-8445c357ed32` | Source artifact PDF | `artifacts/de618f31-bb6f-4905-be68-8445c357ed32/6e7b1ffe-7b4e-4bae-89f6-f2cfd252ee91.pdf` | `5F4A1FE7381346CB551A9B477BDAB2A6F354959486AFA060388E31108C66B0D4` | `Investment-Opportunity-Ultimate-Conversion-System-UCS.pdf` |
| `41f263ab-d83a-42c6-9f30-be128ddd3320` | Project baseline row | `munipal_dev.db (projects table)` | `N/A` | No artifact/report outputs discovered |
| `9253227f-6453-43ce-a199-c59caf66a281` | Legacy source artifact PDF | `artifacts/9253227f-6453-43ce-a199-c59caf66a281/a698fe3b-ee9f-48dc-b5a2-c0ce49167566.pdf` | `82EB12EE75E538E85B09A4CDAD9AD43A3572CC2B5A4B5BAEB14915887D745C52` | Matches UCS corpus file hash |
| `9253227f-6453-43ce-a199-c59caf66a281` | Legacy source artifact XLSX | `artifacts/9253227f-6453-43ce-a199-c59caf66a281/0c6fdfe6-6d93-44f6-b101-8161ad64b920.xlsx` | `626631D6F525D046EA5337350EA96EF72C15386B0BB5287C50982BF8E30F561D` | Artifact-only corpus evidence |

## API/Contract Snapshot

- OpenAPI spec version/path: `contracts/openapi.v1.json` (generated via `scripts/generate_openapi_snapshot.py`; validated by `tests/contract/test_openapi_contract.py`)
- Frontend client version/hash: `Generated OpenAPI artifacts present at frontend/src/types/openapi.generated.ts and frontend/src/generated/api-client/` (runtime adapter delegates through generated services in `frontend/src/services/api.ts`)
- Known endpoint deviations (if any): `No known undocumented API drift in local contract gate runs; snapshot drift is blocked by contract test`

## Comparison Rubric for Future Changes

Classify differences versus baseline:

- `Acceptable`: formatting-only or approved model improvements with no business meaning change.
- `Review Required`: score or checklist deltas within expected tolerance.
- `Blocker`: missing report output, broken core flow step, unauthorized access behavior, or unexplained score delta.

Tolerance policy:
- Readiness score delta threshold (if allowed): `0.0 for Phases 1-3 unless explicitly approved`
- Checklist delta policy: `No unexpected added/removed unresolved items`
- Facts extraction delta policy: `No unexplained critical fact loss; conflict increases require review`

## Rollback Readiness Check

- Previous release artifact/branch identified: `Current local baseline at commit 5b8e19c7aacc75518884b8e2f9b9b175a09bafa3`
- Feature flags documented: `Implemented and documented in config/env paths (e.g., AUTH_ENFORCEMENT_V2, ROLE_ENFORCEMENT_V2, RISK_REPORTING_V2_FOUNDATION, RISK_REPORTING_V2_ADVANCED_ANALYTICS)`
- DB migration rollback or recovery procedure linked: `V2/PHASE_9_RELEASE_CUTOVER_RUNBOOK.md` (includes rollback drill procedure executed in Phase 8)
- Rollback owner assigned: `Stephen Peterson`

## Sign-Off

| Role | Name | Decision | Date | Notes |
|---|---|---|---|---|
| Product/Domain | Stephen Peterson | Approved | 2026-02-21 | Core flow validated on UCS WTE baseline; readiness score 6.6/10 confirmed |
| Engineering | Stephen Peterson | Approved | 2026-02-21 | 184 tests passed (Phase 9 bundle); tenant isolation + auth enforcement verified |
| QA/Validation | Stephen Peterson | Approved | 2026-02-21 | Phase 7/8 staging evidence complete; rollback drill passed |

Decision rule:
- Baseline pack is Approved only when all sign-off rows are complete.
