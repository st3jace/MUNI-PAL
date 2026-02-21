# Muni-Pal V2 Phased Plan

Last updated: 2026-02-21

## Plan Summary

| Phase | Duration | Goal | Exit Criteria |
|---|---:|---|---|
| Phase 0: Architecture Baseline | 1 week | Lock boundaries and contracts | Approved architecture doc, canonical schema v1, API versioning policy, approved baseline pack |
| Phase 1: Security Foundations | 2 weeks | Internal-safe and future external-ready access control | Auth enforced, authz enforced, security tests passing |
| Phase 2: API Contract Stabilization | 2 weeks | Eliminate frontend/backend drift | OpenAPI-driven client in frontend, contract tests passing |
| Phase 3: Test and CI Rehabilitation | 2 weeks | Restore engineering reliability | Green CI for backend/frontend, updated fixtures/tests |
| Phase 4: Ingestion and Extraction Hardening | 3 weeks | Reliable, auditable extraction | Async orchestration active, provenance quality gate met |
| Phase 5: Readiness and Reporting Quality Gates | 2 weeks | Deterministic, explainable outputs | Scoring validation suite green, report quality gates enforced |
| Phase 6: Analytics Engine Hardening | 3 weeks | Reproducible, portable analytics runs | No hardcoded paths, reproducible runs from clean environment |
| Phase 7: Analytics to BFMS Integration | 2 weeks | Safe integration through stable interfaces | BFMS consumes analytics outputs with graceful fallback |
| Phase 8: External Readiness | 2 weeks | Tenant and operational readiness | Tenant isolation, runbooks, staging validation signed off |
| Phase 9: Release Cutover | 2 weeks | Launch-governance closure and external exposure decisioning | Baseline + security sign-offs closed, JWT tenant posture enforced, cutover rehearsal + explicit GO/NO-GO packet |
| Phase 10: Post-Launch Operations | 4 weeks | Operational stability, onboarding readiness, and analytics hardening roadmap | Weekly telemetry evidence captured, tenant onboarding rehearsal completed, post-launch backlog milestones tracked |

## Dependency Rules

1. Phase 1, 2, and 3 must complete before major pipeline refactors in Phase 4.
2. Phase 7 must not start until Phase 6 outputs are stable and versioned.
3. External exposure is blocked until Phase 8 acceptance criteria are complete.
4. Phase 9 release packet sign-off is required before any sustained external launch mode.
5. Phase 10 is a continuous hardening window; no contract-breaking changes without explicit versioning approval.

## Release Gates Per Phase

- Functional gate: core flows still pass (project -> upload -> extract -> facts -> readiness -> report)
- Contract gate: no undocumented API changes
- Data gate: migrations are reversible and validated on staging snapshot
- Ops gate: rollback procedure documented before production release

## Core Flow That Must Never Regress

1. Create project
2. Upload and process artifacts
3. Run extraction and review facts
4. Compute readiness/checklist/gaps
5. Generate internal reports and deliverables

Any release that breaks this flow is blocked.
