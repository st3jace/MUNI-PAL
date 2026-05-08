# ELA-58 BFMS Launch: Gstack Product / Launch Critique

Date: 2026-05-08T20:05:03.232994+00:00

## Scope and evidence

This critique pressure-tests the BFMS launch narrative, wedge, and pilot readiness after the dogfood sequence. It covers the public site, pricing, Healthcare scenario, Housing scenario, BFMS dashboard findings, and ELA-59 compliance-language QA.

Evidence used:
- Public site/pricing HTTP and link evidence: dogfood-output/ela58/audit/public_site_summary.json and dogfood-output/ela58/audit/public_link_check.json
- Prior launch-readiness excerpts: dogfood-output/ela58/audit/prior_launch_evidence_excerpts.md
- ELA-59 compliance QA: docs/launch-readiness/ELA-59-advisor-compliance-language-qa.md and dogfood-output/ela59/
- Healthcare walkthrough refresh: docs/launch-readiness/ELA-52_healthcare_pilot_walkthrough_refresh_after_ELA-92.md
- Housing walkthrough refresh: docs/launch-readiness/ELA-53_housing_pilot_walkthrough_refresh_after_ELA-92.md
- Dashboard/platform landing review: docs/launch-readiness/ELA-51_dashboard_platform_landing_review.md
- Public/pricing/Stripe launch passes: docs/launch-readiness/ELA49_PUBLIC_SITE_PRICING_DOGFOOD.md, docs/launch-readiness/ELA50_STRIPE_PAYMENT_SMOKE_TEST.md, docs/launch-readiness/ELA60_CURRENT_HEAD_ELA49_50_RERUN.md

Environment distinction:
- Deployed public site routes returned HTTP 200 for /, /pricing, /tools/readiness, /tools/market-intelligence, /tools/benchmark, and /tools/credit-spreads.
- Current repo is ahead of origin/master by 33 commits (git rev-list --left-right --count origin/master...HEAD returned 0 / 33), so deployed public evidence is production evidence only; it is not proof that current HEAD is deployed.
- Built-in browser/Windows Chrome headless evidence has been unreliable in this WSL/Windows setup; HTTP, prior screenshots, and current-source artifacts are the durable evidence base.

## Gstack-style read

The product has a real wedge: issuer/operator teams preparing for a municipal financing need to understand whether they have the evidence package, risk language, and advisor-ready handoff discipline to enter professional review without wasting months. Healthcare is currently the strongest wedge because the recent sector-profile refresh removed the most damaging cross-sector taxonomy leakage and gives a credible CFO/operator path.

The biggest launch risk is not core platform value. The biggest risk is coherence at the public boundary: production copy, pricing/payment expectations, Housing scope, and demo/dashboard readiness all need to say the same thing. Muni-Pal should not launch as a generic AI bond advisor. It should launch as a narrow readiness and handoff layer that helps Healthcare issuers/operators organize evidence before registered advisor/counsel/deal-team review.

## Top 5 launch blockers

1. Production is stale relative to current source.
   - Evidence: ELA-59 found deployed public site/pricing still serving stale "what it costs" / "TIC estimates" wording after current source was patched.
   - Risk: public launch would expose the riskiest compliance/positioning language even though source is fixed.
   - Required action: redeploy current HEAD, then re-run ELA-59/ELA-58 public-site evidence before any public launch claim.

2. Public launch scope is Healthcare-ready, not Healthcare-plus-Housing-ready.
   - Evidence: Healthcare refresh passes sector-taxonomy and launch-safety checks after ELA-92; Housing is strategically important but public site remains Healthcare-centric and Housing has not been given a separate public positioning surface.
   - Risk: claiming a dual-sector public launch overpromises and blurs the wedge.
   - Required action: launch Healthcare publicly; keep Housing invite-only/direct-pilot unless a Housing landing/readiness route is separately reviewed.

3. Pricing/payment readiness must stay conditional until the production checkout path is re-smoked after redeploy.
   - Evidence: pricing/Stripe launch work exists, but static route and CTA evidence is not the same as live checkout/webhook/entitlement readiness.
   - Risk: public paid CTA creates support/accounting/entitlement exposure before the handoff loop is operationally stable.
   - Required action: keep payment gated or manually confirmed until a safe Stripe/live-mode checklist is complete after deploy.

4. Dashboard/demo readiness is dependent on seeded current-product evidence.
   - Evidence: prior dashboard work showed the platform shell can be reachable while project lists are empty; later launch work seeded Healthcare/Housing paths and rechecked them.
   - Risk: sales/demo launch falls flat if the dashboard opens empty or shows non-sector-specific content.
   - Required action: use seeded Healthcare demo as the controlled-launch default; do not rely on an empty dashboard as proof of product readiness.

5. Compliance-safe source does not equal compliance-safe market posture.
   - Evidence: ELA-59 fixed current-source language, but the public boundary still needs deploy/recheck and the narrative must consistently avoid advisor replacement or pricing/issuance advice.
   - Risk: a few stale public strings can undermine the entire advisory-boundary posture.
   - Required action: keep the launch narrative anchored on readiness, evidence organization, and registered-advisor/counsel review support.

## Top 5 positioning and product clarity improvements

1. Lead with one wedge: Healthcare bond readiness before advisor/deal-team review.
   - Current product strength is not "AI municipal finance for everyone." It is faster evidence organization, gap identification, and advisor-ready handoff for Healthcare operators/CFOs preparing a financing.

2. Separate public prospect flow from BFMS platform flow.
   - Public pages should qualify and educate. BFMS dashboard should demonstrate workflow depth. Do not make the public user infer how a free scan becomes a controlled pilot/handoff.

3. Make Housing explicitly invite-only unless/until it has its own public narrative.
   - Housing is a good secondary sector, but public launch should not imply full Housing self-serve readiness without a Housing page, Housing-specific examples, and a separate pass.

4. Clarify pricing around deliverables and next step, not just price points.
   - Pricing should answer: what artifact do I receive, who reviews it, what does Muni-Pal not do, when does a registered advisor/counsel enter, and what happens after submission?

5. Show proof artifacts, not only claims.
   - The strongest launch assets would be anonymized screenshots/exports of a readiness score, top gaps, provenance-aware handoff pack, and advisor/counsel boundary language. This turns the pitch from promise to workflow evidence.

## Launch decision

Decision: proceed with a controlled Healthcare launch with conditions; do not proceed with broad public Healthcare-plus-Housing launch yet.

Launch conditions:
1. Redeploy current HEAD containing ELA-59 compliance copy changes.
2. Re-run public site/pricing compliance QA after deploy and confirm stale TIC/cost wording is gone.
3. Use Healthcare as the public wedge and default demo path.
4. Keep Housing as invite-only/direct-pilot until a Housing-specific public surface is reviewed.
5. Keep payment/checkout as gated/manual or re-smoked in safe mode before relying on public paid conversion.
6. Demo only with seeded current-product Healthcare data, not an empty dashboard.

## Linear follow-up policy

Avoid roadmap sprawl. Only blocker-level follow-up should be converted immediately:
- Production redeploy and post-deploy public-site compliance recheck for ELA-59/ELA-58.

Other improvements should be folded into ELA-48 launch readiness synthesis unless they become blockers after redeploy:
- Housing public launch surface.
- Pricing deliverable clarity.
- Proof-artifact/sample-output polish.
- Controlled-launch demo script.

## Bottom line

Muni-Pal is close enough for a controlled Healthcare launch if current source is deployed and rechecked. It is not yet ready for an unqualified broad public launch or a public Housing launch. The right move is narrow, advisor-safe, evidence-backed: Healthcare readiness scan to controlled pilot to advisor-ready handoff, with registered advisors/counsel clearly remaining in the professional decision loop.
