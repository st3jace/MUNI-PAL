# ELA-60 Current-HEAD Re-run of ELA-49/ELA-50 Workflows

Issue: ELA-60 — BFMS Launch: Re-run ELA-49/50 workflows against current BFMS HEAD
Date: 2026-05-05
Repo: /home/st3ja/Developer/MUNI-PAL
Local HEAD at start of pass: 1754ab6 docs: smoke test stripe pricing conversion
Baseline drift: local master was 19 commits ahead of origin/master before this ELA-60 report commit.

## Purpose

ELA-49 and ELA-50 were valid dogfood passes, but they reviewed the deployed public site at https://muni-pal.io/ and https://muni-pal.io/pricing. This pass re-runs the same launch-readiness questions against the current active BFMS checkout running locally from the canonical WSL repo.

The goal is not to replace the deployed-site evidence. The goal is to determine whether those findings can be relied on for current active HEAD, and to identify what must be re-verified after the current local commits are deployed.

## Method

Local services started from the canonical repo:

- Backend: /home/st3ja/.local/bin/uv run --extra dev uvicorn munipal.main:app --host 127.0.0.1 --port 8000
- Frontend: npm run dev -- --host 127.0.0.1 --port 4121 from frontend/

Evidence captured:

- dogfood-output/ela60/http_local_current.json
- dogfood-output/ela60/source_inspection.json
- dogfood-output/ela60/source_snippets.json
- dogfood-output/ela60/browser_fallback.json
- dogfood-output/ela60/chrome_pricing.dom.html
- dogfood-output/ela60/chrome_pricing.stderr.txt

Browser limitation:

The built-in browser tool still fails in this Windows/WSL Hermes session with WinError 193. Windows Chrome headless launched but produced a zero-byte dumped DOM for the WSL localhost pricing route, so this pass uses HTTP evidence plus source-level inspection and production build verification instead of claiming screenshot/rendered-browser confirmation. This is materially weaker than ELA-49/50's deployed-site Chrome captures and should be refreshed on a staging URL or deployed URL after the local commits are deployed.

## Local-current route checks

All required local-current routes returned HTTP 200 from WSL:

| Route | URL | Result |
| --- | --- | --- |
| Backend health | http://127.0.0.1:8000/health | 200 |
| Frontend home | http://127.0.0.1:4121/ | 200 |
| Pricing | http://127.0.0.1:4121/pricing | 200 |
| Pricing success return | http://127.0.0.1:4121/pricing?checkout=success | 200 |
| Pricing cancel return | http://127.0.0.1:4121/pricing?checkout=cancel | 200 |
| Auth/register return | http://127.0.0.1:4121/auth?mode=register&returnTo=/pricing | 200 |

Interpretation: current HEAD can run the relevant local BFMS surfaces and the target routes are not missing or dead on local dev. This confirms the user's concern can be operationally addressed from the active WSL tree rather than the historical OneDrive tree.

## Source-level checkout and pricing inspection

Relevant local-current files inspected:

- frontend/src/pages/tools/PricingPage.tsx
- frontend/src/pages/Auth.tsx
- src/munipal/api/routes/stripe.py
- tests/integration/test_stripe_api.py

Observed source-level invariants still present at current HEAD:

- Pricing CTA text includes Create Account to Subscribe.
- Unauthenticated subscription flow routes toward auth/register with returnTo=/pricing.
- Frontend checkout depends on VITE_STRIPE_PRICE_MONTHLY and VITE_STRIPE_PRICE_ANNUAL build-time values.
- Backend checkout session defines success_url as FRONTEND_URL/pricing?checkout=success.
- Backend checkout session defines cancel_url as FRONTEND_URL/pricing?checkout=cancel.
- Backend webhook route handles checkout.session.completed.
- Backend webhook route handles customer.subscription.updated and customer.subscription.deleted.
- Stripe integration tests still cover create-checkout-session behavior.

Interpretation: the core ELA-50 code-path conclusions remain valid for current HEAD. The pass still does not prove a real checkout, webhook delivery, live/test Stripe mode, accounting readiness, or production entitlement correctness.

## Comparison to ELA-49

ELA-49 finding: public site and pricing returned HTTP 200.

Current HEAD result: still locally true for the comparable frontend routes. Backend health is also healthy locally.

Status: remains valid locally, but must be rechecked on production/staging after deployment.

ELA-49 finding: Healthcare positioning is strong and launch-plausible.

Current HEAD result: not fully re-proven by rendered browser evidence in this pass. Source/build checks do not replace actual public-copy review. The prior deployed-site finding remains valid for the deployed site as of ELA-49, but should be refreshed after deployment.

Status: carried forward as deployed-site evidence only.

ELA-49 finding: Housing is absent from the reviewed public launch surface.

Current HEAD result: not fully re-proven by rendered browser evidence in this pass. No local rendered DOM was captured. Given no dedicated Housing public path was validated here, keep the launch recommendation unchanged: Healthcare-first public launch is plausible; Housing should remain direct-pilot/invite-only until a Housing public path is explicitly reviewed.

Status: still a launch strategy concern; requires rendered staging/prod review.

ELA-49 finding: advisory/legal/pricing language should be softened, including adversarial-advisor language and advisory-access wording.

Current HEAD result: not fully re-proven locally by rendered browser evidence. ELA-59 remains the right copy/language follow-up.

Status: remains valid as a launch copy/compliance follow-up.

## Comparison to ELA-50

ELA-50 finding: public pricing CTA routes unauthenticated users to account creation rather than directly to Stripe.

Current HEAD result: source-level inspection confirms the intended unauthenticated routing remains present; auth/register return route returns HTTP 200 locally.

Status: remains valid for current HEAD at source/route level.

ELA-50 finding: checkout success/cancel return URLs are defined and render.

Current HEAD result: backend source still defines success and cancel URLs; local frontend routes for both query states return HTTP 200. Rendering content was not proven because browser fallback failed.

Status: route-level pass; rendered-copy verification should be refreshed on staging/prod.

ELA-50 finding: backend Stripe tests pass.

Current HEAD result: tests/integration/test_stripe_api.py passed, 10 passed in 0.93s.

Status: remains valid.

ELA-50 finding: do not treat smoke test as final approval for public live payments until mode, price IDs, webhook endpoint/events, signing secret, and accounting expectations are explicitly checked.

Current HEAD result: unchanged. This pass did not expose or verify secrets and did not perform a live or test card transaction.

Status: remains a required launch-ops follow-up.

## Current verdict

This ELA-60 pass resolves the main workspace concern: the active WSL version of BFMS can be run locally, and the ELA-49/50 local-current workflow can be exercised from /home/st3ja/Developer/MUNI-PAL.

It does not fully replace the ELA-49/50 deployed-browser dogfood evidence, because the available browser stack could not capture local rendered DOM/screenshots from WSL localhost. The right confidence model is therefore:

1. ELA-49/50 are valid for the deployed public site that was reviewed at the time.
2. ELA-60 confirms current local HEAD runs the comparable routes and retains the Stripe/payment code-path invariants.
3. Production launch confidence still requires a staging or production re-dogfood after deploying current local HEAD, because local master was 19 commits ahead of origin/master.

## Launch recommendation

Proceed with current BFMS advancement, but do not use ELA-49/50 alone as final launch approval for current HEAD. Before public launch or payment enablement, run one more rendered browser pass against a URL that actually serves current HEAD, preferably staging first and then production.

Recommended follow-ups:

- Deploy or stage current HEAD, then re-run the rendered browser dogfood captures for homepage, pricing, auth/register return, checkout success, and checkout cancel.
- Keep Healthcare-first public positioning unless/until a Housing public path is reviewed.
- Complete ELA-59 copy/compliance language tightening before broad public launch.
- Add or complete a non-secret Stripe launch-ops checklist covering provider mode, price IDs, webhook endpoint/events, signing secret presence, success/cancel URLs, accounting, refunds, support, and entitlement behavior.

## Verification

Commands/results:

- /home/st3ja/.local/bin/uv run --extra dev pytest tests/integration/test_stripe_api.py -q: 10 passed in 0.93s
- npm --prefix frontend run build: passed; Vite emitted the existing non-blocking chunk-size warning.
- python3 scripts/check_dev_environment.py: status OK
- Local HTTP route probe for backend health, home, pricing, pricing success, pricing cancel, and auth/register return: all HTTP 200
