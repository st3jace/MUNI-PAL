
## docs/launch-readiness/ELA-51_dashboard_platform_landing_review.md
# ELA-51 — Local dashboard platform landing review
- Frontend dashboard: http://localhost:4121/dashboard
## Executive summary
The local dashboard loads in the current launch setup and the backend/frontend dev servers are reachable. The dashboard is operational as a BFMS shell, but it is not yet a strong launch landing experience: with the current empty local database it renders generic project metrics and an empty-project
No immediate route-load blocker was found for /dashboard, but the page should not be treated as launch-demo ready until seeded Healthcare/Housing walkthrough data exists and the landing state is made more pilot-aware.
## Evidence
- /dashboard: 200
- frontend/src/pages/Dashboard.tsx
Browser-tool note: the built-in browser session failed in this WSL/Windows environment with WinError 193, so this pass used local HTTP probes and source-level inspection rather than interactive browser screenshots.
## Findings
### Launch blocker: no seeded local projects for dashboard review
The current local Projects API returns an empty project list. As a result, /dashboard can only demonstrate:
This confirms route reliability, but it does not validate the actual BFMS operator value proposition. It also makes Healthcare/Housing walkthrough issues dependent on seed data before they can be meaningfully reviewed.
Recommendation: handle this in the next batch via ELA-57 before using ELA-52/53 as product-readiness evidence.
### Product clarity blocker: dashboard does not explain pilot status or launch path
The dashboard headline is generic:
- Dashboard
Recommendation: add a launch/pilot-aware dashboard panel in a follow-up implementation issue after seed data exists. It should summarize Healthcare primary, Housing pilot-stage, UCS/WTE supported/control, and link to the next operator action.
### UX gap: empty state sends users to generic project creation, not a guided pilot path
The empty dashboard CTA links to /projects with text Create Project. The Projects page supports Healthcare, Affordable Housing, and Waste-to-Energy sectors, which is good. However, from the dashboard alone there is no distinction between ad hoc project creation and the qualified sensing-to-pilot pat
Recommendation: after ELA-57 seed data, provide a guided empty/demo state such as:
- Review seeded Healthcare pilot
- Review Housing pilot-stage scenario
### Public vs authenticated surface separation is mostly clear
- Dashboard
Recommendation: add short labels/copy in a later polish pass, not a blocker.
### Auth/dev-mode caveat should remain a separate security pass
Severity: High as platform security risk, but outside ELA-51 dashboard landing scope.
Recommendation: create or prioritize a full BFMS auth hardening/security pass before pilot/commercial launch.
## Launch blocker vs polish recommendations
### Launch/demo blockers
1. Seeded local dashboard data is missing. ELA-57 should create credible Healthcare/Housing demo projects before ELA-52/53 walkthroughs.
2. Dashboard landing does not yet communicate pilot status or next actions; this becomes more important once seed data is available.
### High-priority follow-up
1. Add a dashboard launch/pilot status panel after ELA-57.
2. Add an explicit internal/full-BFMS label near the dashboard/shell to distinguish it from public sensing.
### Non-blocking polish
2. Add links from dashboard to Pilot Navigation and seeded scenario walkthroughs.
3. Add error handling on the dashboard analogous to ProjectList.tsx so API failures do not silently collapse into an empty/partial Recent Projects card.
## Recommendation for next batch order
Reason: Healthcare and Housing walkthroughs will be low-signal while the dashboard has zero local projects. ELA-57 should seed credible scenarios and golden walkthrough notes so ELA-52/53 can test actual product behavior rather than empty states.

## docs/launch-readiness/ELA-52_healthcare_pilot_walkthrough.md
# ELA-52 — Healthcare pilot scenario end-to-end walkthrough
Linear issue: ELA-52 — BFMS Launch: Walk Healthcare pilot scenario end-to-end
## Environment
- Healthcare demo project id: 62150913-a6b1-5e05-9ecb-be635ae35381
- Evidence directory: dogfood-output/ela52-healthcare
## Routes and API probes
- /dashboard: 200
The browser tool was unavailable in this local Windows/WSL session, so this pass used HTTP probes, backend API evidence, source inspection, and the seeded walkthrough docs rather than interactive click automation.
## Healthcare seeded project evidence
The local BFMS Projects API now returns a concrete Healthcare demo project:
- Name: Launch Demo — Healthcare Hospital Revenue Bond
- Sector: healthcare
- Subsector: healthcare_hospital
This is a meaningful improvement over the pre-ELA-57 empty-dashboard state. The dashboard/project-list path can now demonstrate a live Healthcare project instead of only generic empty-state UI.
## Acceptance-criteria assessment
### Public messaging fits Healthcare without WTE/UCS leakage
Partially passes.
- Tools hub includes Healthcare-specific readiness copy: Healthcare sub-sector scoring for Hospital, Senior Living, and FQHC.
- Healthcare-focused public content exists in the tools area.
- The authenticated BFMS readiness output for the Healthcare seeded project still uses generic/legacy UCS/CAB/SLB readiness dimensions and evidence suggestions, including:
For a hospital revenue-bond launch walkthrough, these labels create sector leakage from the earlier UCS/WTE/CAB+SLB model. This is the main Healthcare launch blocker found in ELA-52.
### Healthcare lead/pilot qualification path is understandable
Pass with caveat.
- This walkthrough did not complete an interactive browser form submission because the browser harness failed in this local session. API and source evidence indicate the path exists, but ELA-52 should not be treated as full click-through/browser validation.
### Healthcare project/dashboard/readiness artifacts show credible sector-specific evidence needs
Fails for readiness evidence taxonomy; passes for demo project identity.
- Seeded project identity is clearly Healthcare.
Launch blocker:
- The readiness engine still evaluates the Healthcare project against non-Healthcare dimensions and evidence labels. The demo scenario says Healthcare, but the readiness gaps still ask for UCS/CAB/SLB-style evidence. That undermines credibility for a Healthcare pilot review.
- Add a Healthcare readiness profile or sector-specific mapping for healthcare_hospital projects before using this as an external demo.
- At minimum, map the Healthcare scenario to Healthcare-appropriate dimensions such as issuer authority, obligated group/borrower profile, audited financials, utilization/service-area demand, capital project scope, revenue pledge/security, debt-service coverage, tax-exempt eligibility, disclosure/ri
### Missing/unknown facts are clearly marked
Pass.
- Healthcare walkthrough doc explicitly lists missing evidence paths:
- Readiness API recommendation is Not Yet Viable, which is conservative and launch-safe.
- The seeded scenario intentionally includes one pending Healthcare fact: disclosure.risk-factors.
- The readiness API gap labels are not Healthcare-specific enough, as noted above.
### Warm handoff posture is advisor-ready but not advisor-replacing
Pass.
- No observed local route or walkthrough copy claims legal advice, municipal advisory advice, deal approval, pricing, sizing, or issuance instruction.
- Explicit launch boundary preserved: this is not legal advice, not municipal advisory advice, not deal approval, not pricing, not sizing, and not issuance instruction.
### Identify all Healthcare-specific launch blockers
Found one launch blocker and two high-priority follow-ups.
## Findings
### Blocker — Healthcare readiness output leaks UCS/CAB/SLB taxonomy
Severity: launch blocker
- /api/v1/readiness/62150913-a6b1-5e05-9ecb-be635ae35381 returns overall_score 0.477 and recommendation Not Yet Viable.
Healthcare hospital revenue-bond readiness should use Healthcare-specific evidence needs and labels.
Healthcare project identity is correct, but readiness analysis still reads like the older UCS/WTE/CAB+SLB model.
Recommendation:
Implement a Healthcare-specific readiness profile before an external Healthcare pilot demo. This should become the next Healthcare implementation issue before considering ELA-52 fully launch-ready for external viewing.
### High priority — Dashboard/project shell is operational but not yet a guided Healthcare demo
- Dashboard and project routes respond 200.
- Healthcare project appears through Projects API with artifact and readiness metrics.
- Dashboard source shows generic Recent Projects cards with project name, issuer, artifact count, and readiness.
For a Healthcare pilot walkthrough, the shell should guide the operator toward the Healthcare scenario, evidence review, missing items, readiness explanation, and handoff next step.
Recommendation:
After fixing Healthcare readiness taxonomy, add a lightweight demo/pilot banner or launch-review cue for seeded demo projects.
### High priority — Browser-level click-through still needs validation
- Built-in browser navigation failed in this Hermes/Windows setup.
Healthcare external launch confidence should include browser-level screenshots or DOM extraction from the actual rendered React app.
Routes and APIs are healthy, but no visual screenshot/click-through proof was captured in this pass.
Recommendation:
Run a follow-up browser validation pass once the local browser harness or Windows Chrome headless path is available and approved.
## Launch recommendation
Do not use the current Healthcare BFMS readiness screen as an external Healthcare demo yet.
The seeded Healthcare project and public pilot navigation path are now strong enough for internal walkthroughs, but the readiness taxonomy must be Healthcare-specific before a prospect/advisor-facing demo. Otherwise the product will look like a UCS/WTE workflow with a Healthcare label applied on top
- Add Healthcare-specific readiness dimensions/evidence labels for healthcare_hospital seeded projects, then re-run ELA-52.
ELA-53 for Housing can still proceed as an internal pilot-stage review, but expect similar sector-taxonomy issues unless Housing readiness mapping already exists.

## docs/launch-readiness/ELA-52_healthcare_pilot_walkthrough_refresh_after_ELA-92.md
# ELA-52 refresh — Healthcare pilot walkthrough after sector readiness profiles
Evidence directory: dogfood-output/ela52-healthcare-refresh
## Scope
This is a fresh walkthrough pass against the current canonical WSL BFMS server and current HEAD after ELA-92. It re-checks the seeded project, platform routes, readiness output, gap labels, and launch-safety boundaries.
Browser screenshots were still not used because the prior local browser automation path is blocked in this Windows/WSL environment. This pass uses live HTTP/API evidence from the current backend and frontend dev servers.
## Route and endpoint health
- Frontend /dashboard: 200
## Project positioning
- Sector path: healthcare
- Demo positioning: Healthcare primary demo path.
- Recommendation: Structurally Viable
## Updated readiness dimensions after ELA-92
| Hospital / Healthcare Project Scope | 4.8 | None from current score |
| Healthcare Risk & Disclosure | 0.0 | Upload documents containing: Healthcare disclosure risk factors |
## Gap and action summary
## Legacy taxonomy re-check
Prospect-visible readiness fields were scanned for the legacy UCS/WTE/CAB/SLB labels called out by the original ELA-52/ELA-53 pass: CAB, SLB, Feedstock/feedstock, Nameplate Throughput, Supply Mechanism, Offtake Status, and KPI baseline.
Result: PASS. No prospect-visible legacy terms were found in names, explanations, summaries, descriptions, suggested evidence, suggestions, impact text, or priority actions.
## Launch-safety boundary
The refreshed walkthrough remains launch-safe. It does not provide legal advice, municipal advisory advice, deal approval, pricing, sizing, issuance instruction, or issuance recommendation. Readiness language is framed as evidence organization and advisor-preparation support.
## Fresh verdict
The Healthcare walkthrough is materially improved versus the original ELA-52 pass. The previous launch blocker — visible UCS/WTE/CAB/SLB readiness taxonomy — is resolved at the prospect-visible readiness layer. The seeded Healthcare project now reads as a Healthcare revenue-bond readiness workflow r
## Go/no-go recommendation
## Remaining notes
Healthcare remains the primary launch path. The next refinement is not taxonomy repair; it is UI/browser validation and any copy polish surfaced by that click-through.

## docs/launch-readiness/ELA-53_housing_pilot_walkthrough.md
# ELA-53 — Housing pilot scenario end-to-end walkthrough
Linear issue: ELA-53 — BFMS Launch: Walk Housing pilot scenario end-to-end
## Environment
- Housing demo project id: b7d9fdc3-b137-5362-a990-d4aa234f86bf
- Evidence directory: dogfood-output/ela53-housing
## Routes and API probes
- /dashboard: 200
The browser tool was unavailable in this local Windows/WSL session, so this pass used HTTP probes, backend API evidence, source inspection, and the seeded walkthrough docs rather than interactive click automation.
## Housing seeded project evidence
The local BFMS Projects API returns a concrete Housing pilot-stage demo project:
- Name: Launch Demo — Affordable Housing Pilot Stage
- Issuer: Demo Housing Finance Authority
- Sector: housing
- Subsector: housing_affordable_multifamily
This is useful for internal pilot-stage navigation because it intentionally presents a lower-maturity scenario than the Healthcare primary demo.
## Acceptance-criteria assessment
### Public messaging and platform behavior support Housing as pilot-stage without overstating maturity
Pass for seeded project posture; partial pass for platform messaging.
- The seeded project is explicitly named Affordable Housing Pilot Stage.
- The walkthrough doc frames Housing as pilot-stage and explicitly warns not to claim product maturity, legal sufficiency, deal approval, pricing, sizing, or issuance instruction.
- The readiness recommendation is conservative and does not imply approval.
- The public tools hub remains primarily Healthcare-oriented and does not yet make Housing visible as a secondary pilot-stage path.
### Housing playbook/artifact expectations are visible and do not inherit Healthcare or WTE-only assumptions
Fails for readiness taxonomy; passes for seeded artifact/project identity.
- The seeded Housing project identity is sector-specific.
- The scenario includes Housing-relevant seeded evidence such as affordable units, affordability restrictions, and site-control status.
- The walkthrough doc lists Housing-specific missing paths:
  - housing.appraisal
  - housing.tax_credit_allocation
Launch blocker:
- The BFMS readiness output still uses legacy UCS/CAB/SLB labels for the Housing project, including:
Those expectations are not Housing-specific and would undermine a Housing pilot walkthrough if shown to a prospect or advisor.
### Housing-specific readiness gaps are understandable
Fails in the live readiness API; passes in the walkthrough doc.
- The walkthrough doc clearly identifies Housing-specific gaps.
- Live readiness gap API still prioritizes non-Housing labels such as Tax Status, Technology Type, Nameplate Throughput, and critical/material evidence for UCS/CAB/SLB-style dimensions.
Recommendation:
Add a Housing readiness profile for housing_affordable_multifamily projects with dimensions such as issuer/borrower authority, affordability restrictions, site control, environmental diligence, appraisal/market study, tax credit/subsidy allocation, construction/permanent financing, debt service cove
### Missing pilot maturity is clearly framed rather than hidden
Pass.
- Housing score is 0.336, lower than the Healthcare score, which matches its secondary/pilot-stage posture.
- Walkthrough doc explicitly says the scenario is pilot-stage and should be treated as a gap/punchlist view, not a financing recommendation.
- Explicit launch boundary preserved: this is not legal advice, not municipal advisory advice, not deal approval, not pricing, not sizing, and not issuance instruction.
### Identify all Housing-specific launch blockers
Found one launch blocker and two high-priority follow-ups.
## Findings
### Blocker — Housing readiness output inherits UCS/CAB/SLB taxonomy
Severity: launch blocker
Affordable housing pilot-stage readiness should show Housing-specific evidence expectations and maturity gates.
Housing project identity is correct, but live readiness analysis still reads like the older UCS/WTE/CAB+SLB model.
Recommendation:
Implement a Housing-specific readiness profile before any external Housing demo. If Housing remains secondary, this can be less comprehensive than Healthcare, but it must not show WTE/UCS-only evidence labels.
### High priority — Public tools hub does not yet surface Housing as a supported secondary path
- Tools hub copy is strongly Healthcare-oriented.
- Pilot Navigation supports a generic path but does not make the Housing secondary path obvious.
Housing should be visible as secondary/pilot-stage, not hidden or implied by generic BFMS language.
The Housing scenario is available in seeded BFMS data but not yet discoverable from public tools messaging.
Recommendation:
After sector-readiness profiles exist, add public copy that says Healthcare is primary and Housing is pilot-stage/secondary, without dropping UCS/WTE from supported/control status.
### High priority — Browser-level click-through still needs validation
- Built-in browser navigation failed in this Hermes/Windows setup.
Housing pilot launch confidence should include rendered browser screenshots or DOM extraction from the actual React app.
Routes and APIs are healthy, but no visual screenshot/click-through proof was captured in this pass.
Recommendation:
Run a follow-up browser validation pass once the local browser harness or Windows Chrome headless path is available and approved.
## Launch recommendation
Use the current Housing scenario for internal pilot-stage walkthrough only.
The seeded project and walkthrough doc correctly frame Housing as secondary/pilot-stage, but the live readiness taxonomy is not Housing-specific. External Housing demo readiness requires a sector profile or at least a Housing-specific gap/label mapping before prospects or advisors see the readiness
- Add sector-specific readiness profiles for Healthcare and Housing, with Healthcare first and Housing second, then re-run ELA-52 and ELA-53.

## docs/launch-readiness/ELA-53_housing_pilot_walkthrough_refresh_after_ELA-92.md
# ELA-53 refresh — Housing pilot walkthrough after sector readiness profiles
Evidence directory: dogfood-output/ela53-housing-refresh
## Scope
This is a fresh walkthrough pass against the current canonical WSL BFMS server and current HEAD after ELA-92. It re-checks the seeded project, platform routes, readiness output, gap labels, and launch-safety boundaries.
Browser screenshots were still not used because the prior local browser automation path is blocked in this Windows/WSL environment. This pass uses live HTTP/API evidence from the current backend and frontend dev servers.
## Route and endpoint health
- Frontend /dashboard: 200
## Project positioning
- Sector path: housing
- Demo positioning: Housing secondary / pilot-stage demo path.
- Recommendation: Not Yet Viable
## Updated readiness dimensions after ELA-92
| Affordable Housing Project Scope | 4.8 | None from current score |
| Housing Finance Readiness | 0.0 | Upload documents containing: Housing appraisal |
| Housing Disclosure & Advisor Readiness | 0.0 | Upload documents containing: Bond counsel inducement resolution |
## Gap and action summary
## Legacy taxonomy re-check
Prospect-visible readiness fields were scanned for the legacy UCS/WTE/CAB/SLB labels called out by the original ELA-52/ELA-53 pass: CAB, SLB, Feedstock/feedstock, Nameplate Throughput, Supply Mechanism, Offtake Status, and KPI baseline.
Result: PASS. No prospect-visible legacy terms were found in names, explanations, summaries, descriptions, suggested evidence, suggestions, impact text, or priority actions.
## Launch-safety boundary
The refreshed walkthrough remains launch-safe. It does not provide legal advice, municipal advisory advice, deal approval, pricing, sizing, issuance instruction, or issuance recommendation. Readiness language is framed as evidence organization and advisor-preparation support.
## Fresh verdict
The Housing walkthrough is materially improved versus the original ELA-53 pass. The previous launch blocker — visible UCS/WTE/CAB/SLB readiness taxonomy — is resolved at the prospect-visible readiness layer. The seeded Housing project now reads as an affordable-housing pilot readiness workflow with
## Go/no-go recommendation
Go for internal pilot-stage walkthroughs and selective controlled discussions, but keep Housing positioned as secondary until browser-level UI validation and Housing-specific copy polish are complete.
## Remaining notes
Housing correctly remains lower maturity than Healthcare. The Not Yet Viable recommendation is acceptable for the pilot-stage story because missing appraisal, tax credit allocation, environmental, and inducement evidence are visible rather than hidden.

## docs/launch-readiness/ELA-59-advisor-compliance-language-qa.md
# ELA-59 Advisor-ready Handoff and Compliance Language Live QA
- Deployed public site: https://muni-pal.io/ and https://muni-pal.io/pricing, captured by HTTP and Windows Chrome screenshot fallback.
- Browser-tool status: built-in browser failed with WinError 193, so evidence used HTTP probes plus Windows Chrome screenshots.
## Linear acceptance criteria
- No deal approval, pricing recommendation, issuance recommendation, bond sizing recommendation, legal opinion, MA advice, or closing instruction language appears.
## Evidence captured
| https://muni-pal.io/pricing | 200 | https://muni-pal.io/pricing | static HTML captured; SPA screenshot captured separately |
- dogfood-output/ela59/http/muni-pal.io_pricing.html
- dogfood-output/ela59/dom/muni-pal.io_pricing.txt
- dogfood-output/ela59/screenshots/pricing.png
## Findings
### 1. Deployed public site still contains stale high-risk cost/pricing framing
Status: launch blocker until redeploy from patched source or equivalent production copy update.
- dogfood-output/ela59/http/muni-pal.io_pricing.html has the same static content.
Why it matters: TIC estimates and what it costs are too close to pricing/cost-of-capital advice for a launch page unless surrounded by stronger registered-advisor and non-pricing boundaries. This is production evidence, not current-HEAD evidence.
Source action taken: reframed cost/pricing language to cost context before registered advisor review; reframed pressure-test advisor language to prepare better questions for the registered advisor and deal team; reframed COI optimization and pre-issuance support as readiness support.
### 2. Current readiness/advisory package copy implied execution or market-readiness too strongly
Status: patched in current source.
- Risk outputs are stable for advisory decisioning -> registered advisor review support with explicit non-approval/non-sizing/non-pricing/non-issuance boundary
### 3. Existing handoff/pilot disclaimers are generally aligned
Status: pass with false-positive audit hits.
The post-patch phrase scan still finds phrases like deal approval, pricing recommendation, and municipal advisory advice in files that explicitly disclaim those acts. Those are desired boundary statements, not unsafe recommendations.
## Current source posture after patches
- Healthcare: pass for current source, subject to redeploy before public launch.
- Housing: no new Housing-specific unsafe launch copy was identified in this pass, but the public deployed site remains Healthcare-centric. Housing should remain invite-only/direct-pilot unless a separate public Housing page is reviewed.
- Warm Handoff / advisory package: pass for current source after copy changes and guardrail tests.
- Readiness: pass for current source after high-score label and rationale changes.
- Public deployed site/pricing: fail until stale deployed TIC/cost wording is replaced by patched source copy or a manual production edit.
## Files changed for launch-safe copy
- frontend/src/pages/tools/HealthcareCFOLanding.tsx
- frontend/src/pages/tools/HealthcareMIRContent.tsx
- frontend/src/pages/tools/HealthcareReadiness.tsx
- frontend/src/pages/tools/design-variants/variant-a/HealthcareCFOLanding.tsx
- frontend/src/pages/tools/design-variants/variant-b/HealthcareCFOLanding.tsx
- frontend/src/pages/tools/design-variants/variant-c/HealthcareCFOLanding.tsx
## Verification performed so far
Result: 7 passed
Remaining current-source hits are disclaimer/guardrail false positives. Remaining deployed-site hits are blocker evidence for stale production copy.
## Launch verdict
Current source can proceed toward advisor/compliance launch readiness after full verification/build. Deployed public site is not launch-safe yet because it still serves stale TIC/cost wording. Redeploy from this patched source, then re-run ELA-59 public-site screenshot/HTTP evidence before declaring

## docs/launch-readiness/ELA49_PUBLIC_SITE_PRICING_DOGFOOD.md
# ELA-49 Public Site and Pricing Dogfood Report
Issue: ELA-49 — BFMS Launch: Dogfood public site and pricing pages
Scope: https://muni-pal.io/ and https://muni-pal.io/pricing
Launch lens: Healthcare and Housing pilot readiness, public-message clarity, pricing/Stripe expectation-setting, advisory/compliance boundary language.
## Method
The built-in browser stack failed in this Hermes/Windows session with a Win32 browser launch error, and browser-harness could not attach because Chrome remote debugging was not enabled. Per the dogfood fallback workflow, this pass used:
- direct HTTP extraction for https://muni-pal.io/ and https://muni-pal.io/pricing
- dogfood-output/ela49/screenshots/pricing.png
- dogfood-output/ela49/dom/pricing.dom.html
## Executive Summary
The public site is strong enough to anchor a Healthcare-first launch narrative, but it is not yet ready for a Healthcare + Housing launch without tightening positioning, pricing/payment verifiability, and advisory-boundary language.
- Homepage and pricing page returned HTTP 200.
- Healthcare positioning is concrete and differentiated: EMMA corpus, DSCR, payer mix, days cash, risk categories, and cost-of-capital framing.
- Pricing page has a clear free/subscription/per-project ladder.
- Pricing page includes an explicit municipal-advisory boundary disclaimer.
1. Housing is absent from the reviewed public launch surface, despite being a top-two launch scenario.
2. The pricing CTA/payment path could not be verified from the rendered DOM; Stripe readiness should be smoke-tested separately under ELA-50.
4. Pricing page language says "ongoing advisory access," which should be tightened because the footer says Muni-Pal is not providing municipal advisory services.
5. The static/no-JS fallback text repeats broad Healthcare pitch content after the pricing page footer; it is probably hidden in normal JS mode but should be checked for SEO/accessibility/no-JS polish.
Launch recommendation from this pass: launch with conditions. Healthcare-first public launch is plausible after copy and payment-path review; Healthcare + Housing launch should wait until Housing has an explicit public path or the launch is deliberately labeled Healthcare-first with Housing pilot by
## Findings
### F1 — Housing is missing from the public launch surface
URLs: https://muni-pal.io/, https://muni-pal.io/pricing
- Page title and primary text are Healthcare-specific.
- Homepage starts with Healthcare Bond Intelligence and Healthcare Bond Readiness Assessment framing.
- Pricing FAQ says Muni-Pal is built for healthcare bond issuances in the M–00M range.
- No Housing copy, Housing CTA, or Housing route was discovered from the reviewed pages.
Healthcare is the primary scenario, but Housing is also a top launch scenario. If both are launch targets, the public site currently over-signals a Healthcare-only product. That may be strategically fine for a Healthcare-first launch, but it is not enough for a dual Healthcare/Housing launch.
- For a Healthcare-first public launch: explicitly treat Housing as direct/outbound pilot only, not public-site self-serve.
- For a Healthcare + Housing launch: add a Housing landing path, sector selector, or pricing note explaining Housing pilot availability.
- Track under ELA-53 for Housing end-to-end dogfood and likely a follow-up public-copy issue if Housing remains in launch scope.
### F2 — Stripe/payment path was not verifiable from public DOM pass
URL: https://muni-pal.io/pricing
- Pricing page displays a Subscription tier at 99/month or ,990/year and a "Create Account to Subscribe" CTA.
- No Stripe URL or payment path was discoverable from the reviewed DOM/link extraction.
The user noted Stripe is configured to accept payments. Launch confidence requires proving the pricing CTA can safely reach the intended checkout/account creation flow, and that success/cancel return paths are correct.
- Execute ELA-50 next or soon: smoke-test pricing conversion and Stripe path.
### F3 — Advisory/compliance copy should be softened before launch
URLs: https://muni-pal.io/, https://muni-pal.io/pricing
- Pricing page says "Subscribe for ongoing advisory access."
The pricing page includes a useful disclaimer: Muni-Pal provides benchmarking, preparation, and analytical tools, not investment advice, and does not constitute municipal advisory services under Section 15B.
### F4 — Healthcare public message is strong but too narrow for current launch ambition
The Healthcare narrative is concrete and credible: 866 EMMA transactions, healthcare DSCR, payer mix, days cash, gross revenue pledge basis, spread/risk benchmarking, and readiness path.
This is a strength for a Healthcare-first wedge. But if Housing is part of the public launch, the lack of a sector bridge means Housing users may bounce or assume the product is not for them.
  - Healthcare-first public launch, Housing by invitation; or
  - public sector-selector launch with Healthcare and Housing routes.
- Do not dilute the strong Healthcare wedge unless Housing is truly ready for public inbound.
### F5 — Pricing page no-JS/static fallback appears to repeat homepage pitch after footer
URL: https://muni-pal.io/pricing
Rendered/static extraction includes pricing page content, then footer/disclaimer text, then the broader Healthcare lead-capture pitch and "This application requires JavaScript" fallback text.
This may be harmless hidden fallback content in the SPA, but it can affect no-JS users, screen readers, crawler snippets, or perceived polish if exposed under certain failure modes.
### F6 — Security headers are partially present; CSP was not observed in the simple HTTP header subset
URLs: https://muni-pal.io/, https://muni-pal.io/pricing
Not a blocker for controlled pilot launch, but public site hardening should include a deliberate CSP posture if feasible.
## Link Check Summary
- https://muni-pal.io/healthcare
- https://muni-pal.io/pricing was directly reviewed and returned HTTP 200
## Launch Readiness Verdict
Healthcare-first controlled launch: conditionally promising.
Healthcare + Housing public launch: not ready from the public site alone because Housing is not visible.
1. ELA-50 — smoke-test Stripe/pricing conversion.
2. ELA-51 — review local dashboard platform landing.
3. ELA-52 — Healthcare end-to-end pilot walkthrough.
4. ELA-53 — Housing end-to-end pilot walkthrough.
If the goal is a public Healthcare-first launch, keep the public site tightly Healthcare-focused and move Housing through invite-only/direct pilot workflows until Housing has public copy and demo data.
If the goal is an explicit Healthcare + Housing launch, add a Housing public landing path before broad launch.

## docs/launch-readiness/ELA50_STRIPE_PAYMENT_SMOKE_TEST.md
# ELA-50 Stripe Payment Path and Pricing Conversion Smoke Test
Issue: ELA-50 — BFMS Launch: Smoke test Stripe payment path and pricing conversion
Scope: https://muni-pal.io/pricing pricing CTA, unauthenticated account handoff, checkout return URLs, and backend Stripe checkout/webhook contract.
## Safety Boundary
This pass did not enter card details, did not create a live Stripe payment, and did not intentionally create a live production subscription. The review stopped at non-charging evidence: public route availability, rendered DOM states, frontend/backend code-path inspection, and existing mocked Stripe
## Evidence Artifacts
- dogfood-output/ela50/capture2/screenshots/pricing.png
- dogfood-output/ela50/capture2/screenshots/pricing_success.png
- dogfood-output/ela50/capture2/screenshots/pricing_cancel.png
## Executive Summary
1. The public pricing CTA correctly routes unauthenticated users to account creation instead of directly exposing Stripe checkout.
3. Backend Stripe checkout/session and webhook behavior is covered by integration tests that pass.
5. The pricing CTA depends on VITE_STRIPE_PRICE_MONTHLY/VITE_STRIPE_PRICE_ANNUAL being present at frontend build time; if they are absent, the Subscribe CTA is disabled. The rendered production DOM showed the CTA as enabled, which is a good sign, but this should be documented as a launch config chec
Verdict: conditionally pass for non-charging smoke test. Proceed to ELA-51/52/53, but before accepting real payments, add a visible launch ops checklist or environment assertion covering Stripe mode, price IDs, webhook endpoint/signing secret, and success/cancel URLs.
## Findings
### F1 — Pricing CTA routes unauthenticated users to account creation
Severity: Pass / expected behavior
- frontend/src/pages/tools/PricingPage.tsx
The public pricing page renders a "Create Account to Subscribe" button for unauthenticated users. Frontend source shows the handler:
- if no user is authenticated, navigate to /auth?mode=register&returnTo=/pricing
- if a user is authenticated and a Stripe price id exists, call /api/v1/stripe/create-checkout-session
- Password
This is the right launch posture. Public pricing should not create a BFMS project or paid entitlement before account creation and onboarding/qualification. It also avoids sending anonymous visitors directly into payment without account context.
### F2 — Checkout success and cancel return URLs are defined and render
Severity: Pass with minor copy follow-up
- src/munipal/api/routes/stripe.py
- dogfood-output/ela50/capture2/screenshots/pricing_success.png
- dogfood-output/ela50/capture2/screenshots/pricing_cancel.png
- success_url: FRONTEND_URL/pricing?checkout=success
- cancel_url: FRONTEND_URL/pricing?checkout=cancel
This satisfies the basic launch requirement that Stripe return paths are not dead ends.
Minor recommendation:
Consider making the success state clarify what happens next, e.g. "Your account is subscribed; continue to the dashboard" or "Sign in to access subscription tools," depending on the actual post-checkout entitlement model.
### F3 — Backend Stripe contract is covered by passing integration tests
Severity: Pass
- tests/integration/test_stripe_api.py
- 10 passed in 1.42s
- Stripe invalid-request handling
### F4 — Live/test Stripe mode posture is not externally visible
- repo env examples did not expose Stripe mode variables beyond credential placeholders
- public UI does not indicate whether the current Stripe path is live or test
- this pass intentionally avoided live checkout/card entry
The code supports Stripe checkout, but the reviewed surfaces do not make the active Stripe mode explicit for reviewers/operators. The user has stated Stripe is configured to accept payments, but launch confidence still requires an operational check that confirms:
- test purchases are performed only against Stripe test mode, or live-mode testing uses a deliberately safe manual process
Add a launch ops checklist or health check that records Stripe readiness without exposing secrets. At minimum, document:
- Stripe mode: test or live
### F5 — Price IDs are frontend build-time requirements
- frontend/src/pages/tools/PricingPage.tsx
The rendered production pricing page showed the "Create Account to Subscribe" button enabled, which suggests the monthly price ID exists in the deployed build.
### F6 — Account creation copy still says "advisory services"
This conflicts with the desired non-municipal-advisory posture and the pricing-page disclaimer. It should be softened before public launch.
## Acceptance Criteria Mapping
### Verify pricing CTAs route to expected checkout/payment path
Status: Partial pass.
- A live authenticated click-through to Stripe Checkout was not performed to avoid production payment side effects.
### Confirm test/live mode posture is explicit and safe for review
Status: Needs follow-up before accepting real payments.
### Confirm successful/canceled checkout return paths are defined
Status: Pass.
- Success and cancel URLs are defined in backend Stripe route.
### Verify no misleading product entitlement promises are made before onboarding qualification
Status: Partial pass.
- Follow-up: success-state and subscription copy should clarify that subscription access is not deal approval, issuance recommendation, or advisor replacement.
### Document Stripe/webhook/accounting follow-up issues
Status: Pass.
## Recommended Follow-Up Issues
1. Add Stripe launch ops checklist / non-secret readiness documentation.
2. ELA-59 should update account/signup and pricing language.
3. Before public live payments, perform one controlled Stripe test-mode checkout using Stripe test cards.
   - Only if the deployment is pointed at test-mode Stripe keys.
   - If already in live mode, use Stripe dashboard/manual verification instead of entering card data through the public site.
## Verification Commands
- Captured public HTTP status for pricing/auth/return routes into .
- Ran Stripe integration tests:
  - Result: 10 passed in 1.42s
  - Result: passed
## Launch Verdict
Conditionally pass for non-charging smoke test.
Do not treat this as final authorization to accept real public payments until Stripe mode, price IDs, webhook registration, and payment-event accounting expectations are explicitly checked in a launch ops checklist.

## docs/launch-readiness/ELA60_CURRENT_HEAD_ELA49_50_RERUN.md
# ELA-60 Current-HEAD Re-run of ELA-49/ELA-50 Workflows
Local HEAD at start of pass: 1754ab6 docs: smoke test stripe pricing conversion
## Purpose
ELA-49 and ELA-50 were valid dogfood passes, but they reviewed the deployed public site at https://muni-pal.io/ and https://muni-pal.io/pricing. This pass re-runs the same launch-readiness questions against the current active BFMS checkout running locally from the canonical WSL repo.
## Method
- dogfood-output/ela60/chrome_pricing.dom.html
- dogfood-output/ela60/chrome_pricing.stderr.txt
The built-in browser tool still fails in this Windows/WSL Hermes session with WinError 193. Windows Chrome headless launched but produced a zero-byte dumped DOM for the WSL localhost pricing route, so this pass uses HTTP evidence plus source-level inspection and production build verification instead
## Local-current route checks
| Pricing | http://127.0.0.1:4121/pricing | 200 |
| Pricing success return | http://127.0.0.1:4121/pricing?checkout=success | 200 |
| Pricing cancel return | http://127.0.0.1:4121/pricing?checkout=cancel | 200 |
| Auth/register return | http://127.0.0.1:4121/auth?mode=register&returnTo=/pricing | 200 |
## Source-level checkout and pricing inspection
- frontend/src/pages/tools/PricingPage.tsx
- src/munipal/api/routes/stripe.py
- tests/integration/test_stripe_api.py
- Pricing CTA text includes Create Account to Subscribe.
- Unauthenticated subscription flow routes toward auth/register with returnTo=/pricing.
- Frontend checkout depends on VITE_STRIPE_PRICE_MONTHLY and VITE_STRIPE_PRICE_ANNUAL build-time values.
- Backend checkout session defines success_url as FRONTEND_URL/pricing?checkout=success.
- Backend checkout session defines cancel_url as FRONTEND_URL/pricing?checkout=cancel.
- Stripe integration tests still cover create-checkout-session behavior.
Interpretation: the core ELA-50 code-path conclusions remain valid for current HEAD. The pass still does not prove a real checkout, webhook delivery, live/test Stripe mode, accounting readiness, or production entitlement correctness.
## Comparison to ELA-49
ELA-49 finding: public site and pricing returned HTTP 200.
Status: remains valid locally, but must be rechecked on production/staging after deployment.
ELA-49 finding: Healthcare positioning is strong and launch-plausible.
Current HEAD result: not fully re-proven by rendered browser evidence in this pass. Source/build checks do not replace actual public-copy review. The prior deployed-site finding remains valid for the deployed site as of ELA-49, but should be refreshed after deployment.
Status: carried forward as deployed-site evidence only.
ELA-49 finding: Housing is absent from the reviewed public launch surface.
Current HEAD result: not fully re-proven by rendered browser evidence in this pass. No local rendered DOM was captured. Given no dedicated Housing public path was validated here, keep the launch recommendation unchanged: Healthcare-first public launch is plausible; Housing should remain direct-pilot
Status: still a launch strategy concern; requires rendered staging/prod review.
ELA-49 finding: advisory/legal/pricing language should be softened, including adversarial-advisor language and advisory-access wording.
Status: remains valid as a launch copy/compliance follow-up.
## Comparison to ELA-50
ELA-50 finding: public pricing CTA routes unauthenticated users to account creation rather than directly to Stripe.
Status: remains valid for current HEAD at source/route level.
Current HEAD result: backend source still defines success and cancel URLs; local frontend routes for both query states return HTTP 200. Rendering content was not proven because browser fallback failed.
Status: route-level pass; rendered-copy verification should be refreshed on staging/prod.
ELA-50 finding: backend Stripe tests pass.
Current HEAD result: tests/integration/test_stripe_api.py passed, 10 passed in 0.93s.
Status: remains valid.
Current HEAD result: unchanged. This pass did not expose or verify secrets and did not perform a live or test card transaction.
Status: remains a required launch-ops follow-up.
## Current verdict
This ELA-60 pass resolves the main workspace concern: the active WSL version of BFMS can be run locally, and the ELA-49/50 local-current workflow can be exercised from /home/st3ja/Developer/MUNI-PAL.
2. ELA-60 confirms current local HEAD runs the comparable routes and retains the Stripe/payment code-path invariants.
## Launch recommendation
Proceed with current BFMS advancement, but do not use ELA-49/50 alone as final launch approval for current HEAD. Before public launch or payment enablement, run one more rendered browser pass against a URL that actually serves current HEAD, preferably staging first and then production.
- Deploy or stage current HEAD, then re-run the rendered browser dogfood captures for homepage, pricing, auth/register return, checkout success, and checkout cancel.
- Keep Healthcare-first public positioning unless/until a Housing public path is reviewed.
- Add or complete a non-secret Stripe launch-ops checklist covering provider mode, price IDs, webhook endpoint/events, signing secret presence, success/cancel URLs, accounting, refunds, support, and entitlement behavior.
## Verification
- /home/st3ja/.local/bin/uv run --extra dev pytest tests/integration/test_stripe_api.py -q: 10 passed in 0.93s
- npm --prefix frontend run build: passed; Vite emitted the existing non-blocking chunk-size warning.
- Local HTTP route probe for backend health, home, pricing, pricing success, pricing cancel, and auth/register return: all HTTP 200
