# ART-127 — Healthcare CFO Landing Page Rewrite (Copy Deck)

**Status:** DRAFT for Stephen's tone approval — copy deck only, no code changed
**Page:** `frontend/src/pages/tools/HealthcareCFOLanding.tsx`
**Governing docs:** COPY-STANDARD.md v1.0 (ART-122) + LANGUAGE-POLICY.md v1.0 (ART-120)
**Author:** COS · **Date:** 2026-08-03

---

## Proposed page order (COPY-STANDARD §6)

The current page runs: hero → value props → stats → pricing path → cost of
inaction → timeline → audience filter → secondary CTAs → Monte Carlo → CTA →
footer. The §6 landing order is different. Proposed mapping:

| §6 slot | Built from (current section) |
|---|---|
| 1. Outcome headline | Hero (~L119) |
| 2. Who it's for | Audience Filter (~L353) — **moves up** |
| 3. Proof block | Social Proof Stats (~L216) + "why check early" note (from Cost of Inaction, ~L285) |
| 4. How it works (≤3 steps) | Engagement Path (~L240) + Timeline (~L315) — **merged, de-priced** |
| 5. What you get | Value Props (~L192) + Platform Preview (~L441) + Secondary cards (~L401) — **merged** |
| 6. Risk reversal / what-this-isn't | New short block + footer compliance language surfaced |
| 7. Single CTA | Bottom CTA (~L508), retargeted to the free readiness assessment |

Sections below follow the **current** page order; each notes where it lands in
the new order.

---

## 1. Hero — eyebrow, H1, subhead (`<section>` HERO, ~L137–155)

**CURRENT**
> Eyebrow: "Healthcare Bond Intelligence"
>
> H1: "Every basis point matters. Now you can prove it."
>
> Subhead: "Muni-Pal's Healthcare Market Intelligence Report benchmarks your
> deal against 866 actual municipal bond transactions — showing you the real
> spread between good deals and great ones. Know your true cost of capital
> before the term sheet hits your desk."

**PROPOSED**
> Eyebrow: "For healthcare CFOs planning a first bond issue"
>
> H1: "Find out if your hospital is bond-ready — and what borrowing will really
> cost — before you sit down with anyone."
>
> Subhead: "Muni-Pal shows you what municipal deals like yours actually looked
> like, built from 866 real municipal bond transactions in public disclosure
> filings. See where you stand — for free, in about 15 minutes — before your
> first advisor meeting."

*Rationale:* §1 — the headline must carry the one promise; "every basis point
matters" assumes a reader who already thinks in basis points, and "prove it" is
our mechanism, not their outcome. Proof (866) stays adjacent to the claim (§5.4).

---

## 2. Hero — CTA buttons (~L157–178)

**CURRENT**
> Primary: "Start Your Readiness Scan"
>
> Second button: "Get Your Free Market Intelligence Report"

**PROPOSED**
> Primary (only button): "Start Your Free Readiness Assessment"
>
> Microcopy under button: "Free. About 15 minutes. No documents required to start."
>
> (The Market Intelligence Report becomes a text mention inside "What you get,"
> not a competing button.)

*Rationale:* §6 — one CTA per page, never two competing asks in one viewport;
§2 — time/effort/cost of the next step stated.

---

## 3. Hero — PreviewCard mock (function `PreviewCard`, ~L66–108)

**CURRENT**
> "Bond Readiness Score — 72/100 · DSCR 1.45x · Rating A- · Coverage 2.1x ·
> Risk Score Low · 3 of 6 dimensions ready for advisor review"

**PROPOSED**
> Keep the card, add a visible caption: "Sample assessment — illustrative
> numbers, not a real facility."
>
> Change "DSCR" tile label to "DSCR (coverage)" and keep the line "3 of 6
> readiness dimensions ready for advisor review."

*Rationale:* §7.4 / LANGUAGE-POLICY §4 — illustrative numbers must not read as
observed data; the label makes the honesty explicit. (DSCR gets its full gloss
at first body-copy use, section 5 below.)

---

## 4. Value prop cards (`VALUE_PROPS`, ~L30–46, rendered ~L192) — merges into "What you get"

**CURRENT**
> Card 1: "Know what 'good' looks like — See the exact DSCR (gross revenue
> pledge, healthcare-adjusted), payer mix, days cash on hand, and pledge
> structures that separate AA-rated healthcare systems from BBB — drawn from
> real public-disclosure data, not industry averages."
>
> Card 2: "Understand cost context before advisor review — Corpus-calibrated
> cost-of-capital context by rating tier. Not a vague market-rate placeholder —
> evidence you can use to prepare better questions for your registered advisor
> and deal team."
>
> Card 3: "Understand where readiness gaps emerge — The 5 risk categories
> healthcare issuers often under-document — and examples of evidence that
> strengthened comparable credits."

**PROPOSED**
> Card 1: "Know what 'good' looks like. See the debt-service coverage (DSCR —
> your cash flow vs. your annual payments), days cash on hand, and payer mix
> that separate highly rated hospitals from the rest — drawn from real
> public disclosure filings, not industry averages."
>
> Card 2: "Walk into advisor meetings with context. See typical borrowing
> costs by credit rating, so you can ask sharper questions of your registered
> advisor and deal team — instead of hearing every number for the first time."
>
> Card 3: "See your gaps before a lender does. The readiness dimensions
> hospitals most often under-document — and the kind of evidence that
> strengthened comparable borrowers."

*Rationale:* §4 — "corpus-calibrated" is banned jargon and "gross revenue
pledge, healthcare-adjusted" fails the sentence test for a first-time CFO;
DSCR glossed on first use. (Card 3's "5 risk categories" conflicts with the
"6 dimensions" used elsewhere — see flag F7; proposed copy avoids the count.)

---

## 5. Social proof stats bar (~L216–235) — becomes the §6 proof block

**CURRENT**
> "866 — municipal bond transactions analyzed · 3.20x — Median healthcare DSCR
> (gross revenue pledge basis) · 5 — Risk categories scored · 1,318 — Financial
> reports in corpus"

**PROPOSED**
> "866 — real municipal bond transactions analyzed"
>
> "6 — readiness dimensions scored on every assessment"
>
> "15 min — to a first readiness read. Free."
>
> (Drop "3.20x median DSCR" and "1,318 financial reports in corpus" pending
> claims-register review — see flags F1 and F2. If the register clears them,
> they return as: "3.20x — median coverage (DSCR) observed across analyzed
> healthcare deals" and "1,318 — public financial reports reviewed.")

*Rationale:* §5.1/§7.3 — specific proof stays, but every number needs a
CLAIMS-REGISTER row and "in corpus" is banned wording (§4); the two
legacy-provenance figures come out until the register clears them.

---

## 6. Engagement Path (`ENGAGEMENT_PATH`, ~L48–54, rendered ~L240) — rebuilt as "How it works," pricing moves to ART-128

**CURRENT**
> "The Bond Readiness Path — From free benchmarks to deal-ready in four steps.
> Start with the data — escalate only when you're confident in the opportunity."
>
> Steps: "1. Market Intelligence Report — Free — Sector benchmarks — DSCR, cost
> context, risk profile, Pareto framework · 2. Readiness Scan — Free —
> Automated pre-screen — sector fit, deal size, top 3 gaps · 3. Bond Readiness
> Diagnostic — $15K–$25K — Full score + gap analysis + critical path to close ·
> 4. Standard Engagement — $40K–$50K — Diagnostic + readiness coordination +
> cost-of-issuance planning support · 5. Bond Readiness Accelerator — $75K+ —
> Expanded readiness support — gap remediation, benchmarking, and
> advisor-review preparation"

**PROPOSED**
> "How it works
>
> 1. Answer questions about your facility. Free, about 15 minutes, no
> documents required to start.
>
> 2. See where you stand. A readiness score across 6 dimensions, benchmarked
> against 866 real municipal bond transactions — plus your top gaps.
>
> 3. Take it to your advisors. You get a report you can put in front of your
> board and your registered advisor, with the questions worth asking."
>
> (The paid Diagnostic / Engagement / Accelerator tiers move to the pricing
> page per ART-128 — not deleted, relocated. A single quiet line may remain:
> "Deeper paid engagements exist when you're ready — start free.")

*Rationale:* §6 — "how it works" is capped at 3 steps and the landing page
carries one ask; a five-step menu with prices is a pricing-page job (§6,
ART-128 anchor-value-first). Also fixes the "four steps" text over a
five-step list. "Pareto framework" is internal-speak (§4 sentence test).

---

## 7. Cost of Inaction (~L285–310) — becomes a short "why check early" note in the proof block

**CURRENT**
> "The Cost of Inaction — The difference between an A-rated and BBB-rated
> issuance costs $27M+ over 25 years on a $75M deal. The Accelerator helps you
> document your way for registered-advisor review — for less than 0.04% of
> deal size. — Based on observed AA vs. BBB spread differentials in public
> healthcare revenue bond disclosures (gross revenue pledge basis)."

**PROPOSED**
> "Why check early: your credit story is worth real money. In public
> healthcare bond filings, higher-rated hospitals consistently borrow at lower
> rates than lower-rated ones — and that gap (the 'spread,' the premium over
> the benchmark rate) compounds every year for the 25–30 year life of a deal.
> The cheapest time to close a readiness gap is before anyone prices your deal."
>
> (The $27M+/25-year/$75M figure and the "less than 0.04% of deal size" line
> come out pending claims-register review — flags F3 and F4. If the register
> re-derives the delta from clean provenance, restore one exact figure with
> its source description in the same block.)

*Rationale:* §5.2 — show the delta, but "exact figures only via
CLAIMS-REGISTER"; the $27M derivation traces to quarantined legacy provenance
(LANGUAGE-POLICY §3), and 0.04% depends on pricing that no longer lives on
this page.

---

## 8. When to Engage timeline (~L315–348) — folds into "How it works" as one line

**CURRENT**
> "When to Engage — A typical healthcare bond transaction takes 6–9 months.
> Here's how the Bond Readiness Path maps to your deal timeline."
> (Bars: Discovery / Diagnostic / Preparation / Execution)

**PROPOSED**
> One line under "How it works": "A typical healthcare bond deal takes 6–9
> months from first conversation to closing — which is why the free
> assessment is worth doing before you think you need it."
>
> (Keep the timeline graphic only if it survives the merge visually; the
> four-phase bar chart is optional decoration, not load-bearing copy.)

*Rationale:* §2 — the timeline's job is urgency (time delay), which one plain
sentence does without adding a second section between the reader and the CTA.
(6–9 months needs a register row — flag F5.)

---

## 9. Audience filter (~L353–396) — moves up to slot 2, copy nearly keeps

**CURRENT**
> "Who this is for — and who it isn't"
>
> Built for: "Healthcare CFOs and finance directors planning a bond issuance ·
> Hospital systems evaluating capital structure options · Deals above $10M in
> total issuance size"
>
> Not designed for: "Sub-$10M deal sizes · Non-healthcare municipal issuers ·
> General financial advice seekers"

**PROPOSED**
> "Who this is for — and who it isn't
>
> Built for: Healthcare CFOs and finance directors thinking about a bond for
> the first time · Hospital systems weighing how to fund a major project ·
> Deals above $10M
>
> Not for: Deals under $10M · Issuers outside healthcare · Anyone looking for
> personal investment advice"

*Rationale:* §1/§4 — this section already does the right job; the rewrite
only swaps "evaluating capital structure options" and "general financial
advice seekers" for plainer second-person-adjacent phrasing and moves the
section up to the §6 who-it's-for slot.

---

## 10. Secondary trust CTA cards (~L401–436) — demoted into "What you get"

**CURRENT**
> Card A: "View a Sample MIR Report — See the exact benchmarks, risk scoring,
> and pricing data a healthcare CFO receives — before you request your own."
>
> Card B: "Compare Risk Profiles by Rating Tier — How does your system's risk
> profile stack up against AA, A, and BBB-rated peers? See the gap analysis
> framework."

**PROPOSED**
> Fold both into the "What you get" list as plain text links (not button-styled
> cards):
>
> "What you get with the free assessment: a readiness score across 6
> dimensions · sector benchmarks from 866 real municipal bond transactions ·
> your top gaps, with examples of what stronger borrowers documented · a
> report you can hand to your board and registered advisor. Want to see one
> first? View a sample market report."
>
> ("MIR" never appears — the acronym is internal shorthand.)

*Rationale:* §6 — two more boxed asks compete with the single CTA; §4 —
unglossed acronyms ("MIR") fail the sentence test.

---

## 11. Platform preview — Monte Carlo (~L441–503) — replaced

**CURRENT**
> "See the Platform in Action — Risk Analysis — Monte Carlo Simulation — 1,000
> simulations over 25 years with 10.00% revenue volatility and 3.00% expense
> volatility." Stat tiles: "P(VR BREACH) 4.10% · NEGATIVE NET INCOME 41.34% ·
> VaR (5TH) -45.52% · EXPECTED COVERAGE RATIO -81.07%" plus an
> IRR/Equity-Multiple/Min-DSCR percentile table.

**PROPOSED**
> "See what the analysis looks like
>
> Before your deal is ever priced, you can stress-test it: what happens to
> your coverage if revenue dips, expenses run hot, or both. The platform runs
> your numbers through hundreds of scenarios and shows you the range — best
> case, worst case, and most likely — in plain terms.
>
> Caption under any screenshot: 'Illustrative example using sample inputs —
> not a prediction for your facility.'"
>
> (The current stat tiles — VaR, P(VR BREACH), -81.07% expected coverage —
> come out: unglossed quant jargon, and demo numbers rendered as if real.
> Flag F6.)

*Rationale:* §2/§7.10 — lead with the dream outcome ("know your range before
pricing"), not the mechanism, and results shown require the what-this-isn't
label; a wall of unexplained negative percentages fails the §4 sentence test
and reads as either alarming or fake.

---

## 12. Bottom CTA (~L508–528)

**CURRENT**
> "Get Your Free Market Intelligence Report — No login required. No sales
> call. Just the data your advisors charge $25K to compile. — Start Now —
> It's Free"

**PROPOSED**
> "Find out if your hospital is bond-ready.
>
> Free. About 15 minutes. No documents required to start. No sales call.
> This is an educational readiness snapshot — not investment advice and not a
> loan application.
>
> Button: Start Your Free Readiness Assessment"

*Rationale:* §6/§2 — the site-wide lead magnet is the readiness assessment,
and the risk reversal ("what it isn't") belongs at the point of action; the
"$25K advisors charge" line is an unsupported claim that also disparages the
advisors the rest of the page tells the reader to work with (flag F8, §5.5
no-borrowed-authority adjacent).

---

## 13. Footer compliance (~L533–548) — plain-Englished, substance preserved

**CURRENT**
> "Muni-Pal — A Launch Shop product. Built by Innovation Factory."
>
> "Bond Readiness Accelerator is an educational and analytical service. It
> does not constitute municipal advisory services as defined under Section 15B
> of the Securities Exchange Act."

**PROPOSED**
> "Muni-Pal — A Launch Shop product. Built by Innovation Factory.
>
> Muni-Pal is an educational and analytical service. We help you understand
> your numbers and prepare for conversations with your own registered
> advisors — we are not your municipal advisor, and nothing on this site is
> municipal advisory services as defined under Section 15B of the Securities
> Exchange Act, investment advice, or an offer to arrange financing. Bond
> decisions belong with your board and your licensed professionals."
>
> (Scope widened from "Bond Readiness Accelerator" to the whole service since
> the Accelerator name leaves this page. No G-42 language added or removed,
> per LANGUAGE-POLICY §5 — that stays a counsel question for Stephen.)

*Rationale:* §6 — compliance language stays but rendered in plain English;
the legal 15B sentence is preserved verbatim in substance, with a
plain-English frame a first-time CFO can actually parse.

---

## Claims-register flags (for ART-129)

| # | Claim (current page) | Issue | Proposed handling |
|---|---|---|---|
| F1 | "3.20x median healthcare DSCR (gross revenue pledge basis)" | Legacy-corpus provenance (LANGUAGE-POLICY §3 Class D quarantine); needs re-derivation or methodology-derived label | Removed from deck; restore only with register row |
| F2 | "1,318 financial reports in corpus" | "corpus" is banned wording; count needs provenance row | Removed; restore as "public financial reports reviewed" if cleared |
| F3 | "$27M+ over 25 years on a $75M deal (A vs. BBB)" | Derived exact figure; §5.2 requires register backing | Replaced with qualitative delta; restore one exact figure if re-derived |
| F4 | "less than 0.04% of deal size" | Depends on Accelerator pricing leaving this page; unregistered | Removed (pricing-page material, ART-128) |
| F5 | "A typical healthcare bond transaction takes 6–9 months" | Retained — market-general, still needs a register row per §7.3 | Kept with row required |
| F6 | Monte Carlo tiles (4.10%, 41.34%, -45.52%, -81.07%, IRR table) | Demo/sample numbers rendered as observed results | Removed; any screenshot labeled illustrative |
| F7 | "5 risk categories" vs "6 dimensions" (cards, stats, preview card) | Internal inconsistency; task brief and preview card say 6 | Deck standardizes on "6 readiness dimensions" — Stephen to confirm canonical count |
| F8 | "the data your advisors charge $25K to compile" | Unsupported third-party pricing claim | Removed outright, no restore path proposed |
| F9 | "866 real municipal bond transactions" | Retained (canonical proof stat, COPY-STANDARD §8 worked example) — still needs its register row | Kept with row required |
| F10 | PreviewCard sample stats (72/100, 1.45x, A-, 2.1x) | Illustrative numbers unlabeled | Kept with "Sample — illustrative" caption |

---

## §7 checklist self-assessment (proposed copy)

| # | Item | Verdict | Evidence |
|---|---|---|---|
| 1 | Headline states reader's outcome, not mechanism | **Pass** | "bond-ready…before you sit down with anyone" |
| 2 | First-time CFO can state the offer in one sentence | **Pass** | "Free 15-minute check of whether my hospital can do a bond" |
| 3 | Every quantitative claim has a CLAIMS-REGISTER row | **Conditional pass** | Retained numbers (866, 6, $10M, 6–9 mo, 15 min) listed F5/F9 — rows must exist before ship |
| 4 | Observed vs. methodology-derived labeled honestly | **Pass** | Illustrative captions added; unlabeled legacy stats removed |
| 5 | Zero banned jargon; allowed terms glossed | **Pass** | "corpus" ×2 removed; DSCR/spread glossed on first use |
| 6 | Zero EMMA/MSRB or internal-tooling references | **Pass** | grep-clean (none in current or proposed copy; "Pareto framework"/"MIR" removed) |
| 7 | Exactly one primary CTA; assessment funnel reachable | **Pass** | Single "Start Your Free Readiness Assessment"; sample-report demoted to text link |
| 8 | Proof adjacent to the claim it supports | **Pass** | 866 sits inside hero subhead and step 2, not a stats island alone |
| 9 | Time/effort/cost of next step stated | **Pass** | "Free. About 15 minutes. No documents required to start." (hero + bottom CTA) |
| 10 | What-this-isn't disclaimer where results shown | **Pass** | Bottom-CTA snapshot disclaimer + illustrative captions + plain-English footer |

Item 3 is the only gate: this deck ships only after the F1–F10 rows land in
the claims register (ART-129) and Arthur certifies the retained numbers.
