# ELA-50 Stripe Payment Path and Pricing Conversion Smoke Test

Issue: ELA-50 — BFMS Launch: Smoke test Stripe payment path and pricing conversion
Date: 2026-04-29
Scope: https://muni-pal.io/pricing pricing CTA, unauthenticated account handoff, checkout return URLs, and backend Stripe checkout/webhook contract.
Launch lens: safe non-charging review of subscription conversion readiness before public launch.

## Safety Boundary

This pass did not enter card details, did not create a live Stripe payment, and did not intentionally create a live production subscription. The review stopped at non-charging evidence: public route availability, rendered DOM states, frontend/backend code-path inspection, and existing mocked Stripe integration tests.

## Evidence Artifacts

- dogfood-output/ela50/http_extract.json
- dogfood-output/ela50/capture2/chrome_capture.json
- dogfood-output/ela50/capture2/dom_extract.json
- dogfood-output/ela50/capture2/screenshots/pricing.png
- dogfood-output/ela50/capture2/screenshots/pricing_success.png
- dogfood-output/ela50/capture2/screenshots/pricing_cancel.png
- dogfood-output/ela50/capture2/screenshots/auth_return.png

## Executive Summary

The subscription payment path is close, but I would not call it fully launch-ready until two configuration/UX gaps are explicitly closed:

1. The public pricing CTA correctly routes unauthenticated users to account creation instead of directly exposing Stripe checkout.
2. Checkout success and cancel return routes are defined and render HTTP 200.
3. Backend Stripe checkout/session and webhook behavior is covered by integration tests that pass.
4. However, live/test mode posture is not visible in repo examples or the reviewed public UI, so reviewers cannot tell whether the configured payment path is safe to test.
5. The pricing CTA depends on VITE_STRIPE_PRICE_MONTHLY/VITE_STRIPE_PRICE_ANNUAL being present at frontend build time; if they are absent, the Subscribe CTA is disabled. The rendered production DOM showed the CTA as enabled, which is a good sign, but this should be documented as a launch config check.
6. Unauthenticated account creation copy still says data is used for "bond readiness and advisory services," which should be tightened under ELA-59 because it conflicts with the non-MA posture.

Verdict: conditionally pass for non-charging smoke test. Proceed to ELA-51/52/53, but before accepting real payments, add a visible launch ops checklist or environment assertion covering Stripe mode, price IDs, webhook endpoint/signing secret, and success/cancel URLs.

## Findings

### F1 — Pricing CTA routes unauthenticated users to account creation

Severity: Pass / expected behavior
Category: Conversion flow
Evidence:
- frontend/src/pages/tools/PricingPage.tsx
- dogfood-output/ela50/capture2/dom_extract.json
- dogfood-output/ela50/capture2/screenshots/auth_return.png

Observed:

The public pricing page renders a "Create Account to Subscribe" button for unauthenticated users. Frontend source shows the handler:

- if no user is authenticated, navigate to /auth?mode=register&returnTo=/pricing
- if a user is authenticated and a Stripe price id exists, call /api/v1/stripe/create-checkout-session

The auth return route rendered HTTP 200 and displayed account creation fields:

- Full Name
- Organization
- Email
- Password
- Create Account

Why it matters:

This is the right launch posture. Public pricing should not create a BFMS project or paid entitlement before account creation and onboarding/qualification. It also avoids sending anonymous visitors directly into payment without account context.

### F2 — Checkout success and cancel return URLs are defined and render

Severity: Pass with minor copy follow-up
Category: Checkout return-path readiness
Evidence:
- src/munipal/api/routes/stripe.py
- dogfood-output/ela50/http_extract.json
- dogfood-output/ela50/capture2/dom_extract.json
- dogfood-output/ela50/capture2/screenshots/pricing_success.png
- dogfood-output/ela50/capture2/screenshots/pricing_cancel.png

Observed:

Backend checkout session creation uses:

- success_url: FRONTEND_URL/pricing?checkout=success
- cancel_url: FRONTEND_URL/pricing?checkout=cancel

Both URLs returned HTTP 200 in the public deployment smoke test.

Rendered DOM extraction detected:

- : payment/success language present
- : cancel language present, including "Checkout was cancelled. No charge was made. You can try again anytime."

Why it matters:

This satisfies the basic launch requirement that Stripe return paths are not dead ends.

Minor recommendation:

Consider making the success state clarify what happens next, e.g. "Your account is subscribed; continue to the dashboard" or "Sign in to access subscription tools," depending on the actual post-checkout entitlement model.

### F3 — Backend Stripe contract is covered by passing integration tests

Severity: Pass
Category: Backend/payment contract
Evidence:
- tests/integration/test_stripe_api.py

Verification:



Result:

- 10 passed in 1.42s

Observed coverage includes:

- checkout session creation behavior
- Stripe invalid-request handling
- webhook handling for checkout completion
- subscription status sync
- invalid webhook signature/payload handling

Why it matters:

This gives confidence in the backend contract without making a live charge during launch review.

### F4 — Live/test Stripe mode posture is not externally visible

Severity: High before accepting real payments
Category: Launch operations / payment safety
Evidence:
- repo env examples did not expose Stripe mode variables beyond credential placeholders
- public UI does not indicate whether the current Stripe path is live or test
- this pass intentionally avoided live checkout/card entry

Observed:

The code supports Stripe checkout, but the reviewed surfaces do not make the active Stripe mode explicit for reviewers/operators. The user has stated Stripe is configured to accept payments, but launch confidence still requires an operational check that confirms:

- current publishable/secret keys are intended for live mode or test mode
- monthly and annual price IDs match the intended product/prices
- webhook endpoint is registered for the deployment receiving checkout events
- webhook signing secret is present in the deployed backend
- test purchases are performed only against Stripe test mode, or live-mode testing uses a deliberately safe manual process

Recommended action:

Add a launch ops checklist or health check that records Stripe readiness without exposing secrets. At minimum, document:

- Stripe mode: test or live
- configured price IDs: present, redacted, and matching expected monthly/annual labels
- webhook endpoint configured: yes/no
- webhook events enabled: checkout.session.completed, customer.subscription.updated, customer.subscription.deleted
- success/cancel URLs configured and verified

### F5 — Price IDs are frontend build-time requirements

Severity: Medium
Category: Configuration readiness
Evidence:
- frontend/src/pages/tools/PricingPage.tsx

Observed:

The Subscribe button uses:




The button is disabled if the monthly price id is missing:



The rendered production pricing page showed the "Create Account to Subscribe" button enabled, which suggests the monthly price ID exists in the deployed build.

Why it matters:

Because Vite env variables are baked into the frontend build, correcting a missing or wrong price ID requires rebuilding/redeploying the public frontend. This should be explicit in the launch checklist.

### F6 — Account creation copy still says "advisory services"

Severity: Medium-High
Category: Compliance / advisor-boundary language
Evidence:
- dogfood-output/ela50/capture2/dom_extract.json
- dogfood-output/ela50/capture2/screenshots/auth_return.png

Observed copy:

"By continuing, you agree to Muni-Pal's terms of service. Your data is used solely for bond readiness and advisory services."

Why it matters:

This conflicts with the desired non-municipal-advisory posture and the pricing-page disclaimer. It should be softened before public launch.

Recommended replacement direction:

Use non-MA phrasing such as:

- "Your data is used solely to provide bond-readiness tools, benchmarking, and platform support."
- Avoid "advisory services" unless counsel confirms the intended regulated meaning.

Track under ELA-59.

## Acceptance Criteria Mapping

### Verify pricing CTAs route to expected checkout/payment path

Status: Partial pass.

- Unauthenticated CTA routes to account creation route by code inspection and rendered auth route verification.
- Authenticated checkout route is defined as .
- A live authenticated click-through to Stripe Checkout was not performed to avoid production payment side effects.

### Confirm test/live mode posture is explicit and safe for review

Status: Needs follow-up before accepting real payments.

- The current implementation can support live payments, but the reviewed repo/public UI does not make mode/posture explicit.
- Add a launch ops checklist or non-secret readiness endpoint/doc.

### Confirm successful/canceled checkout return paths are defined

Status: Pass.

- Success and cancel URLs are defined in backend Stripe route.
- Both public return URLs return HTTP 200 and render relevant success/cancel language.

### Verify no misleading product entitlement promises are made before onboarding qualification

Status: Partial pass.

- Good: public CTA says create account before subscribing and does not create a BFMS project.
- Follow-up: success-state and subscription copy should clarify that subscription access is not deal approval, issuance recommendation, or advisor replacement.
- Follow-up: account creation copy should remove "advisory services."

### Document Stripe/webhook/accounting follow-up issues

Status: Pass.

Follow-ups are listed below.

## Recommended Follow-Up Issues

1. Add Stripe launch ops checklist / non-secret readiness documentation.
   - Covers mode, price IDs, webhook endpoint/events, signing secret presence, success/cancel URL verification.
   - Could be added as a child issue under ELA-48 if not already covered by deployment ops.

2. ELA-59 should update account/signup and pricing language.
   - Replace "advisory services" in account creation copy.
   - Clarify subscription entitlement boundaries.
   - Keep product advisor-supportive rather than advisor-replacing.

3. Before public live payments, perform one controlled Stripe test-mode checkout using Stripe test cards.
   - Only if the deployment is pointed at test-mode Stripe keys.
   - If already in live mode, use Stripe dashboard/manual verification instead of entering card data through the public site.

## Verification Commands

- Captured public HTTP status for pricing/auth/return routes into .
- Captured rendered DOM/screenshots with Windows Chrome headless into .
- Ran Stripe integration tests:

  - Result: 10 passed in 1.42s
- Ran environment check:

  - Result: status OK
- Ran whitespace check:

  - Result: passed

## Launch Verdict

Conditionally pass for non-charging smoke test.

Do not treat this as final authorization to accept real public payments until Stripe mode, price IDs, webhook registration, and payment-event accounting expectations are explicitly checked in a launch ops checklist.
