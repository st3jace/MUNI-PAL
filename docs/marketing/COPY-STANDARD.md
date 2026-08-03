# Muni-Pal Copy Standard

**Status:** v0.1 DRAFT — pending Stephen approval (Linear ART-122)
**Owner:** Stephen (tone approver) · COS (author)
**Applies to:** every visitor-facing page and export on muni-pal.io. Acceptance
test for ART-127/ART-128 rewrites is the checklist in §7.
**Source library:** `MEGA/AREAS/BUSINESS/ACQUISITION` — $100M Offers, $100M
Leads, $100M Money Models course transcripts; $100M Branding Playbook; Proof
Checklist; ACQ Ads Handbook; Lead Nurture Playbook.
**Sibling policy:** LANGUAGE-POLICY.md governs *what we may claim*; this
standard governs *how we say it*. Both gates must pass.

---

## 1. Who we're talking to, and the one promise

The reader is a **school or facility CFO/ED/board member who has never issued a
bond** (or did once, painfully). They are not a muni professional. They fear
looking unprepared in front of advisors, boards, and lenders, and they don't
know what anything costs.

Every page serves one promise:

> **Know whether a bond is achievable for your facility — and what it will
> really cost — before you sit down with anyone.**

If a sentence doesn't move the reader toward that, cut it.

## 2. The value equation (the editing algorithm)

From $100M Offers — perceived value =
**(Dream outcome × Likelihood it works) ÷ (Time delay × Effort required).**
Apply it mechanically to every headline and card:

- **Dream outcome first.** Lead with what they GET ("See the rate deals like
  yours actually priced at"), never the mechanism ("Powered by AAA MMD base
  curve and corpus spreads").
- **Likelihood = proof.** Specific numbers beat adjectives: "866 actual
  municipal bond transactions" beats "comprehensive data." Every proof point
  needs a CLAIMS-REGISTER row (LANGUAGE-POLICY §4).
- **Time/effort down.** Say how fast and how little work: "Free. About 15
  minutes. No documents required to start."
- **Risk down.** Free assessment = the risk reversal. Say plainly what it
  isn't: "This is an educational readiness snapshot, not investment advice or
  a loan application."

## 3. Offer naming

Tools are named by the outcome, verb-first where possible. The tool card
formula: **[Outcome headline] + [what you get, one line] + [proof, one line] +
[one action]**.

| Tool | Mechanism-speak (kill) | Outcome-speak (use as directional model) |
|---|---|---|
| Readiness assessment | "AI-powered multi-dimensional readiness scoring" | "Find out if your facility is bond-ready — free, ~15 minutes" |
| Benchmark calculator | "Compare issuance against corpus spreads" | "See what deals like yours actually cost" |
| Credit spread monitor | "All-in cost of capital grid powered by MMD + spreads" | "What rating tiers pay: today's real borrowing costs by credit level" |
| COI benchmarking | "Cost-of-issuance benchmarking module" | "Every fee in a bond deal — and what's normal to pay" |
| Market intelligence | "Sector benchmark report from filings analysis" | "What good looks like in your sector — the numbers lenders expect" |

(Final names are set in ART-127/128 with Stephen; the column-3 pattern is the
standard, not the exact strings.)

## 4. Jargon policy

- **Allowed with a gloss on first use per page:** DSCR ("debt-service coverage —
  cash flow vs. annual payments"), days cash on hand, cost of issuance ("the
  fees to get a deal done"), spread ("the premium over the benchmark rate"),
  par, covenant, conduit issuer.
- **Banned on public surfaces:** corpus, crawler, sensing, extractor,
  archetype, playbook, pipeline, EMMA/MSRB (per LANGUAGE-POLICY §1), and any
  internal codename.
- **Sentence test:** if a charter-school CFO needs a glossary to parse the
  sentence, rewrite it. Reading level target: plain business English, short
  sentences, second person ("you," "your facility").

## 5. Proof rules (Proof Checklist, applied)

1. Specific beats general: "866 transactions" not "hundreds of deals."
2. Show the delta: "AA-rated systems borrow meaningfully cheaper than BBB —
   here's the observed gap" (exact figures only via CLAIMS-REGISTER).
3. Label honestly: observed vs. methodology-derived per LANGUAGE-POLICY §4 —
   honesty here IS a differentiator; say "based on our deal experience" proudly.
4. Proof near the claim: number + source description in the same block, not a
   footnote page.
5. No borrowed authority: no third-party brand names as implied endorsement.

## 6. Page architecture & CTA discipline

- **One CTA per page.** The free readiness assessment is the site-wide lead
  magnet ($100M Leads: the free, high-value first step). Tool pages may deep-link
  to their own tool as the primary action; every page's secondary path funnels to
  the assessment. Never two competing asks in one viewport.
- **Landing page order** (ART-127): outcome headline → who it's for → proof
  block → how it works (3 steps max) → what you get → risk reversal /
  what-this-isn't → CTA. Compliance language stays (see ART-127 note on the
  advisor-language hardening commits) but rendered in plain English.
- **Pricing page** (ART-128): anchor value before price — the cost of one
  mispriced deal or one wasted advisor engagement dwarfs the subscription; then
  the price, then what's included, then the free path.

## 7. The page checklist (acceptance test)

A page passes ART-127/128 review only if all ten hold:

1. Headline states the reader's outcome, not our mechanism.
2. A first-time CFO could say what this page offers in one sentence.
3. Every quantitative claim has a CLAIMS-REGISTER row (provenance class noted).
4. Observed vs. methodology-derived labeling is honest.
5. Zero banned jargon; allowed terms glossed on first use.
6. Zero EMMA/MSRB or internal-tooling references (LANGUAGE-POLICY grep passes).
7. Exactly one primary CTA; assessment funnel reachable.
8. Proof sits adjacent to the claim it supports.
9. Time/effort/cost of the next step is stated ("free," "~15 minutes").
10. What-this-isn't disclaimer present where results/analysis are shown.

## 8. Worked examples (from live copy)

**ToolsHub intro — before:**
> "Data-driven tools powered by the EMMA municipal bond corpus. Analyze…"

**After:**
> "Free tools that show you what municipal deals like yours actually look like —
> built from 866 real transactions in public disclosure filings."

**CreditSpreadMonitor empty state — before:**
> "Run the EMMA crawler on the {sector} sector to populate observed spreads…"

**After:**
> "Observed data for this sector is coming soon. In the meantime, the benchmark
> curve below shows typical borrowing costs by credit tier."

**Landing proof stat — before:**
> "866 — EMMA transactions analyzed"

**After:**
> "866 — real municipal bond transactions analyzed"
