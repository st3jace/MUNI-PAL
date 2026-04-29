# Sensing / Lead-Capture to Pilot Funnel

This note clarifies how the public sensing microservice and lead-capture surface feed BFMS sector pilots and operator onboarding.

## Deployment scope

The public deployment should use src/munipal/sensing_app.py, not the full BFMS src/munipal/main.py application. The standalone app includes health checks and the /api/v1/sensing/* router only.

Public sensing routes are lead-generation and self-assessment surfaces:

- /api/v1/sensing/sectors
- /api/v1/sensing/market-intelligence
- /api/v1/sensing/benchmark
- /api/v1/sensing/credit-spreads
- /api/v1/sensing/questionnaire
- /api/v1/sensing/readiness
- /api/v1/sensing/coi-benchmarks
- /api/v1/sensing/coi-deal-benchmarks
- /api/v1/sensing/lead
- /api/v1/sensing/event
- /api/v1/sensing/unsubscribe

Protected sensing-admin routes remain authenticated and are not public marketing tools:

- /api/v1/sensing/leads
- /api/v1/sensing/leads/{lead_id}
- /api/v1/sensing/leads/{lead_id}/funnel
- /api/v1/sensing/leads/{lead_id}/convert-to-project

## Blocked BFMS/admin routes

The standalone sensing deployment must not expose the full BFMS/admin surface. These route families stay in the authenticated BFMS app:

- /api/v1/auth
- /api/v1/playbooks
- /api/v1/projects
- /api/v1/artifacts
- /api/v1/extraction
- /api/v1/facts
- /api/v1/checklist
- /api/v1/readiness
- /api/v1/deliverables
- /api/v1/disclosure
- /api/v1/information-requests
- /api/v1/advisory-packages
- /api/v1/risk
- /api/v1/deal-documents
- /api/v1/templates
- /api/v1/stripe

## Lead -> pilot qualification -> BFMS project creation

The intended handoff is not direct public lead capture to production BFMS project creation. It is a qualified handoff:

1. Lead capture: public tools collect contact, organization, sector, estimated deal context, session events, and selected market/readiness/benchmark snapshots. The lead starts as report_requested.
2. Pilot qualification: Muni-Pal reviews entity fit, sector fit, readiness snapshot, referral/source channel, registered MA coverage, and whether the lead belongs in Healthcare, Housing, or UCS/WTE pilot strategy. Qualified leads advance to qualified; unqualified leads should not create BFMS projects.
3. BFMS project creation: an authenticated BFMS user converts a qualified lead through /api/v1/sensing/leads/{lead_id}/convert-to-project. Conversion carries issuer name, estimated bond amount, state, contact context, owner/tenant, and selected sector playbook into the BFMS project and moves the lead to engaged.
4. Pilot onboarding: the BFMS project enters the pilot onboarding workflow, where pre-pilot gates, sector playbook, evidence workspace, document requests, readiness, and warm handoff are managed.

## Privacy and compliance expectations

The sensing surface is lead-generation-only. It should not imply legal advice, municipal advisory advice, deal approval, pricing recommendation, bond sizing recommendation, or issuance instructions.

Production expectations:

- Consent language explains why contact details and report snapshots are collected.
- PII minimization limits collection to contact, organization, sector, estimated deal context, and selected report snapshots.
- Protected sensing-admin endpoints require authentication.
- Unsubscribe support is required for email drip follow-up.
- Retention, export, and delete policy should be defined before production lead-scale rollout.
- Readiness and benchmark outputs are screening artifacts for advisor/operator review, not approval or advice.

## Follow-up implementation issues

Gaps found during ELA-38 review that should be tracked separately:

- ELA-45: Enforce qualified stage before /api/v1/sensing/leads/{lead_id}/convert-to-project can create a BFMS project.
- ELA-46: Codify lead consent, retention, delete/export, and report-snapshot handling as production privacy controls.
- ELA-47: Decide whether authenticated sensing-admin endpoints should be excluded from the public sensing deployment entirely or remain protected inside the sensing app.
