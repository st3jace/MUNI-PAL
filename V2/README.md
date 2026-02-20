# Muni-Pal V2 Planning Workspace

Last updated: 2026-02-18

This folder memorializes the V2 execution plan so roadmap, sprint scope, and safety controls stay explicit while the codebase evolves.

## Documents

1. `PHASED_PLAN.md`
- End-to-end phased roadmap (Phase 0 through Phase 8)
- Dependencies and phase gates

2. `PHASE_0_BASELINE_PACK_TEMPLATE.md`
- Template to freeze current known-good behavior before V2 changes
- Includes project selection, output capture, comparison rubric, and sign-off

3. `PHASE_1_SECURITY_BACKLOG.md`
- Detailed Phase 1 two-week backlog
- Ticket-level acceptance criteria and order of operations

4. `NON_REGRESSION_STRATEGY.md`
- Working agreement to avoid breaking currently working functionality
- Baselines, feature flags, contract tests, staged rollout, and rollback

5. `EXECUTION_TRACKER.md`
- Running status board for phases, risks, decisions, and completed milestones

6. `SECURITY_HARDENING_ROLLOUT_CHECKLIST.md`
- SEC-008 release hardening checklist
- Go/no-go gate, phased rollout steps, and rollback runbook

7. `PHASE_4_5_CONFLICT_DEDUP_ADDENDUM.md`
- Phase 4/5 backlog extension for duplicate/conflict handling
- Includes canonicalization strategy and archive review flow

8. `RISK_REPORTING_V2_BACKLOG.md`
- Phase 5/6 backlog for qualitative + quantitative + actionable risk reporting
- Defines confidence-aware scoring and internal/external report contracts

9. `PHASE_5_SPRINT_1_RISK_FOUNDATION.md`
- First Phase 5 two-week execution slice (`RISK-501` to `RISK-503`)
- Scope lock, acceptance criteria, tests, and rollout guardrails

## Operating Rule

No phase is considered complete until its exit criteria are met and documented in `EXECUTION_TRACKER.md`.
