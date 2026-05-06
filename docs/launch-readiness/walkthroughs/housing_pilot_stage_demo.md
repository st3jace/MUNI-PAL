# Housing pilot-stage demo walkthrough

Scenario: Launch Demo — Affordable Housing Pilot Stage

Purpose: demonstrate a secondary/pilot-stage affordable housing workflow without overstating maturity or launch readiness.

Expected seeded state:

- Sector: Housing
- Subsector: Affordable Multifamily
- Project appears on the dashboard and project list after running scripts/seed_demo_scenarios.py.
- Two synthetic PDF artifacts are attached as demo metadata.
- Approved evidence exists for project identity, location, preliminary project cost, draft issuer inducement timing, unit count, and affordability restrictions.
- Site control remains pending and multiple evidence paths remain missing.

Golden operator path:

1. Open /dashboard and confirm the housing project appears alongside the healthcare primary scenario.
2. Open /projects and select Launch Demo — Affordable Housing Pilot Stage.
3. Review Facts Review to confirm a pilot-stage mix of approved and pending evidence.
4. Open Readiness and treat the result as a gap/punchlist view, not a financing recommendation.
5. Use the missing evidence paths below as the operator punchlist before any external pilot review.

Expected missing evidence paths:

- housing.appraisal
- housing.tax_credit_allocation
- environmental.phase_one
- bond_counsel.inducement_resolution

Launch-safe messaging:

This walkthrough is intentionally pilot-stage. It should show BFMS navigation and evidence tracking, not claim housing product maturity, legal sufficiency, deal approval, pricing, sizing, or issuance instruction.
