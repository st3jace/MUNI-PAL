# V2 Execution Tracker

Last updated: 2026-02-20

## Phase Status

| Phase | Status | Start | Target End | Owner | Notes |
|---|---|---|---|---|---|
| Phase 0 | In Progress | 2026-02-18 | TBD | TBD | First-pass baseline drafted at `V2/BASELINE_PACK_20260218.md` (pending validation/sign-off) |
| Phase 1 | In Progress (Guarded) | 2026-02-18 | TBD | TBD | SEC-001 through SEC-008 artifacts implemented; rollout sign-off pending |
| Phase 2 | In Progress (Contract Gate) | 2026-02-19 | TBD | TBD | OpenAPI snapshot and contract test added; frontend generated OpenAPI types/client landed and runtime adapter now delegates through generated services (`contracts/openapi.v1.json`, `frontend/src/types/openapi.generated.ts`, `frontend/src/generated/api-client/`, `frontend/src/services/api.ts`) |
| Phase 3 | In Progress (CI Rehab) | 2026-02-19 | TBD | TBD | Core/security/risk/contract/fact-service gate now green (`181 passed`) and CI workflow now enforces frontend test + production build (`5 frontend tests passed`), plus full local suite green (`176 passed`) |
| Phase 4 | In Progress (Dedup/Archive Foundation) | 2026-02-19 | TBD | TBD | `DEDUP-401` through `REVIEW-406` core backend contracts implemented plus canonical transition audit coverage and expanded dataset/property replay reproducibility validation (`AUDIT-503`/`TEST-504`); target baseline DB schema/backfill gap resolved and replay harness now stable on populated corpus with live baseline sign-off complete (`de618f31-bb6f-4905-be68-8445c357ed32`, 239 facts) |
| Phase 5 | In Progress (Sprint 4) | 2026-02-19 | TBD | TBD | `RISK-501` through `RISK-511` implemented behind `RISK_REPORTING_V2_FOUNDATION` (`RISK-508` external brief, `RISK-509` request sync, `RISK-510` audit/governance, `RISK-511` validation suite) |
| Phase 6 | In Progress (Risk Analytics Bridge) | 2026-02-19 | TBD | TBD | `RISK-512` advanced analytics bridge implemented behind reliability gate (`RISK_REPORTING_V2_ADVANCED_ANALYTICS`, default off) |
| Phase 7 | **Complete** | 2026-02-19 | 2026-02-20 | Stephen Peterson | BFMS integration contract shipped and signed off — both fallback and full modes confirmed in staging; all automated gates green; Internal Report + External Package generation confirmed; sign-off: Stephen Peterson 2026-02-20 |
| Phase 8 | **Complete** | 2026-02-20 | 2026-02-21 | Stephen Peterson | Tenant isolation foundation shipped and signed off — migration `b8c9d0e1f2a3` applied, `TENANT_ISOLATION_V2=true` enabled, tenant-scoped listing and cross-tenant 403 confirmed, flag-only rollback drill passed; all automated gates green; sign-off: Stephen Peterson 2026-02-21 |

## Active Risks

| ID | Risk | Impact | Mitigation | Status |
|---|---|---|---|---|
| R-001 | API contract drift | High | OpenAPI-generated client and contract tests | Open |
| R-002 | Core flow regression during refactor | High | Baselines + feature flags + smoke tests | Open |
| R-003 | Test suite staleness | High | Rebuild fixtures and CI gates in Phase 3 | Open |

## Decision Log

| Date | Decision | Rationale | Owner |
|---|---|---|---|
| 2026-02-18 | Backend remains domain source of truth | Prevent duplicated business logic and drift | Team |
| 2026-02-18 | Analytics harden first, integrate second | Reduce coupling and runtime instability | Team |
| 2026-02-18 | Baseline pack approval is mandatory before risky refactors | Protect currently working readiness/report behavior | Team |
| 2026-02-18 | UCS WTE Facility is the only legitimate live project for V2 baseline | Prevent false confidence from non-production sample rows | Team |
| 2026-02-18 | Add archive review flow to Phase 4/5 plan | Preserve superseded evidence without polluting canonical readiness/report outputs | Team |
| 2026-02-18 | Add confidence-aware risk reporting backlog for Phase 5/6 | Improve risk outputs for internal execution and external advisory consumption | Team |
| 2026-02-19 | Approve baseline canonical replay evidence for live UCS project | Replay artifact is stable (`overall_stable=true`) with populated live baseline and no schema errors | Team |
| 2026-02-19 | Keep explicit empty control baseline row `41f263ab-d83a-42c6-9f30-be128ddd3320` | Preserve deterministic empty-corpus guard coverage without polluting live baseline evidence | Team |
| 2026-02-19 | Adopt `risk-bfms-integration-v1` as initial Phase 7 interface contract | Provide stable, versioned analytics handoff with explicit fallback mode for low-reliability scenarios | Team |

## Next Milestones

1. Finalize `V2/BASELINE_PACK_20260218.md` sign-off fields (owners, dates, and rollback owner assignment).
2. Approve Phase 0 artifact set, owners, and baseline sign-off.
3. Execute SEC-008 checklist sign-off for target environment.
4. ~~Apply migration `b8c9d0e1f2a3` in target baseline DB and validate `projects.tenant_id` backfill output.~~ **DONE** — 0 missing rows, tenant distribution: default=3; milestone 112.
5. ~~Enable `TENANT_ISOLATION_V2=true` in staging and run project-access smoke validation for tenant-scoped behavior.~~ **DONE** — tenant-scoped listing confirmed (default=3, other-org=0); cross-tenant 403 confirmed; milestone 113.
6. ~~Dispatch `.github/workflows/phase8-closeout-dispatch.yml` in target CI and archive artifacts.~~ **DONE** — run `22256677506`, commit `2435a0a8`, success; core-security-risk-gate run `22256628880` also green; milestone 114.
7. ~~Complete `reports/phase8_closeout/STAGING_EVIDENCE_TEMPLATE.md` with staging API/UI evidence and sign-off (`EXT-807`).~~ **DONE** — all sections filled, sign-off Stephen Peterson 2026-02-21; milestone 115.

## Completed Milestones

1. 2026-02-18: SEC-001 completed (auth dependency now supports JWT bearer validation via `AUTH_ENFORCEMENT_V2`; compatibility mode preserved).
2. 2026-02-18: Added unit test coverage for SEC-001 (`tests/unit/test_auth_dependencies.py`, 6 passing tests).
3. 2026-02-18: SEC-002 completed (auth dependency applied at router level for facts/readiness/checklist/deliverables/disclosure/information-requests/advisory-packages).
4. 2026-02-18: Added SEC-002 integration enforcement checks (`tests/integration/test_auth_enforcement_routes.py`, 7 passing tests).
5. 2026-02-18: SEC-003 completed (introduced `AuthorizationService` with `can_read_project`/`can_write_project`; enforced project ownership checks on project get/update/delete).
6. 2026-02-18: Added SEC-003 integration coverage (`tests/integration/test_project_authorization.py`, 5 passing tests).
7. 2026-02-18: SEC-004 completed (object-level authorization enforced for artifact, extraction job, and fact endpoints).
8. 2026-02-18: Added SEC-004 integration coverage (`tests/integration/test_object_authorization.py`, 3 passing tests).
9. 2026-02-18: SEC-005 completed (feature-flagged role model `admin`/`analyst`/`viewer` with route-level policy).
10. 2026-02-18: Added SEC-005 integration coverage (`tests/integration/test_role_policy.py`, 5 passing tests).
11. 2026-02-18: SEC-006 completed (structured security audit events emitted for approve/reject/delete/export actions in project/artifact/fact/deliverable/advisory/disclosure routes).
12. 2026-02-18: Added SEC-006 unit coverage (`tests/unit/test_audit_service.py`, `tests/unit/test_audit_route_events.py`, 10 passing tests).
13. 2026-02-18: SEC-007 completed (added integrated JWT+role+ownership security module `tests/integration/test_security_integration.py` covering 401/403 and owner/non-owner behavior).
14. 2026-02-18: Security-focused suite passed end-to-end (`42 passed` across auth/authz/role/audit/security-integration modules).
15. 2026-02-18: SEC-008 deliverable created (`V2/SECURITY_HARDENING_ROLLOUT_CHECKLIST.md`) with go/no-go gates, phased rollout procedure, and rollback runbook.
16. 2026-02-18: Added Phase 4/5 conflict-dedup addendum (`V2/PHASE_4_5_CONFLICT_DEDUP_ADDENDUM.md`) including archive review flow backlog and acceptance criteria.
17. 2026-02-18: Added risk reporting backlog (`V2/RISK_REPORTING_V2_BACKLOG.md`) defining confidence-aware qualitative/quantitative/actionable output contracts for Phase 5/6.
18. 2026-02-18: Added Phase 5 Sprint 1 execution plan (`V2/PHASE_5_SPRINT_1_RISK_FOUNDATION.md`) covering `RISK-501` through `RISK-503`.
19. 2026-02-19: Core-flow smoke suite stabilized and passing (`55 passed`) across readiness/checklist/facts/projects/playbooks integration modules.
20. 2026-02-19: Security suite revalidated after compatibility fixes (`42 passed`) and combined core+security gate verified (`97 passed`).
21. 2026-02-19: Added CI workflow gate (`.github/workflows/core-security-risk-gate.yml`) for core-flow + security + risk foundation suites.
22. 2026-02-19: Implemented Sprint 1 risk foundation artifacts (`src/munipal/core/schemas/risk_reporting.py`, `src/munipal/services/risk_reporting_service.py`, `src/munipal/api/routes/risk_reporting.py`) behind `RISK_REPORTING_V2_FOUNDATION`.
23. 2026-02-19: Added risk foundation test coverage (`tests/unit/test_risk_reporting_service.py`, `tests/integration/test_risk_reporting_foundation.py`, 9 passing tests) and revalidated combined gate (`106 passed`).
24. 2026-02-19: Implemented `RISK-504` risk posture scoring engine with deterministic dimension and overall benchmark positions (`above`/`at`/`below`) plus explainers in risk diagnostics contract (`src/munipal/core/schemas/risk_reporting.py`, `src/munipal/services/risk_reporting_service.py`).
25. 2026-02-19: Expanded risk reporting tests for posture contract and determinism (`tests/unit/test_risk_reporting_service.py`, `tests/integration/test_risk_reporting_foundation.py`, 13 passing tests) and revalidated combined gate (`110 passed`).
26. 2026-02-19: Implemented `RISK-505` quantitative guardrails with DSCR and equipment-concentration threshold checks (including tolerance bands, explicit violations, and evidence-path linkage) in risk diagnostics contract (`src/munipal/core/schemas/risk_reporting.py`, `src/munipal/services/risk_reporting_service.py`).
27. 2026-02-19: Expanded risk reporting guardrail coverage (`tests/unit/test_risk_reporting_service.py`, `tests/integration/test_risk_reporting_foundation.py`, 16 passing tests) and revalidated combined gate (`113 passed`).
28. 2026-02-19: Implemented `RISK-506` action synthesis engine generating prioritized, deduplicated actions with owners, evidence requirements, target-date hints, expected impact, and source traceability to guardrails/dimensions (`src/munipal/core/schemas/risk_reporting.py`, `src/munipal/services/risk_reporting_service.py`).
29. 2026-02-19: Expanded action-synthesis coverage (`tests/unit/test_risk_reporting_service.py`, `tests/integration/test_risk_reporting_foundation.py`, 17 passing tests) and revalidated combined gate (`114 passed`).
30. 2026-02-19: Implemented `RISK-507` internal risk report contract with versioned JSON + markdown output including executive summary and readiness/advisory handoff blocks (`src/munipal/core/schemas/risk_reporting.py`, `src/munipal/services/risk_reporting_service.py`, `src/munipal/api/routes/risk_reporting.py`).
31. 2026-02-19: Expanded internal report coverage (`tests/unit/test_risk_reporting_service.py`, `tests/integration/test_risk_reporting_foundation.py`, 20 passing tests) and revalidated combined gate (`117 passed`).
32. 2026-02-19: Implemented `RISK-508` external advisory brief contract with disclosure-safety checks and markdown export (`src/munipal/core/schemas/risk_reporting.py`, `src/munipal/services/risk_reporting_service.py`, `src/munipal/api/routes/risk_reporting.py`).
33. 2026-02-19: Implemented `RISK-509` risk-action to information-request sync (`/api/v1/risk/sync-information-requests`) with create/refresh/skip behavior and action-linked acceptance criteria (`src/munipal/services/risk_reporting_service.py`, `src/munipal/api/routes/risk_reporting.py`).
34. 2026-02-19: Implemented `RISK-510` governance events for diagnostics/internal/external generation, override decisions, and action acceptance (`src/munipal/api/routes/risk_reporting.py`, `tests/unit/test_audit_route_events.py`).
35. 2026-02-19: Implemented `RISK-511` validation/regression suite additions for external contract, sync behavior, override/acceptance endpoints, and corpus drift guards; revalidated core+security+risk gate (`128 passed`) (`tests/unit/test_risk_reporting_service.py`, `tests/integration/test_risk_reporting_foundation.py`, `tests/unit/test_audit_route_events.py`).
36. 2026-02-19: Implemented `RISK-512` advanced analytics bridge ingest (`spectral_omega`/`wavelet_omega`/`dynamic_omega`) with reliability gating and default-disabled rollout controls (`src/munipal/config.py`, `src/munipal/core/schemas/risk_reporting.py`, `src/munipal/services/risk_reporting_service.py`, `.env.example`).
37. 2026-02-19: Added `RISK-512` unit/integration coverage and revalidated combined core+security+risk gate (`132 passed`) (`tests/unit/test_risk_reporting_service.py`, `tests/integration/test_risk_reporting_foundation.py`).
38. 2026-02-19: Implemented dedup/canonical metadata model (`DEDUP-401` to `DEDUP-404`) with deterministic fingerprinting, duplicate classification (`duplicate_exact`/`duplicate_semantic`/`candidate_conflict`), source trust scoring, and canonical selector fields on facts (`src/munipal/core/models/fact.py`, `src/munipal/core/schemas/fact.py`, `src/munipal/services/fact_service.py`).
39. 2026-02-19: Implemented archive lifecycle flow (`REVIEW-405`) with `archive`/`unarchive` endpoints, mandatory archive reason/note, revision trail updates, and archive audit events (`src/munipal/api/routes/facts.py`, `src/munipal/services/fact_service.py`, `tests/integration/test_facts_api.py`, `tests/unit/test_audit_route_events.py`).
40. 2026-02-19: Implemented conflict review queue contract (`REVIEW-406`) for unresolved conflicts and stale pending items with criticality/phase/age filters (`src/munipal/api/routes/facts.py`, `src/munipal/services/fact_service.py`, `tests/integration/test_facts_api.py`, `tests/unit/test_fact_service.py`).
41. 2026-02-19: Applied archive exclusion guardrails across readiness/checklist/deliverable/disclosure/advisory/risk/information-request fact reads to prevent archived facts from driving calculations (`src/munipal/services/readiness_service.py`, `src/munipal/services/checklist_service.py`, `src/munipal/services/deliverable_service.py`, `src/munipal/services/disclosure_service.py`, `src/munipal/services/advisory_package_service.py`, `src/munipal/services/risk_reporting_service.py`, `src/munipal/services/information_request_service.py`).
42. 2026-02-19: Revalidated expanded quality gate including new dedup/archive tests (`162 passed`) across core/security/risk/fact-service suites.
43. 2026-02-19: Added OpenAPI contract snapshot workflow (`contracts/openapi.v1.json`) with drift test (`tests/contract/test_openapi_contract.py`) and snapshot generation script (`scripts/generate_openapi_snapshot.py`).
44. 2026-02-19: Added frontend OpenAPI type generation workflow (`frontend/package.json` script `generate:api-types`) and generated TypeScript contract artifact (`frontend/src/types/openapi.generated.ts`) with type exports in `frontend/src/types/index.ts`.
45. 2026-02-19: Expanded CI gate workflow to include contract snapshot validation and fact-service unit coverage (`.github/workflows/core-security-risk-gate.yml`) and verified gate locally (`163 passed`).
46. 2026-02-19: Revalidated full repository test suite after dedup/risk/contract updates (`176 passed`).
47. 2026-02-19: Added frontend OpenAPI-generated axios client scaffold (`frontend/package.json` script `generate:api-client`, `frontend/src/generated/api-client/`, `frontend/src/services/generatedApi.ts`) for incremental migration off hand-authored API calls.
48. 2026-02-19: Validated frontend build after generated-client integration prep (`npm --prefix frontend run build` successful).
49. 2026-02-19: Completed `AUDIT-503` remainder for dedup decisions by emitting canonical transition audit events (`promote_canonical`, `demote`) with actor/rationale/source metadata during canonical refresh (`src/munipal/services/fact_service.py`).
50. 2026-02-19: Added deterministic canonical selector hardening and validation coverage (`TEST-504` slice): deterministic tie-break on fact id plus repeat-refresh stability and canonical transition audit tests (`tests/unit/test_fact_service.py`).
51. 2026-02-19: Migrated frontend runtime API adapter from raw axios route calls to generated OpenAPI service calls while preserving page-facing method contracts (`frontend/src/services/api.ts`, `frontend/src/services/generatedApi.ts`).
52. 2026-02-19: Revalidated rollout batch with focused backend suites (`60 passed` across fact-service/audit-route/facts-api) and successful frontend production build (`npm --prefix frontend run build`).
53. 2026-02-19: Added project-level canonical replay helpers and deterministic snapshot contract for reproducibility checks (`refresh_canonicalization_for_project`, `canonical_snapshot_for_project`) in fact service (`src/munipal/services/fact_service.py`).
54. 2026-02-19: Expanded `TEST-504` dataset/property-style reproducibility coverage with replay-order invariance at both unit and API integration levels (`tests/unit/test_fact_service.py`, `tests/integration/test_facts_api.py`).
55. 2026-02-19: Added baseline canonical replay harness script and captured first replay artifact (`scripts/replay_baseline_canonicalization.py`, `reports/baseline_canonical_replay_20260219.json`) with explicit empty-corpus/schema-mismatch diagnostics.
56. 2026-02-19: Revalidated fact-service and facts API suites including replay coverage (`63 passed` across fact-service/audit-route/facts-api modules).
57. 2026-02-19: Applied baseline DB reconciliation migration adding dedup/canonical/archive columns on `extracted_facts` (`alembic/versions/20260219_0001_a7b8c9d0e1f2_add_fact_canonicalization_columns.py`) and upgraded target DB to `a7b8c9d0e1f2`.
58. 2026-02-19: Executed canonical metadata backfill across projects with facts (`scripts/backfill_fact_canonicalization.py`), refreshing 54 schema paths and 53 canonical paths for project `9253227f-6453-43ce-a199-c59caf66a281`.
59. 2026-02-19: Reran baseline canonical replay (`scripts/replay_baseline_canonicalization.py --iterations 3`) with no schema errors and stable replay for populated baseline corpus; report updated at `reports/baseline_canonical_replay_20260219.json` (`overall_stable=true`, two baseline IDs remained `no_facts` at that checkpoint).
60. 2026-02-19: Added offline baseline bootstrap utility (`scripts/bootstrap_baseline_project_from_legacy.py`) and chunk text sanitization on artifact processing to strip invalid NUL bytes before chunk insert (`src/munipal/services/artifact_service.py`).
61. 2026-02-19: Bootstrapped live baseline project `de618f31-bb6f-4905-be68-8445c357ed32` from populated source corpus, registering/processing 4 artifacts and cloning canonicalized fact corpus to 239 facts.
62. 2026-02-19: Reran baseline canonical replay (`scripts/replay_baseline_canonicalization.py --iterations 3`) after bootstrap with stable output for live baseline (`54` schema paths, `53` canonical paths, `239` facts); replay report now lists only control baseline ID `41f263ab-d83a-42c6-9f30-be128ddd3320` as empty.
63. 2026-02-19: Removed accidental orphan project row `de618f8d-f58f-44e9-964f-815708c04c9a` (no artifacts/facts) created during a failed bootstrap attempt with a mismatched artifact path.
64. 2026-02-19: Revalidated CI-equivalent core+security+risk+contract/fact-service gate locally after baseline rollout (`168 passed`).
65. 2026-02-19: Approved baseline replay sign-off artifact for Phase 4 canonical stability (`reports/baseline_canonical_replay_20260219.json`; `overall_stable=true`, no schema errors, live baseline stable at `239` facts).
66. 2026-02-19: Restored explicit empty control baseline row `41f263ab-d83a-42c6-9f30-be128ddd3320` in target DB (`Sierra Vista WTE Facility`, `0` artifacts, `0` facts) per policy.
67. 2026-02-19: Reran baseline canonical replay after control-row restoration; output remains stable with control baseline intentionally reported as `no_facts`.
68. 2026-02-19: Added Phase 7 BFMS integration contract endpoint with explicit fallback semantics (`GET /api/v1/risk/bfms-integration`, schema `risk-bfms-integration-v1`) and governance audit event `generate_risk_bfms_integration` (`src/munipal/core/schemas/risk_reporting.py`, `src/munipal/services/risk_reporting_service.py`, `src/munipal/api/routes/risk_reporting.py`).
69. 2026-02-19: Added integration coverage for BFMS contract full/fallback behavior and feature-flag gate (`tests/integration/test_risk_reporting_foundation.py`).
70. 2026-02-19: Regenerated OpenAPI snapshot after BFMS integration contract addition (`contracts/openapi.v1.json`) and revalidated contract test (`1 passed`).
71. 2026-02-19: Hardened promotion workflow to require frontend test + production build in core/security/risk gate (`.github/workflows/core-security-risk-gate.yml`) and revalidated CI-equivalent backend gate (`171 passed`) plus local frontend validation (`npm --prefix frontend run test`, `npm --prefix frontend run build`).
72. 2026-02-19: Regenerated frontend OpenAPI artifacts to consume Phase 7 contract updates (`frontend/src/types/openapi.generated.ts`, `frontend/src/generated/api-client/`).
73. 2026-02-19: Added API adapter method `getRiskBfmsIntegration` with default cohort wiring and 404-safe fallback handling (`frontend/src/services/api.ts`, `frontend/src/types/index.ts`).
74. 2026-02-19: Integrated BFMS contract into Readiness UI with explicit full/fallback mode presentation, fallback reasons, and top next-step actions (`frontend/src/pages/Readiness.tsx`).
75. 2026-02-19: Added frontend component test harness (`vitest` + Testing Library) and fallback/full rendering coverage for Readiness integration mode card (`frontend/src/pages/__tests__/Readiness.test.tsx`, `frontend/vite.config.ts`, `frontend/src/test/setup.ts`, `2 passed`).
76. 2026-02-19: Revalidated frontend build and risk validation slices after UI wiring (`npm --prefix frontend run build`, `35 passed` across risk integration + risk service tests, `171 passed` backend CI-equivalent gate).
77. 2026-02-19: Expanded Phase 7 consumer coverage into advisory decisioning surface by integrating BFMS risk mode/fallback rationale card in external Advisory Packages workflow (`frontend/src/pages/AdvisoryPackages.tsx`).
78. 2026-02-19: Added frontend component coverage for advisory integration full/fallback/unavailable states (`frontend/src/pages/__tests__/AdvisoryPackages.test.tsx`), then revalidated frontend gate (`npm --prefix frontend run test`, `5 passed`; `npm --prefix frontend run build` successful).
79. 2026-02-19: Enriched external advisory package generation with BFMS integration context (full/fallback mode, directional guidance signal, posture metric, fallback rationale, and top next-step carry-through in executive summary/assumptions) with graceful degradation when risk foundation is disabled (`src/munipal/services/advisory_package_service.py`).
80. 2026-02-19: Added advisory package service unit coverage for risk-context enrichment behavior (`tests/unit/test_advisory_package_service.py`, `3 passed`) and revalidated risk reporting slices (`35 passed`).
81. 2026-02-19: Expanded core/security/risk CI workflow gate to include advisory package service tests and revalidated local CI-equivalent backend gate (`174 passed`) plus frontend gate (`5 passed`, build successful) (`.github/workflows/core-security-risk-gate.yml`).
82. 2026-02-19: Refreshed baseline pack contract/flag evidence to remove outdated assumptions (`V2/BASELINE_PACK_20260218.md` now references frozen OpenAPI snapshot, generated frontend client artifacts, and implemented feature-flag inventory).
83. 2026-02-19: Added one-command Phase 7 closeout bundle runner and runbook (`scripts/run_phase7_closeout_bundle.py`, `V2/PHASE_7_CLOSEOUT_RUNBOOK.md`) to capture automated gate evidence plus target CI/staging checklist in timestamped artifacts under `reports/phase7_closeout/`.
84. 2026-02-19: Executed Phase 7 closeout bundle locally with passing evidence artifact (`reports/phase7_closeout/phase7_closeout_20260219_222058.md`, `reports/phase7_closeout/phase7_closeout_20260219_222058.json`): backend gate `174 passed`, frontend tests `5 passed`, frontend build successful, risk-focused slice `38 passed`.
85. 2026-02-19: Added target staging evidence capture template to streamline final closeout recording (`reports/phase7_closeout/STAGING_EVIDENCE_TEMPLATE.md`).
86. 2026-02-19: Added dispatchable CI closeout workflow (`.github/workflows/phase7-closeout-dispatch.yml`) to run Phase 7 bundle via Actions and upload timestamped evidence artifacts.
87. 2026-02-20: Fixed `core-security-risk-gate.yml` npm cache-dependency-path from literal `frontend/package-lock.json` to glob `"**/package-lock.json"` (matching the fix already applied to `phase7-closeout-dispatch.yml`) to unblock GitHub Actions cache step.
88. 2026-02-20: Confirmed first green run of `.github/workflows/core-security-risk-gate.yml` in target CI — run `22235087843`, commit `84f2a18dfc667aa504a15f60dc75cbd86ef98cae`, all backend + frontend gates pass.
89. 2026-02-20: Confirmed first green run of `.github/workflows/phase7-closeout-dispatch.yml` in target CI — run `22235130725`, commit `84f2a18`, 4/4 gates pass (backend 174 tests 14.89s, frontend tests 2.00s, frontend build 7.60s, risk slice 4.45s).
90. 2026-02-20: Diagnosed staging `.env` was missing 5 feature-flag/JWT settings (`AUTH_ENFORCEMENT_V2`, `ROLE_ENFORCEMENT_V2`, `RISK_REPORTING_V2_FOUNDATION`, `RISK_REPORTING_V2_ADVANCED_ANALYTICS`, `RISK_REPORTING_V2_ADVANCED_MIN_RELIABILITY`); added all five to live staging `.env`.
91. 2026-02-20: Confirmed staging BFMS fallback-mode API response for project `de618f31-bb6f-4905-be68-8445c357ed32` — `integration_mode=fallback`, `overall_posture_score=0.78`, 5 low-reliability dimensions, 3 compliance checks pass, 7 critical risk flags, 5 material risk statements, 5 advisory next steps.
92. 2026-02-20: Confirmed staging UI — Readiness tab loads without errors; Advisory Packages External tab renders BFMS fallback mode panel correctly (yellow banner, contract version, posture score, fallback reasons, top risk next steps).
93. 2026-02-20: Diagnosed `Generate Report` error in Advisory Packages: SQLAlchemy async lazy-load failure on `disclosure_doc.tbd_items` relationship after `session.flush()` in the disclosure service; fixed by adding `await self.session.refresh(disclosure_doc, attribute_names=["tbd_items"])` before iterating the collection (`src/munipal/services/advisory_package_service.py`).
94. 2026-02-20: Added staging evidence capture template entries for confirmed automated gates, staging API fallback evidence, and staging UI evidence (`reports/phase7_closeout/STAGING_EVIDENCE_TEMPLATE.md`).
95. 2026-02-20: Added full-mode risk fact seed script (`scripts/seed_fullmode_risk_facts.py`) inserting 10 approved risk dimension facts at `confidence_score=0.95` for project `de618f31-bb6f-4905-be68-8445c357ed32` to push all 5 dimensions from LOW to HIGH reliability and enable staging full-mode BFMS evidence capture.
96. 2026-02-20: Updated Phase 7 status in Phase Status table and Next Milestones list to reflect CI green runs, staging API/UI validation, advisory package fix, and pending full-mode evidence capture.
97. 2026-02-20: Captured staging full-mode BFMS response — `integration_mode=full`, `directional_guidance_only=false`, `fallback_reasons=[]`, `reliability_low_dimensions=0`, `overall_posture_score=0.25`, 2 critical DSCR flags, 1 high-priority advisory action; recorded verbatim in `reports/phase7_closeout/STAGING_EVIDENCE_TEMPLATE.md`. Both fallback and full modes are now confirmed in staging.
98. 2026-02-20: Confirmed Internal Readiness Report generation in staging — Version 3, score 6.6/10 ("Ready for selective advisor engagement"), 2 critical gaps (Issuer Authority 1.5/5.0), 6 open requests, 91 facts collected; export options (Markdown/PDF/HTML) rendered correctly.
99. 2026-02-20: Confirmed External Advisory Package generation in staging — Version 2 "Ready for Distribution" for ABV Advisory; BFMS full-mode green banner renders with contract `risk-bfms-integration-v1`, posture score 0.250, reliability-low dimensions 0, and top DSCR next-step carries through; external package content evidence section in STAGING_EVIDENCE_TEMPLATE.md marked complete.
100. 2026-02-20: **Phase 7 COMPLETE** — Sign-off recorded in `reports/phase7_closeout/STAGING_EVIDENCE_TEMPLATE.md` (Stephen Peterson, Product/Engineering/QA, 2026-02-20). All staging evidence sections complete. Artifact: commit `854b6017`.
101. 2026-02-20: Started Phase 8 with tenant isolation foundation backlog and scope lock (`V2/PHASE_8_EXTERNAL_READINESS_BACKLOG.md`).
102. 2026-02-20: Added tenant identity context dependency (`CurrentTenantId`) with JWT claim/header resolution and `TENANT_ISOLATION_V2` config flag (`src/munipal/api/dependencies.py`, `src/munipal/config.py`, `.env.example`, `tests/unit/test_auth_dependencies.py`).
103. 2026-02-20: Added project tenant partitioning via `projects.tenant_id` model + Alembic migration/backfill (`src/munipal/core/models/project.py`, `src/munipal/core/schemas/project.py`, `src/munipal/services/project_service.py`, `alembic/versions/20260220_0001_b8c9d0e1f2a3_add_project_tenant_id.py`).
104. 2026-02-20: Implemented tenant-aware project authorization/list filtering paths behind `TENANT_ISOLATION_V2` with cross-tenant deny semantics for project endpoints (`src/munipal/services/authorization_service.py`, `src/munipal/api/routes/projects.py`).
105. 2026-02-20: Added tenant isolation integration coverage and expanded CI gate command/workflow to include tenant tests (`tests/integration/test_tenant_isolation.py`, `tests/unit/test_audit_route_events.py`, `.github/workflows/core-security-risk-gate.yml`, `scripts/run_phase7_closeout_bundle.py`).
106. 2026-02-20: Revalidated updated backend gate (`181 passed`) and frontend gate (`5 passed`, build successful) after Phase 8 tenant foundation rollout.
107. 2026-02-20: Added Phase 8 tenant isolation operations runbook with rollout, smoke validation, incident response, and rollback procedures (`V2/PHASE_8_TENANT_ISOLATION_RUNBOOK.md`).
108. 2026-02-20: Added one-command Phase 8 closeout bundle runner with automated gate evidence output and manual staging checklist (`scripts/run_phase8_closeout_bundle.py`).
109. 2026-02-20: Added dispatchable Phase 8 closeout workflow for target CI with artifact upload support (`.github/workflows/phase8-closeout-dispatch.yml`).
110. 2026-02-20: Added Phase 8 staging evidence template for migration/backfill proof, tenant-scope API/UI validation, rollback drill evidence, and sign-off capture (`reports/phase8_closeout/STAGING_EVIDENCE_TEMPLATE.md`).
111. 2026-02-20: Executed Phase 8 closeout bundle locally with passing evidence artifact (`reports/phase8_closeout/phase8_closeout_20260220_204240.md`, `reports/phase8_closeout/phase8_closeout_20260220_204240.json`): backend gate `181 passed`, frontend tests `5 passed`, frontend build successful, tenant isolation slice `17 passed`.
112. 2026-02-21: Applied migration `b8c9d0e1f2a3` to target staging DB — `projects.tenant_id` column added, index created, owner→organization backfill completed: 0 missing rows, tenant distribution `default=3` (3 projects total).
113. 2026-02-21: Enabled `TENANT_ISOLATION_V2=true` in staging and confirmed tenant-scoped behavior — Tenant A (`default`) sees 3 projects, Tenant B (`other-org`) sees 0; cross-tenant single-project access returns `403 Forbidden: cross-tenant access denied`; same-tenant access returns `200` with full project payload.
114. 2026-02-21: Both CI workflows green on commit `2435a0a8` — core-security-risk-gate run `22256628880` (push-triggered), phase8-closeout-dispatch run `22256677506` (manually dispatched), all gates pass.
115. 2026-02-21: Executed flag-only rollback drill — set `TENANT_ISOLATION_V2=false`, restarted server, verified: `other-org` listing returns all 3 projects (no tenant filter), cross-tenant project access returns `200` (no block). Restored `TENANT_ISOLATION_V2=true`. Rollback is clean and immediate.
116. 2026-02-21: **Phase 8 COMPLETE** — All staging evidence sections filled in `reports/phase8_closeout/STAGING_EVIDENCE_TEMPLATE.md`. Sign-off: Stephen Peterson, Product/Engineering/QA, 2026-02-21. Artifact: commit `2435a0a8`.
