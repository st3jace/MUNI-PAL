# ELA-52 — Healthcare pilot scenario end-to-end walkthrough

Reviewed: local current HEAD with ELA-57 seeded demo data.

Linear issue: ELA-52 — BFMS Launch: Walk Healthcare pilot scenario end-to-end

## Environment

- Frontend: http://127.0.0.1:4121
- Backend: http://127.0.0.1:8000
- Seed script used before walkthrough: scripts/seed_demo_scenarios.py
- Healthcare demo project id: 62150913-a6b1-5e05-9ecb-be635ae35381
- Evidence directory: dogfood-output/ela52-healthcare

## Routes and API probes

All core local routes responded successfully during the walkthrough:

- /tools: 200
- /tools/pilot-navigation: 200
- /dashboard: 200
- /projects: 200
- /health: 200
- /api/v1/sensing/sectors: 200
- /api/v1/sensing/privacy: 200
- /api/v1/projects/?limit=10: 200
- /api/v1/projects/62150913-a6b1-5e05-9ecb-be635ae35381: 200
- /api/v1/readiness/62150913-a6b1-5e05-9ecb-be635ae35381: 200

The browser tool was unavailable in this local Windows/WSL session, so this pass used HTTP probes, backend API evidence, source inspection, and the seeded walkthrough docs rather than interactive click automation.

## Healthcare seeded project evidence

The local BFMS Projects API now returns a concrete Healthcare demo project:

- Name: Launch Demo — Healthcare Hospital Revenue Bond
- Issuer: Demo Regional Health Authority
- Sector: healthcare
- Subsector: healthcare_hospital
- Tenant: launch-demo
- Target bond amount: 42,000,000
- Artifact count: 3
- Fact count: 8
- Approved fact count: 7
- Overall readiness score: 0.48

This is a meaningful improvement over the pre-ELA-57 empty-dashboard state. The dashboard/project-list path can now demonstrate a live Healthcare project instead of only generic empty-state UI.

## Acceptance-criteria assessment

### Public messaging fits Healthcare without WTE/UCS leakage

Partially passes.

Positive evidence:

- Tools hub includes Healthcare-specific readiness copy: Healthcare sub-sector scoring for Hospital, Senior Living, and FQHC.
- Healthcare-focused public content exists in the tools area.
- Pilot Navigation language is advisor-safe and describes qualification/handoff rather than automatic project creation.

Concern:

- The authenticated BFMS readiness output for the Healthcare seeded project still uses generic/legacy UCS/CAB/SLB readiness dimensions and evidence suggestions, including:
  - Project & Technology
  - Revenue & Feedstock
  - CAB Financial Structure
  - Risk, Security & SLB
  - SLB Verification
  - Nameplate Throughput
  - Supply Mechanism
  - Gross Annual Revenue
  - Offtake Status
  - KPI baseline methodology

For a hospital revenue-bond launch walkthrough, these labels create sector leakage from the earlier UCS/WTE/CAB+SLB model. This is the main Healthcare launch blocker found in ELA-52.

### Healthcare lead/pilot qualification path is understandable

Pass with caveat.

Positive evidence:

- /tools/pilot-navigation responds 200.
- Tools hub has a Pilot Navigation card describing lead capture, pilot qualification, BFMS project creation gate, pre-pilot checks, and advisor-safe handoff boundaries.
- ELA-54/55/56 make the path safer: qualified lead gate, privacy consent/export/delete controls, and public/admin route separation.

Caveat:

- This walkthrough did not complete an interactive browser form submission because the browser harness failed in this local session. API and source evidence indicate the path exists, but ELA-52 should not be treated as full click-through/browser validation.

### Healthcare project/dashboard/readiness artifacts show credible sector-specific evidence needs

Fails for readiness evidence taxonomy; passes for demo project identity.

Positive evidence:

- Seeded project identity is clearly Healthcare.
- Artifact/fact counts are visible through the project API.
- The project has approved and pending evidence states.

Launch blocker:

- The readiness engine still evaluates the Healthcare project against non-Healthcare dimensions and evidence labels. The demo scenario says Healthcare, but the readiness gaps still ask for UCS/CAB/SLB-style evidence. That undermines credibility for a Healthcare pilot review.

Recommended fix:

- Add a Healthcare readiness profile or sector-specific mapping for healthcare_hospital projects before using this as an external demo.
- At minimum, map the Healthcare scenario to Healthcare-appropriate dimensions such as issuer authority, obligated group/borrower profile, audited financials, utilization/service-area demand, capital project scope, revenue pledge/security, debt-service coverage, tax-exempt eligibility, disclosure/risk factors, and counsel/advisor document readiness.

### Missing/unknown facts are clearly marked

Pass.

Positive evidence:

- Healthcare walkthrough doc explicitly lists missing evidence paths:
  - bond_counsel.tax_certificate
  - rating.preliminary_indication
  - debt_service.reserve_policy
- Readiness API reports critical and material gaps.
- Readiness API recommendation is Not Yet Viable, which is conservative and launch-safe.
- The seeded scenario intentionally includes one pending Healthcare fact: disclosure.risk-factors.

Concern:

- The readiness API gap labels are not Healthcare-specific enough, as noted above.

### Warm handoff posture is advisor-ready but not advisor-replacing

Pass.

Positive evidence:

- Public Pilot Navigation and walkthrough docs preserve advisor-safe boundaries.
- The language frames BFMS as screening, evidence tracking, and handoff support.
- No observed local route or walkthrough copy claims legal advice, municipal advisory advice, deal approval, pricing, sizing, or issuance instruction.
- Explicit launch boundary preserved: this is not legal advice, not municipal advisory advice, not deal approval, not pricing, not sizing, and not issuance instruction.

### Identify all Healthcare-specific launch blockers

Found one launch blocker and two high-priority follow-ups.

## Findings

### Blocker — Healthcare readiness output leaks UCS/CAB/SLB taxonomy

Severity: launch blocker
Category: Product / Content / Domain-fit

Evidence:

- /api/v1/readiness/62150913-a6b1-5e05-9ecb-be635ae35381 returns overall_score 0.477 and recommendation Not Yet Viable.
- Dimensions and suggestions include Project & Technology, Revenue & Feedstock, CAB Financial Structure, Risk, Security & SLB, and SLB Verification.
- Suggested evidence includes Nameplate Throughput, Supply Mechanism, Gross Annual Revenue, Offtake Status, Accretion Rate, Base DSCR, and KPI baseline methodology.

Expected:

Healthcare hospital revenue-bond readiness should use Healthcare-specific evidence needs and labels.

Actual:

Healthcare project identity is correct, but readiness analysis still reads like the older UCS/WTE/CAB+SLB model.

Recommendation:

Implement a Healthcare-specific readiness profile before an external Healthcare pilot demo. This should become the next Healthcare implementation issue before considering ELA-52 fully launch-ready for external viewing.

### High priority — Dashboard/project shell is operational but not yet a guided Healthcare demo

Severity: high
Category: UX / Launch readiness

Evidence:

- Dashboard and project routes respond 200.
- Healthcare project appears through Projects API with artifact and readiness metrics.
- Dashboard source shows generic Recent Projects cards with project name, issuer, artifact count, and readiness.

Expected:

For a Healthcare pilot walkthrough, the shell should guide the operator toward the Healthcare scenario, evidence review, missing items, readiness explanation, and handoff next step.

Actual:

The shell is operational but generic; the golden walkthrough doc carries most of the pilot guidance.

Recommendation:

After fixing Healthcare readiness taxonomy, add a lightweight demo/pilot banner or launch-review cue for seeded demo projects.

### High priority — Browser-level click-through still needs validation

Severity: high
Category: QA coverage

Evidence:

- Built-in browser navigation failed in this Hermes/Windows setup.
- This review used HTTP/API/source evidence.

Expected:

Healthcare external launch confidence should include browser-level screenshots or DOM extraction from the actual rendered React app.

Actual:

Routes and APIs are healthy, but no visual screenshot/click-through proof was captured in this pass.

Recommendation:

Run a follow-up browser validation pass once the local browser harness or Windows Chrome headless path is available and approved.

## Launch recommendation

Do not use the current Healthcare BFMS readiness screen as an external Healthcare demo yet.

The seeded Healthcare project and public pilot navigation path are now strong enough for internal walkthroughs, but the readiness taxonomy must be Healthcare-specific before a prospect/advisor-facing demo. Otherwise the product will look like a UCS/WTE workflow with a Healthcare label applied on top.

Recommended next implementation issue:

- Add Healthcare-specific readiness dimensions/evidence labels for healthcare_hospital seeded projects, then re-run ELA-52.

ELA-53 for Housing can still proceed as an internal pilot-stage review, but expect similar sector-taxonomy issues unless Housing readiness mapping already exists.
