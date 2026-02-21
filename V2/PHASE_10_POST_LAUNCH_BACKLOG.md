# Phase 10 Post-Launch Operations Backlog

Phase window: 4 weeks

## Objective

Stabilize external launch operations with production telemetry discipline, tenant onboarding confidence, and analytics roadmap hardening.

## Scope Lock

In scope:
- Post-launch monitoring and alert tuning
- Multi-tenant onboarding rehearsal and evidence
- BFMS analytics hardening plan from foundation to production-grade scoring
- Sector expansion readiness for healthcare corpus intake

Out of scope:
- Breaking API contract changes without versioning
- Unbounded model/schema redesign
- New UI redesign unrelated to launch operations

## Backlog (Ordered)

| ID | Task | Deliverable | Acceptance Criteria | Depends On |
|---|---|---|---|---|
| OPS-1001 | Launch telemetry baseline | 7-day dashboard + alert threshold report for 401/403/cross-tenant-denied | Alert thresholds documented and tuned with observed data; no blind spots on authz failures | Phase 9 complete |
| OPS-1002 | Second-tenant onboarding rehearsal | Tenant onboarding runbook execution evidence on non-default tenant | End-to-end tenant provisioning + access validation succeeds with rollback notes | OPS-1001 |
| OPS-1003 | BFMS production-grade scoring plan | Roadmap addendum for reliability, calibration, and governance controls | Plan approved with milestones, data needs, and validation strategy | OPS-1001 |
| OPS-1004 | Healthcare corpus readiness | Intake assessment for EMMA healthcare corpus with quality and compliance checks | Go/no-go assessment recorded with remediation list (if needed) | OPS-1003 |
| OPS-1005 | Post-launch incident drill | Simulated auth/tenant incident timeline with detection and recovery evidence | Detection-to-recovery flow validated with timestamps and owner handoffs | OPS-1002 |

## Definition of Done (Phase 10)

1. Production monitoring thresholds are calibrated from real traffic.
2. Multi-tenant onboarding is rehearsed and documented.
3. BFMS analytics hardening plan is approved and sequenced.
4. Healthcare corpus expansion readiness is explicitly assessed.
5. Incident response drill evidence is captured and reviewed.

## Current Progress (2026-02-21)

- `OPS-1001`: Week 1 telemetry baseline captured and signed in `reports/phase10_postlaunch/WEEKLY_EVIDENCE_TEMPLATE.md`.
- `OPS-1002`: Week 1 second-tenant onboarding rehearsal completed (`acme-corp`) with clean rollback.
- `OPS-1003`: Plan artifact drafted at `V2/OPS_1003_BFMS_PRODUCTION_SCORING_PLAN.md` (execution pending).
- `OPS-1004`: Automated readiness assessor added (`scripts/assess_healthcare_corpus_readiness.py`) and baseline report generated (`recommendation=go`).
- `OPS-1005`: Incident drill template prepared at `reports/phase10_postlaunch/INCIDENT_DRILL_TEMPLATE.md` (drill execution pending).
