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

## Current Progress (2026-02-25)

- `OPS-1001`: Week 1 telemetry baseline captured and signed in `reports/phase10_postlaunch/WEEKLY_EVIDENCE_TEMPLATE.md`; Closeout-A/C automation now includes `scripts/assess_ops1001_telemetry_trends.py` + `scripts/route_ops1001_telemetry_alerts.py` (7-day trend artifact + routed incident/escalation scaffold) pending production telemetry export ingestion.
- `OPS-1002`: Week 1 second-tenant onboarding rehearsal completed (`acme-corp`) with clean rollback.
- `OPS-1003`: M1 through M5 automation remains operational with latest recommendations stable (`calibration=go`, `cohort=go`, `smoke=go`, `M5 readiness=go`; age-weighting remains `hold`). Strict corpus normalization hardening is now wired: outlier cleanup + normalized document index rebuild (`UNIQUE(source_hash, doc_type)` + provenance tagging) + strict reconciliation gate (`--fail-on-extra-db --fail-on-index-extras --fail-on-type-mismatch`) are included in the Phase 10 bundle. Latest local bundle: `phase10_postlaunch_20260225_164128.{md,json}`; latest local archive: `phase10_postlaunch_20260225_123753_archive.zip`; latest M5 artifact: `ops1003_m5_readiness_20260225_164254.json`; latest CI dispatch evidence: `https://github.com/st3jace/MUNI-PAL/actions/runs/22406633452` (`success`).
- `OPS-1004`: Automated readiness assessor remains `go`; healthcare backfill-only rows are now explicitly provenance-tagged in `document_index` and treated as non-actionable in strict reconciliation while preserving traceability.
- `OPS-1005`: First incident drill completed (`OPS-1005-20260221-01`) and evidence captured in `reports/phase10_postlaunch/INCIDENT_DRILL_TEMPLATE.md`; alerting + drill-readiness automation is now implemented via `ops1001_telemetry_alert_routing_<timestamp>.md/.json` and `ops1005_incident_drill_assessment_<timestamp>.md/.json`, with live-data timeline validation still pending.
