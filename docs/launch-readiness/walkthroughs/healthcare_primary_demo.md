# Healthcare primary demo walkthrough

Scenario: Launch Demo — Healthcare Hospital Revenue Bond

Purpose: demonstrate the primary BFMS pilot path for a synthetic nonprofit hospital revenue bond without using sensitive issuer data.

Expected seeded state:

- Sector: Healthcare
- Subsector: Hospital / Health System
- Project appears on the dashboard and project list after running scripts/seed_demo_scenarios.py.
- Three synthetic PDF artifacts are attached as demo metadata.
- Approved evidence exists for project identity, location, governance, capital cost, revenue pledge, financial statements, and market demand.
- At least one pending fact remains visible for counsel/operator review.

Golden operator path:

1. Open /dashboard and confirm the demo healthcare project contributes to total projects, uploaded documents, scored projects, and average readiness.
2. Open /projects and select Launch Demo — Healthcare Hospital Revenue Bond.
3. Review Facts Review for approved and pending evidence.
4. Open Readiness and confirm the score is non-zero but still shows missing evidence.
5. Use the missing evidence paths below as the operator punchlist for the next pilot review.

Expected missing evidence paths:

- bond_counsel.tax_certificate
- rating.preliminary_indication
- debt_service.reserve_policy

Launch-safe messaging:

This walkthrough is screening and workflow evidence only. It is not legal advice, municipal advisory advice, deal approval, pricing, sizing, or issuance instruction.
