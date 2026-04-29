# ELA-49 Public Site and Pricing Dogfood Report

Issue: ELA-49 — BFMS Launch: Dogfood public site and pricing pages
Date: 2026-04-29
Scope: https://muni-pal.io/ and https://muni-pal.io/pricing
Launch lens: Healthcare and Housing pilot readiness, public-message clarity, pricing/Stripe expectation-setting, advisory/compliance boundary language.

## Method

The built-in browser stack failed in this Hermes/Windows session with a Win32 browser launch error, and browser-harness could not attach because Chrome remote debugging was not enabled. Per the dogfood fallback workflow, this pass used:

- direct HTTP extraction for https://muni-pal.io/ and https://muni-pal.io/pricing
- Windows Chrome headless from WSL for rendered DOM and screenshots
- internal-link status checks for links discovered from the reviewed pages

Evidence artifacts:

- dogfood-output/ela49/screenshots/home.png
- dogfood-output/ela49/screenshots/pricing.png
- dogfood-output/ela49/dom/home.dom.html
- dogfood-output/ela49/dom/pricing.dom.html
- dogfood-output/ela49/dom_extract.json
- dogfood-output/ela49/link_check.json

## Executive Summary

The public site is strong enough to anchor a Healthcare-first launch narrative, but it is not yet ready for a Healthcare + Housing launch without tightening positioning, pricing/payment verifiability, and advisory-boundary language.

Observed strengths:

- Homepage and pricing page returned HTTP 200.
- Internal links discovered from the reviewed pages returned HTTP 200.
- HSTS is present on the Vercel-hosted public pages.
- Healthcare positioning is concrete and differentiated: EMMA corpus, DSCR, payer mix, days cash, risk categories, and cost-of-capital framing.
- Pricing page has a clear free/subscription/per-project ladder.
- Pricing page includes an explicit municipal-advisory boundary disclaimer.

Primary launch-confidence gaps:

1. Housing is absent from the reviewed public launch surface, despite being a top-two launch scenario.
2. The pricing CTA/payment path could not be verified from the rendered DOM; Stripe readiness should be smoke-tested separately under ELA-50.
3. Some copy risks sounding adversarial toward advisors or too close to advisor-substitute positioning.
4. Pricing page language says "ongoing advisory access," which should be tightened because the footer says Muni-Pal is not providing municipal advisory services.
5. The static/no-JS fallback text repeats broad Healthcare pitch content after the pricing page footer; it is probably hidden in normal JS mode but should be checked for SEO/accessibility/no-JS polish.

Launch recommendation from this pass: launch with conditions. Healthcare-first public launch is plausible after copy and payment-path review; Healthcare + Housing launch should wait until Housing has an explicit public path or the launch is deliberately labeled Healthcare-first with Housing pilot by direct invitation only.

## Findings

### F1 — Housing is missing from the public launch surface

Severity: High
Category: Product positioning / launch readiness
URLs: https://muni-pal.io/, https://muni-pal.io/pricing

Observed:

- Page title and primary text are Healthcare-specific.
- Homepage starts with Healthcare Bond Intelligence and Healthcare Bond Readiness Assessment framing.
- Pricing FAQ says Muni-Pal is built for healthcare bond issuances in the M–00M range.
- No Housing copy, Housing CTA, or Housing route was discovered from the reviewed pages.

Why it matters:

Healthcare is the primary scenario, but Housing is also a top launch scenario. If both are launch targets, the public site currently over-signals a Healthcare-only product. That may be strategically fine for a Healthcare-first launch, but it is not enough for a dual Healthcare/Housing launch.

Recommended action:

- For a Healthcare-first public launch: explicitly treat Housing as direct/outbound pilot only, not public-site self-serve.
- For a Healthcare + Housing launch: add a Housing landing path, sector selector, or pricing note explaining Housing pilot availability.
- Track under ELA-53 for Housing end-to-end dogfood and likely a follow-up public-copy issue if Housing remains in launch scope.

### F2 — Stripe/payment path was not verifiable from public DOM pass

Severity: High
Category: Functional / conversion
URL: https://muni-pal.io/pricing

Observed:

- Pricing page displays a Subscription tier at 99/month or ,990/year and a "Create Account to Subscribe" CTA.
- Rendered DOM extraction saw this CTA as a button, not a direct link in the static/link inventory.
- No Stripe URL or payment path was discoverable from the reviewed DOM/link extraction.

Why it matters:

The user noted Stripe is configured to accept payments. Launch confidence requires proving the pricing CTA can safely reach the intended checkout/account creation flow, and that success/cancel return paths are correct.

Recommended action:

- Execute ELA-50 next or soon: smoke-test pricing conversion and Stripe path.
- Confirm whether the CTA opens checkout, account creation, or requires an authenticated app session.
- Confirm live/test mode posture and avoid unsafe live-charge behavior during review.

### F3 — Advisory/compliance copy should be softened before launch

Severity: Medium-High
Category: Compliance / positioning
URLs: https://muni-pal.io/, https://muni-pal.io/pricing

Observed copy examples:

- "Here's what your advisors won't tell you for free."
- "Actual spread data so you can pressure-test your advisor's term sheet."
- "The Accelerator helps you document your way to a better rating."
- Pricing page says "Subscribe for ongoing advisory access."

Positive offset:

The pricing page includes a useful disclaimer: Muni-Pal provides benchmarking, preparation, and analytical tools, not investment advice, and does not constitute municipal advisory services under Section 15B.

Why it matters:

The product should be advisor-ready and advisor-supportive, not advisor-replacing or adversarial. Some current public copy can be read as "we tell you what advisors won't" or as implying a rating outcome. That may increase trust friction with municipal advisors, bond counsel, and sophisticated issuers.

Recommended action:

- Track under ELA-59.
- Replace "advisory access" with "platform access," "analyst support," "readiness support," or another non-MA phrase.
- Soften "what your advisors won't tell you for free" to a less adversarial claim such as "see the benchmarks before the first scoping call" or "arrive prepared with benchmark-backed questions."
- Rephrase "document your way to a better rating" to avoid implying rating improvement as an outcome.

### F4 — Healthcare public message is strong but too narrow for current launch ambition

Severity: Medium
Category: Product strategy / UX content
URL: https://muni-pal.io/

Observed:

The Healthcare narrative is concrete and credible: 866 EMMA transactions, healthcare DSCR, payer mix, days cash, gross revenue pledge basis, spread/risk benchmarking, and readiness path.

Why it matters:

This is a strength for a Healthcare-first wedge. But if Housing is part of the public launch, the lack of a sector bridge means Housing users may bounce or assume the product is not for them.

Recommended action:

- Decide the public launch stance:
  - Healthcare-first public launch, Housing by invitation; or
  - public sector-selector launch with Healthcare and Housing routes.
- Do not dilute the strong Healthcare wedge unless Housing is truly ready for public inbound.

### F5 — Pricing page no-JS/static fallback appears to repeat homepage pitch after footer

Severity: Low-Medium
Category: UX / accessibility / SEO
URL: https://muni-pal.io/pricing

Observed:

Rendered/static extraction includes pricing page content, then footer/disclaimer text, then the broader Healthcare lead-capture pitch and "This application requires JavaScript" fallback text.

Why it matters:

This may be harmless hidden fallback content in the SPA, but it can affect no-JS users, screen readers, crawler snippets, or perceived polish if exposed under certain failure modes.

Recommended action:

- During ELA-49/59 or frontend polish, check the actual rendered visual state and accessibility tree.
- Ensure no-JS fallback content is intentional, concise, and not duplicative/confusing.

### F6 — Security headers are partially present; CSP was not observed in the simple HTTP header subset

Severity: Low
Category: Security hardening
URLs: https://muni-pal.io/, https://muni-pal.io/pricing

Observed:

- Strict-Transport-Security was present.
- Content-Security-Policy was not observed in the captured header subset.

Why it matters:

Not a blocker for controlled pilot launch, but public site hardening should include a deliberate CSP posture if feasible.

Recommended action:

- Treat as a later public-web hardening issue unless additional review finds script-injection exposure or third-party script risk.

## Link Check Summary

All internal links discovered from the reviewed pages returned HTTP 200:

- https://muni-pal.io/
- https://muni-pal.io/healthcare
- https://muni-pal.io/tools
- https://muni-pal.io/tools/readiness
- https://muni-pal.io/tools/market-intelligence
- https://muni-pal.io/tools/benchmark
- https://muni-pal.io/tools/credit-spreads
- https://muni-pal.io/pricing was directly reviewed and returned HTTP 200

## Launch Readiness Verdict

Healthcare-first controlled launch: conditionally promising.

Healthcare + Housing public launch: not ready from the public site alone because Housing is not visible.

Recommended next Linear sequence:

1. ELA-50 — smoke-test Stripe/pricing conversion.
2. ELA-51 — review local dashboard platform landing.
3. ELA-52 — Healthcare end-to-end pilot walkthrough.
4. ELA-53 — Housing end-to-end pilot walkthrough.
5. ELA-59 — advisor/compliance language live QA.

Decision point:

If the goal is a public Healthcare-first launch, keep the public site tightly Healthcare-focused and move Housing through invite-only/direct pilot workflows until Housing has public copy and demo data.

If the goal is an explicit Healthcare + Housing launch, add a Housing public landing path before broad launch.
