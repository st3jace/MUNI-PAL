# ELA-53 refresh — Housing pilot walkthrough after sector readiness profiles

Issue: ELA-53
Refresh trigger: ELA-92 sector-specific readiness profiles, commit 6adf83f.
Evidence directory: dogfood-output/ela53-housing-refresh

## Scope

This is a fresh walkthrough pass against the current canonical WSL BFMS server and current HEAD after ELA-92. It re-checks the seeded project, platform routes, readiness output, gap labels, and launch-safety boundaries.

Browser screenshots were still not used because the prior local browser automation path is blocked in this Windows/WSL environment. This pass uses live HTTP/API evidence from the current backend and frontend dev servers.

## Route and endpoint health

- Frontend /tools: 200
- Frontend /tools/pilot-navigation: 200
- Frontend /dashboard: 200
- Frontend /projects: 200
- Backend /health: 200
- Projects API: 200
- Readiness API: 200
- Readiness gaps API: 200
- Readiness explanation API: 200

## Project positioning

- Project id: b7d9fdc3-b137-5362-a990-d4aa234f86bf
- Sector path: housing
- Demo positioning: Housing secondary / pilot-stage demo path.
- Overall readiness score: 2.97/10
- Recommendation: Not Yet Viable
- Explanation summary: Project readiness score is 3.0/10 (Not Yet Viable). There are 6 critical gaps that need to be addressed before engaging bond counsel or underwriters.

## Updated readiness dimensions after ELA-92

| Dimension | Score | Current suggestions |
| --- | ---: | --- |
| Issuer & Inducement Readiness | 1.5 | Upload documents containing: Bond counsel inducement resolution |
| Affordable Housing Project Scope | 4.8 | None from current score |
| Affordability & Subsidy Stack | 1.5 | Upload documents containing: Tax credit allocation |
| Housing Finance Readiness | 0.0 | Upload documents containing: Housing appraisal |
| Site Control & Diligence | 0.0 | Upload documents containing: Phase One environmental report, Site control evidence |
| Housing Disclosure & Advisor Readiness | 0.0 | Upload documents containing: Bond counsel inducement resolution |

## Gap and action summary

- Critical gaps: 6
- Material gaps: 0
- Secondary gaps: 0

Priority actions:
- Upload documents for Issuer & Inducement Readiness: Bond counsel inducement resolution
- Upload documents for Affordability & Subsidy Stack: Tax credit allocation
- Focus on critical path documentation before engaging advisors

## Legacy taxonomy re-check

Prospect-visible readiness fields were scanned for the legacy UCS/WTE/CAB/SLB labels called out by the original ELA-52/ELA-53 pass: CAB, SLB, Feedstock/feedstock, Nameplate Throughput, Supply Mechanism, Offtake Status, and KPI baseline.

Result: PASS. No prospect-visible legacy terms were found in names, explanations, summaries, descriptions, suggested evidence, suggestions, impact text, or priority actions.

Internal API object keys such as revenue_feedstock remain for backwards compatibility, but the labels and human-facing text now render sector-specific language.

## Launch-safety boundary

The refreshed walkthrough remains launch-safe. It does not provide legal advice, municipal advisory advice, deal approval, pricing, sizing, issuance instruction, or issuance recommendation. Readiness language is framed as evidence organization and advisor-preparation support.

## Fresh verdict

The Housing walkthrough is materially improved versus the original ELA-53 pass. The previous launch blocker — visible UCS/WTE/CAB/SLB readiness taxonomy — is resolved at the prospect-visible readiness layer. The seeded Housing project now reads as an affordable-housing pilot readiness workflow with conservative maturity signals.

## Go/no-go recommendation

Go for internal pilot-stage walkthroughs and selective controlled discussions, but keep Housing positioned as secondary until browser-level UI validation and Housing-specific copy polish are complete.

## Remaining notes

Housing correctly remains lower maturity than Healthcare. The Not Yet Viable recommendation is acceptable for the pilot-stage story because missing appraisal, tax credit allocation, environmental, and inducement evidence are visible rather than hidden.
