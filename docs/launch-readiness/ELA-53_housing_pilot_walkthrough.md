# ELA-53 — Housing pilot scenario end-to-end walkthrough

Reviewed: local current HEAD with ELA-57 seeded demo data.

Linear issue: ELA-53 — BFMS Launch: Walk Housing pilot scenario end-to-end

## Environment

- Frontend: http://127.0.0.1:4121
- Backend: http://127.0.0.1:8000
- Seed script used before walkthrough: scripts/seed_demo_scenarios.py
- Housing demo project id: b7d9fdc3-b137-5362-a990-d4aa234f86bf
- Evidence directory: dogfood-output/ela53-housing

## Routes and API probes

All core local routes responded successfully during the walkthrough:

- /tools: 200
- /tools/pilot-navigation: 200
- /dashboard: 200
- /projects: 200
- /health: 200
- /api/v1/projects/?limit=10: 200
- /api/v1/projects/b7d9fdc3-b137-5362-a990-d4aa234f86bf: 200
- /api/v1/readiness/b7d9fdc3-b137-5362-a990-d4aa234f86bf: 200
- /api/v1/readiness/gaps?project_id=b7d9fdc3-b137-5362-a990-d4aa234f86bf: 200

The browser tool was unavailable in this local Windows/WSL session, so this pass used HTTP probes, backend API evidence, source inspection, and the seeded walkthrough docs rather than interactive click automation.

## Housing seeded project evidence

The local BFMS Projects API returns a concrete Housing pilot-stage demo project:

- Name: Launch Demo — Affordable Housing Pilot Stage
- Issuer: Demo Housing Finance Authority
- Sector: housing
- Subsector: housing_affordable_multifamily
- Tenant: launch-demo
- Target bond amount: 28,500,000
- Artifact count: 2
- Fact count: 7
- Approved fact count: 6
- Overall readiness score: 0.34

This is useful for internal pilot-stage navigation because it intentionally presents a lower-maturity scenario than the Healthcare primary demo.

## Acceptance-criteria assessment

### Public messaging and platform behavior support Housing as pilot-stage without overstating maturity

Pass for seeded project posture; partial pass for platform messaging.

Positive evidence:

- The seeded project is explicitly named Affordable Housing Pilot Stage.
- The walkthrough doc frames Housing as pilot-stage and explicitly warns not to claim product maturity, legal sufficiency, deal approval, pricing, sizing, or issuance instruction.
- Readiness score is low at 0.336, which correctly avoids overstating maturity.
- The readiness recommendation is conservative and does not imply approval.

Concern:

- The public tools hub remains primarily Healthcare-oriented and does not yet make Housing visible as a secondary pilot-stage path.

### Housing playbook/artifact expectations are visible and do not inherit Healthcare or WTE-only assumptions

Fails for readiness taxonomy; passes for seeded artifact/project identity.

Positive evidence:

- The seeded Housing project identity is sector-specific.
- The scenario includes Housing-relevant seeded evidence such as affordable units, affordability restrictions, and site-control status.
- The walkthrough doc lists Housing-specific missing paths:
  - housing.appraisal
  - housing.tax_credit_allocation
  - environmental.phase_one
  - bond_counsel.inducement_resolution

Launch blocker:

- The BFMS readiness output still uses legacy UCS/CAB/SLB labels for the Housing project, including:
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

Those expectations are not Housing-specific and would undermine a Housing pilot walkthrough if shown to a prospect or advisor.

### Housing-specific readiness gaps are understandable

Fails in the live readiness API; passes in the walkthrough doc.

Positive evidence:

- The walkthrough doc clearly identifies Housing-specific gaps.
- The seeded project has pilot-stage maturity cues and pending evidence.

Concern:

- Live readiness gap API still prioritizes non-Housing labels such as Tax Status, Technology Type, Nameplate Throughput, and critical/material evidence for UCS/CAB/SLB-style dimensions.

Recommendation:

Add a Housing readiness profile for housing_affordable_multifamily projects with dimensions such as issuer/borrower authority, affordability restrictions, site control, environmental diligence, appraisal/market study, tax credit/subsidy allocation, construction/permanent financing, debt service coverage, operating pro forma, and counsel/advisor documentation.

### Missing pilot maturity is clearly framed rather than hidden

Pass.

Positive evidence:

- Housing score is 0.336, lower than the Healthcare score, which matches its secondary/pilot-stage posture.
- Seeded data intentionally leaves site control pending.
- Walkthrough doc explicitly says the scenario is pilot-stage and should be treated as a gap/punchlist view, not a financing recommendation.
- Explicit launch boundary preserved: this is not legal advice, not municipal advisory advice, not deal approval, not pricing, not sizing, and not issuance instruction.

### Identify all Housing-specific launch blockers

Found one launch blocker and two high-priority follow-ups.

## Findings

### Blocker — Housing readiness output inherits UCS/CAB/SLB taxonomy

Severity: launch blocker
Category: Product / Content / Domain-fit

Evidence:

- /api/v1/readiness/b7d9fdc3-b137-5362-a990-d4aa234f86bf returns overall_score 0.336.
- Dimensions and suggestions include Project & Technology, Revenue & Feedstock, CAB Financial Structure, Risk/Security/SLB, and SLB Verification.
- Suggested evidence includes Nameplate Throughput, Supply Mechanism, Gross Annual Revenue, Offtake Status, Accretion Rate, Base DSCR, and KPI baseline methodology.

Expected:

Affordable housing pilot-stage readiness should show Housing-specific evidence expectations and maturity gates.

Actual:

Housing project identity is correct, but live readiness analysis still reads like the older UCS/WTE/CAB+SLB model.

Recommendation:

Implement a Housing-specific readiness profile before any external Housing demo. If Housing remains secondary, this can be less comprehensive than Healthcare, but it must not show WTE/UCS-only evidence labels.

### High priority — Public tools hub does not yet surface Housing as a supported secondary path

Severity: high
Category: UX / Launch readiness

Evidence:

- Tools hub copy is strongly Healthcare-oriented.
- Pilot Navigation supports a generic path but does not make the Housing secondary path obvious.

Expected:

Housing should be visible as secondary/pilot-stage, not hidden or implied by generic BFMS language.

Actual:

The Housing scenario is available in seeded BFMS data but not yet discoverable from public tools messaging.

Recommendation:

After sector-readiness profiles exist, add public copy that says Healthcare is primary and Housing is pilot-stage/secondary, without dropping UCS/WTE from supported/control status.

### High priority — Browser-level click-through still needs validation

Severity: high
Category: QA coverage

Evidence:

- Built-in browser navigation failed in this Hermes/Windows setup.
- This review used HTTP/API/source evidence.

Expected:

Housing pilot launch confidence should include rendered browser screenshots or DOM extraction from the actual React app.

Actual:

Routes and APIs are healthy, but no visual screenshot/click-through proof was captured in this pass.

Recommendation:

Run a follow-up browser validation pass once the local browser harness or Windows Chrome headless path is available and approved.

## Launch recommendation

Use the current Housing scenario for internal pilot-stage walkthrough only.

The seeded project and walkthrough doc correctly frame Housing as secondary/pilot-stage, but the live readiness taxonomy is not Housing-specific. External Housing demo readiness requires a sector profile or at least a Housing-specific gap/label mapping before prospects or advisors see the readiness screen.

Recommended next implementation issue:

- Add sector-specific readiness profiles for Healthcare and Housing, with Healthcare first and Housing second, then re-run ELA-52 and ELA-53.
