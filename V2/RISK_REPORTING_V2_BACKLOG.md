# Risk Reporting V2 Backlog

Last updated: 2026-02-19

## Objective

Upgrade Muni-Pal risk reporting from gap-only visibility to benchmarked, confidence-aware, decision-grade outputs for internal teams and client-facing packages.

## Scope

In scope:
- Risk benchmark methodology and cohorting
- Confidence-aware risk scoring
- Action generation tied to evidence quality and materiality
- Internal vs external output contract

Out of scope:
- UI design details
- Full market data platform integration

## Design Principles

1. Deterministic where possible, probabilistic where necessary.
2. Every score must include confidence metadata and sample-size context.
3. Internal outputs can expose uncertainty and conflicts; external outputs must be curated and disclosure-safe.
4. Recommendations must map to concrete evidence requests and owners.

## Execution Status

Completed in codebase:
- `RISK-501` through `RISK-507`
- `RISK-508` external advisory brief contract with disclosure-safety checks
- `RISK-509` risk-action to information-request sync (create/refresh/skip resolved)
- `RISK-510` risk governance audit events (generation, overrides, action acceptance)
- `RISK-511` validation/regression suite with corpus drift guards
- `RISK-512` advanced analytics bridge (spectral/wavelet/dynamic ingest) with reliability gates and default-off config
- Phase 7 integration foundation kickoff: versioned BFMS handoff contract `risk-bfms-integration-v1` (`GET /api/v1/risk/bfms-integration`) with explicit `full`/`fallback` mode semantics for consumer-side graceful degradation
- Phase 7 integration expansion: advisory decisioning surfaces (Readiness + Advisory Packages UI) and external package generation now carry BFMS integration mode/fallback context with graceful degradation when risk foundation is disabled

Remaining:
- No remaining Phase 5/6 scope in this backlog. Active work now focuses on Phase 7 closeout evidence promotion to target CI/staging (tracked in `V2/EXECUTION_TRACKER.md`); local closeout bundle evidence is captured under `reports/phase7_closeout/`, and Readiness + Advisory Packages UI plus external package generation now consume `risk-bfms-integration-v1`.

## Backlog (Ordered)

| ID | Phase | Task | Deliverable | Acceptance Criteria | Depends On |
|---|---|---|---|---|---|
| RISK-501 | 5 | Canonical risk data model | Risk dimension model with fields for `exposure`, `mitigants`, `severity`, `evidence_count`, `conflict_count`, `confidence` | Model supports all five core risk dimensions and versioned extensions | Phase 4 canonical facts |
| RISK-502 | 5 | Benchmark cohort framework | Cohort selection logic by sector, deal type, issuer size band, and recency window | Any benchmark output includes cohort metadata and sample counts | RISK-501 |
| RISK-503 | 5 | Confidence and reliability layer | Reliability score from sample size, source quality, and conflict rate | Every benchmark metric carries `reliability_band` (`high/medium/low`) | RISK-502 |
| RISK-504 | 5 | Risk posture scoring engine | Dimension and overall risk posture (`above/at/below corpus`) with explainers | Score is reproducible for same inputs; rationale generated per dimension | RISK-503 |
| RISK-505 | 5 | Quantitative guardrails | Metric checks (e.g., DSCR percentile position, concentration thresholds) with tolerance bands | Rule violations are explicit and link to evidence paths | RISK-504 |
| RISK-506 | 5 | Action synthesis engine | Prioritized action list with `priority`, `owner`, `evidence_required`, `target_date_hint`, `expected_impact` | Actions are deduplicated and traceable to one or more gaps/metrics | RISK-505 |
| RISK-507 | 5 | Internal risk report contract | Internal JSON/MD contract with full diagnostics: gaps, conflicts, uncertainty, benchmark stats | Output consumed by internal readiness/advisory services without manual transformation | RISK-506 |
| RISK-508 | 5 | External advisory risk brief contract | External-safe contract suppressing internal conflict noise while retaining material disclosure content | No internal-only fields leaked; compliance review checklist passes | RISK-507 |
| RISK-509 | 5 | Information request integration | Auto-create/refresh risk-related requests from RISK-506 actions | Requests include why-it-matters and evidence acceptance criteria | RISK-506 |
| RISK-510 | 5 | Audit and governance | Audit events for risk score generation, overrides, and action acceptance | All override decisions include actor, reason, timestamp | SEC-006 |
| RISK-511 | 5 | Validation suite | Statistical and regression tests with known corpora and expected outputs | Stable test fixtures pass in CI; drift alerts on threshold breaches | RISK-504 |
| RISK-512 | 6 | Advanced analytics bridge | Optional ingest of extended risk analytics (spectral/wavelet/dynamic) behind reliability gates | Advanced metrics disabled by default unless reliability gate passes | RISK-503 |

## Data Contract (Draft)

Core fields per risk dimension:
- `dimension_id` (`risk.technology`, etc.)
- `project_status` (`missing`, `partial`, `complete`)
- `gap_severity` (`critical`, `material`, `secondary`)
- `benchmark_position` (`above`, `at`, `below`)
- `benchmark_stats`:
  - `n_issuances`
  - `n_disclosures`
  - `mitigation_rate`
  - `severity_distribution`
- `confidence`:
  - `score` (0-1)
  - `reliability_band`
  - `uncertainty_note`
- `evidence`:
  - `required_items`
  - `provided_items`
  - `missing_items`
- `actions`:
  - `action_id`
  - `priority`
  - `owner`
  - `evidence_required`
  - `expected_impact`

## Internal vs External Output Rules

Internal report includes:
- Full uncertainty notes
- Conflict counts and unresolved conflict references
- Reliability downgrades and sample-size warnings
- Raw benchmark context and methodological caveats

External report includes:
- Curated material risk statements
- Mitigant summary and key assumptions
- Actionable next steps appropriate for advisors/investors
- No operational queue details, no internal conflict diagnostics

## Quality Gates

1. Any metric with low reliability must be clearly labeled and cannot drive a hard blocker without human confirmation.
2. If sample size below configured threshold, output must shift from prescriptive target to directional guidance.
3. Action lists must be bounded and prioritized (top N) with clear ownership.
4. No externally distributed report may include unresolved internal review metadata.

## Initial Milestones

1. Finalize risk model and cohorting rules (`RISK-501`, `RISK-502`).
2. Implement confidence/reliability layer (`RISK-503`).
3. Ship first internal contract with action synthesis (`RISK-507`, `RISK-506`).
4. Add external-safe brief contract and governance checks (`RISK-508`, `RISK-510`).
