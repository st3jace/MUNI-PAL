# Phase 4/5 Addendum: Conflict, Dedup, and Archive Review Flow

Last updated: 2026-02-19

## Purpose

Define implementation backlog items for handling duplicate/conflicting ingested inputs with deterministic resolution and auditable reviewer workflows.

## Problem Statement

When many documents are ingested for one project, the same schema path can appear multiple times:
- exact duplicate values (corroboration);
- semantically equivalent values with format differences;
- conflicting values that require decisioning.

Current behavior keeps multiple facts and supports conflict detection/review, but does not yet enforce a strict canonicalization lifecycle.

## Scope Placement

- Phase 4 focus: ingestion/extraction normalization + conflict/dedup primitives.
- Phase 5 focus: readiness/report quality gates using canonical facts only.

## Execution Status

Implemented:
- `DEDUP-401` canonical fingerprinting
- `DEDUP-402` duplicate classification states (`duplicate_exact`, `duplicate_semantic`, `candidate_conflict`)
- `DEDUP-403` source trust scoring
- `DEDUP-404` canonical selector fields and refresh workflow
- `REVIEW-405` archive/unarchive lifecycle API + reason/note + audit
- `REVIEW-406` unresolved conflict/stale pending queue endpoint
- `AUDIT-503` canonical decision audit transitions (`promote_canonical`, `demote`) with actor/rationale/source metadata
- `TEST-504` deterministic selector stability slice (tie-break hardening + repeat-refresh unit coverage)
- `TEST-504` dataset/property-style replay expansion (project-level canonical snapshot replay plus API-level order-invariance checks)
- Baseline replay harness for canonical/archive validation (`scripts/replay_baseline_canonicalization.py`)
- Target baseline environment reconciliation and replay execution: dedup/canonical/archive schema columns applied + backfilled, live baseline `de618f31-bb6f-4905-be68-8445c357ed32` corpus populated (`239` facts), and replay evidence stabilized in `reports/baseline_canonical_replay_20260219.json`
- Stakeholder/default approval completed for replay artifact promotion readiness (`reports/baseline_canonical_replay_20260219.json`, `overall_stable=true`)
- Control baseline policy ratified and enforced: explicit empty control row `41f263ab-d83a-42c6-9f30-be128ddd3320` retained in target DB (`0` artifacts, `0` facts) for deterministic empty-corpus coverage

In validation:
- Promotion of approved replay artifact and gate evidence into target CI release run records

## Backlog (Ordered)

| ID | Phase | Task | Deliverable | Acceptance Criteria | Depends On |
|---|---|---|---|---|---|
| DEDUP-401 | 4 | Canonical fingerprinting | Deterministic fingerprint for each extracted fact (`project_id + schema_path + normalized_value + unit`) | Repeat ingests of same content create same fingerprint; duplicates are detectable | Existing fact ingest |
| DEDUP-402 | 4 | Duplicate classification | Classification states: `duplicate_exact`, `duplicate_semantic`, `candidate_conflict` | Each newly extracted fact is classified on ingest against existing path candidates | DEDUP-401 |
| DEDUP-403 | 4 | Source trust scoring | Source trust rubric by artifact type/source + recency score | Tie-break metadata available for conflict ranking | DEDUP-402 |
| DEDUP-404 | 4 | Canonical fact selector | One canonical active fact per `project_id + schema_path` | Selector output deterministic under same inputs | DEDUP-403 |
| REVIEW-405 | 4 | Archive review flow (new) | Reviewer action `archive` for superseded/redundant facts with mandatory reason | Archived facts excluded from readiness/report calculations but preserved for audit and traceability | DEDUP-404 |
| REVIEW-406 | 4 | Conflict work queue UI/API contract | Queue endpoint for unresolved conflicts and stale pending items | Reviewers can filter by criticality/phase/age | REVIEW-405 |
| READINESS-501 | 5 | Conflict-aware readiness gate | Unresolved critical conflicts reduce readiness and appear in outstanding items | Critical unresolved conflicts block "ready" state | DEDUP-404 |
| REPORT-502 | 5 | Reporting from canonical set only | Reports/readiness/checklist consume canonical active facts; archives excluded | Report snapshot is deterministic and reproducible | READINESS-501 |
| AUDIT-503 | 5 | Decision audit trail expansion | Structured audit events for dedup decisions (`archive`, `promote_canonical`, `demote`) | Every decision has actor, rationale, target, timestamp | REVIEW-405 |
| TEST-504 | 5 | Regression and property tests | Dataset-based and property-style tests for dedup/canonical consistency | Same input corpus yields same canonical outputs across reruns | REPORT-502 |

## Archive Review Flow (Requested Feature)

Proposed reviewer actions on a fact:
- `approve` (active contributor)
- `reject` (invalid)
- `needs_revision` (investigate)
- `archive` (valid but non-canonical/superseded/redundant)

Rules:
1. `archive` requires reason code and free-text note.
2. Archived facts remain queryable with full provenance and revision history.
3. Archived facts are excluded from readiness scoring/checklist fulfillment/report synthesis.
4. Archived facts can be restored to active only by privileged reviewer action (`unarchive`), with audit event.
5. If canonical fact is archived, selector must immediately promote a replacement or mark path unresolved.

Suggested reason codes:
- `superseded_newer_source`
- `superseded_higher_trust_source`
- `duplicate_exact`
- `duplicate_semantic`
- `out_of_scope_for_current_disclosure`

## Data Model Additions (Draft)

- `extracted_facts.lifecycle_state`: `active | archived | rejected | pending_review`
- `extracted_facts.archive_reason_code`: nullable enum
- `extracted_facts.archive_note`: nullable text
- `extracted_facts.archived_by`: nullable user id
- `extracted_facts.archived_at`: nullable timestamp
- `canonical_fact_index` materialized view or table keyed by (`project_id`, `schema_path`)

## API/Service Additions (Draft)

- `POST /facts/{fact_id}/archive`
- `POST /facts/{fact_id}/unarchive`
- `GET /facts/conflicts/queue`
- `GET /facts/{schema_path}/canonical`
- `POST /facts/conflicts/resolve` (extended strategy options beyond highest-confidence)

## Non-Regression Constraints

1. Archive flow must be feature-flagged on rollout (`FACT_ARCHIVE_FLOW_V1`).
2. Existing approve/reject behavior remains unchanged when flag is off.
3. Core flow must pass with and without archive flow enabled.
4. Baseline UCS WTE outputs must remain stable unless deltas are explicitly approved.

## Exit Criteria

Phase 4/5 addendum considered complete when:
1. Deterministic canonical selector is productionized.
2. Archive review flow is active with audit coverage.
3. Readiness and reports use canonical-only facts.
4. Regression suite demonstrates reproducibility on baseline datasets.
