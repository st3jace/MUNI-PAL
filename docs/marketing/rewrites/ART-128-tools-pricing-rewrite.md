# ART-128 Copy Deck — Tool Pages & Pricing Rewrite

**Status:** DRAFT for Stephen's tone approval — no code has been changed.
**Author:** COS · **Date:** 2026-08-03
**Governing docs:** COPY-STANDARD.md v1.0 (ART-122) · LANGUAGE-POLICY.md v1.0 (ART-120)
**Scope:** `frontend/src/pages/tools/` — ToolsHub, PricingPage, MarketIntelligence,
HealthcareMIRContent, BenchmarkCalculator, CreditSpreadMonitor, CoiBenchmarking,
ReportExport, ReadinessAssess, HealthcareReadiness.
**Format:** one section per page; each string shows file + approx. line, CURRENT
(quoted from source), PROPOSED. Flags are marked ⚑ and collected in §10.

---

## 0. Decisions Stephen needs to make (read this first)

1. **⚑ Pilot Navigation card (ToolsHub ~L47–53).** This card exposes internal ops
   language ("BFMS project creation gate," "pre-pilot checks," "advisor-safe
   handoff boundaries") on the public grid. **Recommendation: remove the card from
   the public grid entirely.** A fallback rewrite is provided in §1 if it must stay.
2. **⚑ COI Benchmarking is not a real page.** `CoiBenchmarking.tsx` is a 3-line
   re-export of `BenchmarkCalculator`. The ToolsHub card promises "line-item
   cost-of-issuance comparison" but routes to the general benchmark form (which
   shows a COI estimate block only for healthcare). Proposed card copy below is
   written to match what the page actually delivers, but the honest fix is either
   a dedicated page or merging the card into Deal Benchmarks.
3. **⚑ "10 minutes" vs "~15 minutes."** Live pages say "10 minutes"
   (MarketIntelligence CTA, HealthcareReadiness subtitle); COPY-STANDARD §2's
   worked example says "~15 minutes." This deck standardizes on **"about 10
   minutes"** (the number already published — no new claim). Confirm or flip.
4. **⚑ "AAA MMD."** MMD (Municipal Market Data) is a third-party brand.
   LANGUAGE-POLICY §1 only bans EMMA/MSRB, but COPY-STANDARD §5 bans borrowed
   authority via third-party brand names. This deck replaces every visible "MMD"
   with **"the AAA benchmark curve."** Confirm with counsel alongside the G-42
   question.
5. **⚑ Assessment naming.** The same tool is called "Bond Readiness Assessment,"
   "Bond Readiness Scan," "Readiness Scan," and "Readiness Assessment" across
   pages. This deck standardizes on **"Bond Readiness Assessment"** ("free
   readiness assessment" in running text).
6. **⚑ ROI numbers on PricingPage** ($150K–$500K, $27M+, 0.1%) are kept per the
   "reuse existing numbers only" constraint but **all three need CLAIMS-REGISTER
   rows before this ships** — see §10.

---

## 1. ToolsHub.tsx — the tool-card grid

### 1.1 Page header

**L62 — h1**
- CURRENT: "Sensing Tools"
- PROPOSED: "Free Bond Tools"
- Why: "sensing" is banned internal jargon (COPY-STANDARD §4). "Free" states the
  cost of the next step up front (§7 item 9).

**L63–68 — intro paragraph**
- CURRENT: "Data-driven tools powered by our municipal bond corpus, built from
  public disclosure filings. Analyze sector benchmarks, compare your issuance,
  and assess your bond readiness."
- PROPOSED: "Free tools that show you what municipal deals like yours actually
  look like — built from 866 real transactions in public disclosure filings.
  See what your sector pays, compare your deal, and find out if you're
  bond-ready before you sit down with anyone."
- Why: "corpus" is banned; this is the COPY-STANDARD §8 approved worked example,
  extended with the site promise (§1). ⚑ "866" needs its CLAIMS-REGISTER row
  (legacy-corpus quarantine, ART-129).

### 1.2 Full proposed card set (L5–54)

Card formula per COPY-STANDARD §3: outcome headline + what you get + proof + one
action. The hover CTA "Open tool" (L92) is replaced per-card below.

**Card 1 — Bond Readiness Assessment** (`/tools/readiness`) — *make this the
visually primary card (first position, accent border). It is the site-wide lead
magnet and every other page funnels here.*
- Name: **Bond Readiness Assessment**
- Description: "Find out if your facility is bond-ready — free, about 10
  minutes. Answer plain-English questions and get a scored action plan: your
  top gaps, what each one costs you, and what to fix first."
- CTA: **"Check my readiness"**
- CURRENT (L24–26, for reference): "Healthcare sub-sector scoring (Hospital,
  Senior Living, FQHC) with 177-item assessment, COI gap estimates, and
  timeline compression analysis."
- Note: the 177-item framework moves to proof position if wanted: "Built on a
  177-item readiness framework from real deals." ⚑ register row for 177.

**Card 2 — Deal Benchmarks** (`/tools/benchmark`)
- Name: **Deal Benchmarks** (was "Benchmarking Calculator")
- Description: "See what deals like yours actually cost. Enter your size,
  state, and expected rating, and compare against real municipal bond
  transactions — the spread you can expect (the premium over the benchmark
  rate), typical structures, and your closest peers."
- CTA: **"Compare my deal"**
- CURRENT (L16–17): "Compare your prospective issuance against sector peers.
  Get spread estimates, structural norms, and risk context."

**Card 3 — Today's Borrowing Costs** (`/tools/credit-spreads`)
- Name: **Today's Borrowing Costs** (was "Credit Spread Monitor")
- Description: "What each rating tier pays to borrow right now. Current
  tax-exempt yield curves and the all-in cost of a deal by credit level —
  built from the AAA benchmark curve and real observed trades."
- CTA: **"See today's costs"**
- CURRENT (L40–41): "Live yield curves, all-in cost of capital grid, and issuer
  channel comparison. Powered by the AAA benchmark curve and observed spreads
  from our municipal bond corpus."
- Why: kills "corpus" and mechanism-first framing; matches §3 column-3 model
  ("What rating tiers pay: today's real borrowing costs by credit level").

**Card 4 — Cost-of-Issuance Benchmarks** (`/tools/coi-benchmarking`)
- Name: **Cost-of-Issuance Benchmarks** (was "COI Benchmarking")
- Description: "Every fee in a bond deal — and what's normal to pay. Cost of
  issuance (the fees to get a deal done) benchmarked against real healthcare
  deals, sized to your deal."
- CTA: **"See what's normal"**
- CURRENT (L32–33): "Line-item cost-of-issuance comparison across healthcare
  sub-sectors. See COI impact, lead times, and agent displacement value per
  item."
- ⚑ See Decision 2: proposed copy is scoped down to what the page actually
  shows (a COI estimate on the benchmark results). "Agent displacement value"
  is internal framing — removed.

**Card 5 — Sector Market Report** (`/tools/market-intelligence`)
- Name: **Sector Market Report** (was "Market Intelligence")
- Description: "What good looks like in your sector — the financial profile,
  ratings, deal structures, and borrowing costs lenders expect, built from 866
  real municipal bond transactions."
- CTA: **"Read the report"**
- CURRENT (L8–9): "Comprehensive sector benchmark report covering deal
  structures, ratings, financial metrics, risk factors, and secondary market
  activity."
- (If Stephen prefers keeping the "Market Intelligence" name for continuity,
  the description and CTA stand as-is.)

**Card 6 — Pilot Navigation** (`/tools/pilot-navigation`)
- CURRENT (L48–50): "Lead capture to pilot qualification path, BFMS project
  creation gate, pre-pilot checks, and advisor-safe handoff boundaries."
- PROPOSED: **Remove from the public grid** (Decision 1). Fallback if it must
  stay — Name: "Work With Us"; Description: "Thinking about a deeper
  engagement? See how a pilot works: what we check first, what you get, and
  where your registered advisor stays in charge."; CTA: "See how it works".

### 1.3 Export CTA block (L109–114)

- CURRENT (L109–110): "Export Combined Report" / "{n} of 4 sections ready —
  download as PDF"
- PROPOSED: "Download Your Combined Report" / "{n} of 4 sections ready — get
  everything as one PDF, free"
- Why: states cost; keeps it a secondary, contextual action (only shows after
  tool use), preserving the one-primary-CTA rule.

### 1.4 "How it works" block (L121–156)

- L122 CURRENT: "How it works" — KEEP.
- Step 1 (L129–130) CURRENT: "Review sector benchmarks from the Market
  Intelligence report."
  PROPOSED: "See what good looks like in your sector — ratings, financials,
  and costs from real deals."
- Step 2 (L136–137) CURRENT: "Benchmark your specific issuance against corpus
  peers."
  PROPOSED: "Compare your specific deal against its closest real-world peers."
  (kills "corpus")
- Step 3 (L144–145) CURRENT: "Complete the readiness assessment for a scored
  action plan."
  PROPOSED: "Take the free readiness assessment and get a scored action plan
  — about 10 minutes."
- Step 4 (L152–153) CURRENT: "View live credit spreads and all-in cost of
  capital by issuer channel."
  PROPOSED: "See what borrowing costs today at your credit level — all fees
  included."

---

## 2. PricingPage.tsx

Structural note (COPY-STANDARD §6): reorder sections to **value anchor → price →
what's included → free path**. Concretely: move the "Why This Pays for Itself"
section (currently L530–544, after the estimator) to directly beneath the page
header, before the tier cards. All pricing NUMBERS are unchanged.

### 2.1 Header

**L233–235 — kicker** CURRENT: "Pricing & Plans" — KEEP.

**L237–239 — h1**
- CURRENT: "Choose the right level for your bond journey"
- PROPOSED: "The most expensive part of a bond deal is what you don't know"
- Why: value anchor leads (§6); outcome/stakes, not navigation language.

**L240–243 — subtitle**
- CURRENT: "Start free with sensing tools. Subscribe for ongoing readiness
  workspace access. Or scope a registered-advisor-review support engagement
  for pre-issuance preparation."
- PROPOSED: "Every tool here exists to make sure you never overpay for fees,
  rates, or wasted advisor hours. Start free — no login. Subscribe when you
  want an ongoing readiness workspace. Scope a per-project engagement when a
  real deal is on the table."
- Why: "sensing" banned; "registered-advisor-review support engagement" fails
  the sentence test.

### 2.2 Value anchor section (moved up; currently L530–544)

**L533 — heading** CURRENT: "Why This Pays for Itself" — KEEP (moved above the
tier cards).

**L535–540 — body**
- CURRENT: "Repeat issuers who benchmark costs save $150K–$500K on a $100M deal
  through better underwriter negotiation alone. A one-tier rating improvement
  saves $27M+ over 25 years. The Per-Project engagement typically costs less
  than 0.1% of deal size."
- PROPOSED: "Issuers who benchmark their costs before negotiating have saved
  $150K–$500K on a $100M deal on underwriting alone. A one-tier rating
  improvement is worth $27M+ over 25 years of debt service. Against numbers
  like that, the Per-Project engagement typically runs under 0.1% of deal
  size — and the readiness assessment that starts the whole path is free."
- ⚑ All three figures need CLAIMS-REGISTER rows (see §10, items R1–R3). Do not
  ship this section until they exist or the figures are relabeled/removed.

**L541–543 — attribution line**
- CURRENT: "Based on observed cost-of-issuance and spread differentials in
  public healthcare revenue bond disclosures."
- PROPOSED: "Based on cost-of-issuance and rate differences observed in public
  healthcare bond disclosures, and on our own deal analysis. Savings depend on
  your deal — these are illustrations, not promises."
- Why: LANGUAGE-POLICY §4 honest labeling + proof-near-claim; adds the honest
  hedge in plain English.

### 2.3 Tier cards (L269–364)

**Free tier (L273–292)**
- L277–279 CURRENT: "Sensing tools — no login required"
  PROPOSED: "Free tools — no login required" ("sensing" banned)
- L273–275: "Free" / "$0/forever" — KEEP (numbers untouched).
- Feature list L281–284 — KEEP.
- L290 CTA CURRENT: "Explore Free Tools"
  PROPOSED: **"Start with the free assessment"** (link target → `/tools/readiness`
  instead of `/tools`)
  Why: §6 — the free path on the pricing page should funnel to the readiness
  assessment, the site-wide lead magnet.

**Subscription tier (L296–333)** — this card carries the page's ONE primary CTA.
- L303–309: "Subscription" / "$499/mo" / "or $4,990/year (save 17%)" — KEEP
  (numbers untouched).
- L310–311 CURRENT: "For organizations exploring bond issuance"
  PROPOSED: "For teams preparing for a bond in the next 1–3 years" — ⚑ only if
  Stephen confirms the 1–3 year framing; otherwise KEEP current.
- L330 CTA: "Subscribe — $499/mo" — KEEP.

**Per-Project tier (L337–363)**
- L341–346: "Per-Project" / "Custom quote" / "Scoped to your deal — pay for
  what you need" — KEEP.
- L360 CTA CURRENT: "Get Your Estimate" — KEEP (in-page anchor, not a
  competing conversion ask).

### 2.4 Feature comparison (L370–404)

- L371 heading "Full Feature Comparison" — KEEP.
- FEATURES rows (L32–47): KEEP names; two glosses in row labels:
  - L35 CURRENT: "COI Benchmarking Tool" → PROPOSED: "Cost-of-Issuance (COI)
    Benchmarks" (matches renamed card; COI glossed once on this page here).
  - L41 CURRENT: "Evidence Extraction (AI)" — KEEP (plain enough).

### 2.5 Per-project estimator (L409–526)

- L412 heading "Per-Project Estimator" — KEEP.
- L414–417 intro CURRENT: "Select the features you need, set your bond size and
  complexity, and get an indicative quote. Final pricing is confirmed after a
  scoping conversation."
  PROPOSED: "Pick what you need, set your deal size and complexity, and get an
  honest ballpark. Final pricing is confirmed after a short scoping call —
  no obligation."
- ESTIMATOR_FEATURES names/descriptions (L61–111): KEEP names and all baseCost
  numbers. One description edit:
  - L65 CURRENT: "Full readiness score, gap analysis, and critical path to
    close" → PROPOSED: "Full readiness score, gap analysis, and a step-by-step
    path to being deal-ready" ("critical path to close" is PM-speak).
- L507 CURRENT: "Indicative range. Final pricing confirmed after scoping call."
  — KEEP.
- L518 CTA CURRENT: "Start with Free Assessment"
  PROPOSED: "Start with the free assessment" — KEEP as the estimator panel's
  action (it funnels to the assessment, per §6).
- L522 CURRENT: "We'll reach out to discuss your project scope" — KEEP.

### 2.6 FAQ (L550–570)

- FAQ 1 answer (L553) CURRENT contains "free sensing tools"
  PROPOSED: "…Start with the free tools today. When you're ready for deeper
  analysis, subscribe or request a per-project quote — your readiness data
  carries over."
- FAQ 2 answer (L557) CURRENT: "The subscription gives you ongoing access to
  advisory dashboards, advanced scoring, and benchmark reports…"
  PROPOSED: "The subscription gives you ongoing access to your project
  dashboard, advanced scoring, and full benchmark reports. Per-project adds
  hands-on deal support scoped to your specific issuance: document evidence
  extraction, disclosure tracking, deliverable packs for your advisors, and
  dedicated support."
  Why: "advisory dashboards" both overstates the feature list and brushes the
  advisor line we're careful about everywhere else.
- FAQ 4 (L564–565, "Is this a replacement for a financial advisor? No.…") —
  KEEP verbatim. This is the best sentence on the page.
- FAQ 5 (L568–569, $5M–$100M range) — KEEP (numbers untouched).

### 2.7 Disclaimer (L584–589)

- CURRENT: "Pricing shown is indicative and subject to final scoping. Muni-Pal
  provides benchmarking, preparation, and analytical tools — not investment
  advice, not municipal advisory advice, and not a pricing, sizing, issuance,
  or deal-execution recommendation. Registered advisors, counsel, underwriters,
  issuers, and borrowers retain their professional roles."
- PROPOSED (same substance, plainer): "Pricing shown is indicative and subject
  to final scoping. Muni-Pal gives you benchmarks, preparation tools, and
  analysis — it is not investment advice, not municipal advisory advice, and
  not a recommendation on pricing, sizing, issuing, or executing a deal. Your
  registered advisors, counsel, and underwriters keep their professional
  roles; we help you walk in prepared."
- Note: no G-42/MSRB language added or removed (LANGUAGE-POLICY §5).

---

## 3. MarketIntelligence.tsx — headers, intro, section labels only

### 3.1 Report header

- L421–423 h1: "{Sector} Municipal Bond Market Intelligence" — KEEP (or
  "…Sector Market Report" if the Card 5 rename is adopted; keep consistent).
- L428–432 intro CURRENT: "Sector benchmark from our municipal bond corpus —
  deal structures, financial benchmarks, risk profiles, credit spreads, and
  rating agency perspectives."
  PROPOSED: "What deals in your sector actually look like — structures,
  financial benchmarks, risk profiles, borrowing costs, and how rating
  agencies see the sector. Built from real public disclosure filings."
  (kills "corpus")

### 3.2 Executive summary block

- L474–481 CURRENT: "This is a data-driven market intelligence report for the
  {sector} municipal bond sector, built from analysis of real public municipal
  securities disclosures, rating agency actions, and secondary market trading
  data."
  PROPOSED: "This report shows you the {sector} municipal bond market as it
  actually is — built from real public municipal securities disclosures,
  rating agency actions, and secondary market trades."
  (already policy-compliant; light outcome-first polish only)
- L516 "What You'll Find in This Report", L539 "Why This Matters", L550 "What
  You Should Take Away", L565 "Data at a Glance" — KEEP all four labels.

### 3.3 Section labels (SECTION_META, L50–66)

- L55 CURRENT: "Pareto Analysis" → PROPOSED: "What Best Performers Look Like"
  ("Pareto" fails the charter-school-CFO sentence test)
- L57 CURRENT: "Risk Profile & Cybersecurity" → PROPOSED: "Where Risk
  Disclosures Go Wrong"
- L61 CURRENT: "Full Pricing Grid" → PROPOSED: "What Healthcare Bonds Cost Now"
- L65 CURRENT: "Engagement Path" → PROPOSED: "How to Work With Us"
- All other labels (Executive Summary, Deal Structure Profile, Rating
  Distribution, Financial Benchmarks, Security & Covenant Profile, Credit
  Spread & Pricing, Bond Structure Norms, Regulatory Framework, Secondary
  Market Activity, Rating Agency Perspective) — KEEP.

### 3.4 In-section header strings (not the data tables)

- L1024 table header CURRENT: "Over AAA MMD" → PROPOSED: "Over AAA benchmark"
  (⚑ Decision 4)
- L1047 CURRENT: "Estimated Cost-of-Capital Reference (25-Year Maturity)" —
  KEEP.
- L1049–1052 CURRENT: "Based on AAA MMD curve + sector spreads. For detailed
  pricing, see Credit Spread Monitor."
  PROPOSED: "Based on the AAA benchmark curve plus sector spreads. For the
  full picture, see Today's Borrowing Costs."
  (⚑ note: the 4.42 base yield at L1059 is hardcoded in the component —
  engineering follow-up, out of copy scope)

### 3.5 Bottom CTA (L1284–1302)

- L1284–1286 CURRENT: "You've seen how your sector benchmarks." — KEEP.
- L1287–1291 CURRENT: "Now see where your organization stands. Take the Bond
  Readiness Scan — it's free, takes 10 minutes, and scores you across the 5
  dimensions that drive your credit rating."
  PROPOSED: "Now see where your organization stands. Take the free Bond
  Readiness Assessment — about 10 minutes, and you'll get a score across the
  5 dimensions that drive your credit rating."
  (naming standardized per Decision 5; "free" moved to the front)
- L1300 button CURRENT: "Take the Bond Readiness Scan"
  PROPOSED: **"Take the Free Readiness Assessment"** (page's one primary CTA)

---

## 4. HealthcareMIRContent.tsx — narrative sections

### 4.1 InformationGap (L11–66)

- L14–15 heading: "The Information Gap You're Walking Into" — KEEP (this is
  good copy).
- L17–22 and L23–26 body — KEEP.
- L44–47 CURRENT: "Market context for advisor review — corpus-calibrated
  cost-of-capital context by rating tier, not a vague 'market rate' answer"
  PROPOSED: "Real cost-of-capital context by rating tier — grounded in deals
  we've analyzed, not a vague 'market rate' answer"
  (kills "corpus-calibrated")
- L60–63 footer CURRENT: "All benchmarks are empirical — sourced from 866
  public official statements, 1,318 financial reports, and 239 rating agency
  actions."
  PROPOSED: "All benchmarks come from real filings: 866 public official
  statements, 1,318 financial reports, and 239 rating agency actions."
  ⚑ Register rows R4 (all three counts; legacy-corpus provenance).

### 4.2 ParetoAnalysis (L148–243)

- L153 heading CURRENT: "Pareto Analysis: What Best Performers Look Like"
  PROPOSED: "What Best Performers Look Like"
- L155–158 sub CURRENT: "The 20% of deal characteristics that explain 80% of
  the credit outcome difference between upgraded and downgraded healthcare
  bonds." — KEEP (this explains the idea without the word "Pareto").
- L163–165 CURRENT: "Best Performer Profile (Top Quartile: DSCR > 4.30x,
  Ratings Aa1–A1)"
  PROPOSED: "Best Performer Profile (top quartile: debt-service coverage above
  4.30x, ratings Aa1–A1)" — DSCR glossed at its first use on this page (see
  §4.0 note below); ⚑ register row R5 for the quartile figures.
- L75 (trait examples) CURRENT: "AdventHealth (FL), Texas Children's Hospital
  (TX)" — **⚑ PROPOSED: remove the named examples.** COPY-STANDARD §5: no
  borrowed authority via third-party names. The trait stands on its own.
- L92 CURRENT: "Corpus median: 202 days. Best performers above 250 days.…"
  PROPOSED: "Median across the deals we analyzed: 202 days. Best performers
  sit above 250.…" (kills "corpus"; ⚑ register row R5)
- L110 CURRENT: "69% of corpus uses gross revenue pledge. 60% have first
  lien.…"
  PROPOSED: "69% of the deals we analyzed pledge gross revenues; 60% carry a
  first lien.…" (⚑ R5)
- L196 CURRENT: "Warning Signs (Bottom Quartile: DSCR < 2.10x, BBB or below)"
  PROPOSED: "Warning Signs (bottom quartile: coverage below 2.10x, BBB or
  below)"
- L229–238 "The critical insight:" block — KEEP (strong, plain).

### 4.3 RiskProfileNarrative (L264–354)

- L268–270 heading CURRENT: "Healthcare Risk Profile — Where Disclosures Go
  Wrong" — KEEP.
- L271–274 sub CURRENT: "Based on 156 risk factors across 11 issuances with
  risk disclosures. Overall mitigation rate: 46% (vs. 23% for WTE)."
  PROPOSED: "Based on 156 risk factors disclosed across 11 healthcare
  issuances. Overall, only 46% of disclosed risks came with a real mitigation
  plan."
  Why: "WTE" is an unexplained internal cross-sector comparison — meaningless
  to this reader; removed. ⚑ R6 for the 156/11/46% figures.
- L317 heading "Cybersecurity — A Bond Documentation Risk" — KEEP.
- L319–324 body — KEEP; ⚑ R7 covers "$25M+ for systems > $500M revenue" and
  the "30–90 days" outage figure.
- L346–349 italic note — KEEP.

### 4.4 BondStructureNorms (L375–463)

- L379–381 heading: "Bond Structure Norms — What Market-Standard Healthcare
  Deals Look Like" — KEEP.
- STRUCTURE_NORMS rows (L358–364): two edits inside the "Market Standard"
  column strings (these are jargon fixes, not data edits):
  - L359 CURRENT: "Gross revenue (69% of corpus)" → PROPOSED: "Gross revenue
    (69% of deals analyzed)"
  - L360 CURRENT: "First lien (60% of corpus)" → PROPOSED: "First lien (60% of
    deals analyzed)"
- L395 column header CURRENT: "Your Deal Should..." — KEEP.
- Obligated Group block (L412–435) — KEEP (already plain and glossed).
- L440–441 CURRENT: "Typical Transaction Timeline (5–8 months total)" — KEEP;
  ⚑ R8 (timeline figures).

### 4.5 PricingGrid (L601–746)

- L605–607 heading: "Current Pricing — What Healthcare Bonds Cost Now" — KEEP.
- L608–611 sub CURRENT: "Municipal yield curve as of March 27, 2026. All-in
  TIC = yield + issuer fees (~7 bps) + structural/underwriting costs (~95
  bps)."
  PROPOSED: "Municipal yield curve as of March 27, 2026. 'All-in TIC' is the
  true interest cost — the yield plus every fee: issuer fees (~7 bps) and
  structural/underwriting costs (~95 bps). (100 bps = 1%.)"
  ⚑ R9: curve is dated March 27, 2026 — four months stale for a section titled
  "Current." Either refresh the data or retitle to "Q1 2026 Pricing."
- L656 CURRENT: "All-In TIC — Healthcare Borrowers (Corpus-Calibrated)"
  PROPOSED: "All-In TIC — Healthcare Borrowers (from observed deals)"
- L674–676 column header CURRENT: "Corpus Obs." → PROPOSED: "Deals Observed"
- L703–705 notes CURRENT: "AA healthcare bonds trade at -12.6 bps to AAA MMD…"
  / "…28 corpus observations = reliable benchmark" / "BBB… +100 bps…"
  PROPOSED: "AA healthcare bonds have traded 12.6 bps below the AAA benchmark
  — strong institutional demand." / "A-rated healthcare bonds trade about 23.9
  bps over the AAA benchmark (28 observed deals — a solid sample)." / "BBB
  healthcare bonds carry roughly +100 bps — materially more expensive, but
  accessible to well-documented credits."
  (⚑ R9 for all three spreads + observation counts; MMD replaced per Decision 4)
- L711–712 heading "What a Rating Tier Costs in Dollar Terms" — KEEP; ⚑ R10
  (the $5.4M/$135M table).
- L737–741 CURRENT: "The AA vs. BBB spread illustration shows why rating-tier
  context belongs in the preparation record for registered-advisor and
  deal-team review."
  PROPOSED: "This is why your rating tier belongs in the preparation record
  you bring to your registered advisor and deal team: the gap between AA and
  BBB is measured in millions."
  (same compliance substance — context for advisor review, not advice —
  plainer sentence)

### 4.6 EngagementPath (L778–819)

- L781–783 heading CURRENT: "How to Engage — The Bond Readiness Path"
  PROPOSED: "How to Work With Us — The Bond Readiness Path"
- L784–786 sub CURRENT: "For a $75M healthcare bond, the Diagnostic costs less
  than 0.04% of deal size." — KEEP; ⚑ R11.
- ENGAGEMENT_STEPS (L750–776) string edits:
  - L757 step name CURRENT: "Readiness Scan" → PROPOSED: "Bond Readiness
    Assessment" (Decision 5)
  - L758 CURRENT: "Automated BFMS pre-screen: sector fit, deal size, top 3
    gaps" → PROPOSED: "Free automated pre-screen: sector fit, deal size, and
    your top 3 gaps" (BFMS is an internal codename — banned)
  - L763 CURRENT: "BFMS score + gap analysis + critical path to close" →
    PROPOSED: "Full readiness score, gap analysis, and a step-by-step path to
    being deal-ready"
  - L768 CURRENT: "Diagnostic + readiness workplan + registered-advisor review
    support" → PROPOSED: "Everything in the Diagnostic, plus a readiness
    workplan and support through your registered advisor's review"
  - L773 CURRENT: "Readiness support — gap remediation, benchmarking, and
    preparation workflow" → PROPOSED: "Hands-on gap remediation, benchmarking,
    and preparation, start to finish"
  - All `cost` values (Free / $15,000–$25,000 / $40,000–$50,000 / $75,000+) —
    KEEP, numbers untouched; ⚑ R11 (consistency check vs PricingPage estimator
    figures — Diagnostic "from $15K" matches).

---

## 5. BenchmarkCalculator.tsx (+ CoiBenchmarking.tsx)

`CoiBenchmarking.tsx` re-exports this component (see Decision 2) — every edit
below applies to both routes.

- L469–471 h1 CURRENT: "Benchmarking Calculator"
  PROPOSED: "Deal Benchmarks" (matches renamed card; keep "Benchmarking
  Calculator" if card rename is declined)
- L472–475 subtitle CURRENT: "Compare your prospective issuance against our
  municipal bond corpus"
  PROPOSED: "See what deals like yours actually cost — compared against real
  municipal bond transactions"
  (kills "corpus")
- L574 button CURRENT: "Run Benchmark" → PROPOSED: **"Compare my deal"**
  (page's one primary CTA)
- L569 loading state "Analyzing..." — KEEP.
- L111–113 COI section heading CURRENT: "COI Estimate"
  PROPOSED: "Cost-of-Issuance (COI) Estimate" (gloss on first use per page)
- L114–119 CURRENT: "Based on {n} actual {subsector} deals ({years})" — KEEP
  (proof adjacent to claim, dynamic).
- L143–145 CURRENT: "Repeat issuers save ~${x}/1000 par on average."
  PROPOSED: "Repeat issuers pay about ${x} less per $1,000 borrowed, on
  average." ("par" without gloss fails sentence test; rephrased instead of
  glossed)
- Results-section headings (Spread Estimate, Peer Comparison, Structural
  Norms, Risk Profile, Financial Benchmarks, Market Context) — KEEP; one edit:
  - L371–373 CURRENT: "Public Finance Authority Comparison" — KEEP but add a
    one-line sub if feasible: "How deals issued through multi-state conduit
    issuers (authorities that issue on your behalf) compare."
- **Missing funnel:** page has no path to the assessment. PROPOSED addition
  after results (secondary, text link): "Not sure you're ready to be in this
  table? Take the free readiness assessment — about 10 minutes."

---

## 6. CreditSpreadMonitor.tsx

- L621–623 h1 CURRENT: "Credit Spread Monitor"
  PROPOSED: "Today's Borrowing Costs" (matches renamed card; alt: keep name)
- L624–627 subtitle CURRENT: "All-in cost of capital comparison powered by our
  municipal bond corpus & live AAA MMD curve"
  PROPOSED: "What each rating tier pays to borrow right now — every fee
  included, built from the AAA benchmark curve and real observed trades. The
  'spread' is simply the premium a borrower pays over that benchmark."
  (kills "corpus" and "MMD"; glosses spread once for the page)
- L692 button CURRENT: "Update Analysis" — KEEP.
- L720–722 banner heading "{Sector} Sector — Cost of Capital Overview" — KEEP.
- L772–775 stat label CURRENT: "Corpus Trades" → PROPOSED: "Trades Observed"
- L784–789 Yield curves intro CURRENT: "…AAA base from {source}; spreads from
  reference table blended with corpus observations."
  PROPOSED: "…The AAA base comes from {source}; spreads blend our reference
  table with real observed trades."
- L797 section title "All-In Cost of Capital Grid" — KEEP; L800–805 intro
  CURRENT: "Estimated all-in True Interest Cost (TIC) by rating and tenor,
  including base yield, sector credit spread, issuer fees, and structural
  costs (underwriter, counsel, trustee, rating agency, DSRF)."
  PROPOSED: "The estimated all-in true interest cost (TIC) — the full annual
  cost of borrowing — by rating and maturity. Includes the base yield, sector
  spread, issuer fees, and every structural cost: underwriter, counsel,
  trustee, rating agency, and reserve fund."
  ("DSRF" unglossed acronym → "reserve fund")
- L153–155 grid column header CURRENT: "Corpus Obs." → PROPOSED: "Observed"
- L812–817 Issuer comparison intro — KEEP ("issuance channels" acceptable),
  minor: "affect all-in TIC" → "change your all-in TIC".
- L824 section title "Observed Spreads" — KEEP (matches LANGUAGE-POLICY §2).
- L828–832 intro CURRENT: "Credit spreads derived from actual secondary market
  trades in our corpus for this sector. These observations inform the blended
  spread estimates in the cost grid above."
  PROPOSED: "Spreads observed in actual secondary-market trades for this
  sector. These real trades feed the blended estimates in the grid above."
- L839–841 empty state CURRENT: "No corpus trade observations yet for this
  sector"
  PROPOSED: "No observed trades yet for this sector"
  (L842–844 second line "Observed data for this sector is coming soon." — KEEP,
  already the LANGUAGE-POLICY §2 approved string)
- L851 section title "Recent Comparable Deals" — KEEP.
- L855–859 intro CURRENT: "Most recent observed trades from our corpus in this
  sector, sorted by trade date. Use these as conversation-ready comps for
  borrower discussions."
  PROPOSED: "The most recent observed trades in this sector, newest first.
  Bring them to your advisor conversations as real reference points."
  Why: kills "corpus"; "comps for borrower discussions" is advisor-side
  framing — the reader IS the borrower.
- L865–867 empty state CURRENT: "No comparable deals in the corpus yet"
  PROPOSED: "No comparable deals observed yet"
  (L868–870 "As sector data is added, trades will appear here." — KEEP,
  approved string)
- L882–886 fee schedules intro — KEEP (plain, honest about negotiation).
- **Missing funnel:** PROPOSED addition near the footer (secondary text link):
  "Want to know which of these rows you'd land in? Take the free readiness
  assessment — about 10 minutes."

---

## 7. ReportExport.tsx

- L183–185 h1: "Export Combined Report" — KEEP.
- L186–189 subtitle CURRENT: "Download your complete sensing analysis as a PDF"
  PROPOSED: "Download everything you've generated here as one free PDF"
  ("sensing" banned; states cost)
- L195–201 empty state CURRENT: "No Report Data Available" / "Use the sensing
  tools to generate results first, then return here to export your combined
  report as a PDF."
  PROPOSED: "Nothing to export yet" / "Run any of the free tools first — your
  results collect here automatically, ready to download as one PDF."
- L286–291 CURRENT: "Ready to export {n} report section(s)" / "Enter your
  information to receive the combined PDF report." — KEEP heading; body
  PROPOSED: "Tell us who to prepare it for and the PDF downloads immediately
  — free."
- L298 / L310 CTA "Get Your Report" — KEEP (one primary CTA).
- L312–314 CURRENT: "We'll prepare your customized PDF with the analysis
  results." — KEEP.
- L436–441 consent text — **KEEP VERBATIM** (compliance substance; already
  plain enough; per LANGUAGE-POLICY §5 do not adjust advisor language
  unilaterally).
- L483–487 success state — KEEP.
- PDF cover L555 CURRENT: "Municipal Bond Sensing Report"
  PROPOSED: "Municipal Bond Readiness & Benchmark Report"
  ("sensing" banned — and this string ships inside a PDF clients forward, the
  highest-risk surface for jargon)
- PDF section heads (L593 "1. Sector Market Intelligence", L674 "2. Issuance
  Benchmark", L782 "3. Bond Readiness Assessment", L941 "4. Credit Spread
  Monitor") — KEEP (rename #4 to "Borrowing Costs" only if the page rename is
  adopted).
- PDF footer L1059–1061 CURRENT: "This report was generated by Muni-Pal
  Sensing Tools using data from our corpus of public municipal securities
  disclosures. For professional advisory services, contact us at
  info@muni-pal.io."
  PROPOSED: "This report was generated by Muni-Pal's free tools using data
  from public municipal securities disclosures and our own deal analysis. It
  is an educational snapshot, not investment or municipal advisory advice.
  Questions? info@muni-pal.io."
  Why: "Sensing" + "corpus" banned (note: LANGUAGE-POLICY §2's export-
  attribution replacement still contains "corpus"; COPY-STANDARD §4 bans the
  word on public surfaces — this wording satisfies both). "For professional
  advisory services, contact us" was actively dangerous — it invites reading
  Muni-Pal as an advisor; replaced with the what-this-isn't line (§7 item 10).

---

## 8. ReadinessAssess.tsx

- L624–626 h1: "Bond Readiness Assessment" — KEEP (canonical name).
- L627–632 subtitle CURRENT: "Evaluate your project across {n} readiness
  categories / risk dimensions"
  PROPOSED: "Find out if your project is bond-ready — free, about 10 minutes,
  no documents required to start"
  (leads with outcome + time/effort/cost per §2/§7-9)
- L667–668 "Project Information", L715–716 "Financial Metrics (optional)" —
  KEEP form section heads. Inside Financial Metrics, gloss once:
  - L724 label CURRENT: "DSCR" → PROPOSED: "DSCR (debt-service coverage —
    cash flow vs. annual payments)"
- L402–407 sub-sector picker CURRENT: "Select the type of healthcare facility
  for a tailored readiness assessment." — KEEP.
- L925–926 CURRENT: "Evidence Items (+2 pts each)" — KEEP.
- L972 submit CTA CURRENT: "Score Assessment"
  PROPOSED: **"See my readiness score"** (page's one primary CTA)
- Results view:
  - L122–124 CURRENT: "Cost of Issuance Impact" → PROPOSED: "Cost-of-Issuance
    (COI) Impact" (gloss placement for this page)
  - L125–134 body CURRENT: "Incomplete readiness may contribute to {range} in
    additional cost-of-issuance pressure from advisory fees, expanded
    feasibility scope, and extended deal timelines."
    PROPOSED: "Gaps like yours typically add {range} in extra fees — more
    advisor hours, a bigger feasibility study, and a longer timeline. Fixing
    them first is how you keep that money."
  - L147–149 "Timeline to Market" — KEEP; L170 bar label CURRENT:
    "Agent-Assisted" → PROPOSED: "With Muni-Pal" ; L197–200 CURRENT: "{n}%
    faster with agent-assisted preparation" → PROPOSED: "{n}% faster with
    Muni-Pal-assisted preparation"
  - L210–212 heading CURRENT: "Agent Displacement Value"
    PROPOSED: "Estimated Preparation Savings"
    ("displacement value" is internal economics-speak)
  - L219–221 CURRENT: "Estimated savings per deal through agent-assisted
    preparation." → PROPOSED: "What deals like yours typically save by closing
    these gaps before engaging the deal team." ⚑ R12 (dynamic value; register
    row for the underlying model).
  - "Dimension Scores", "Financial Assessment", "Gap Analysis", "Priority
    Actions" heads — KEEP.
- **Missing what-this-isn't (§7 item 10):** results view has no disclaimer.
  PROPOSED addition under the score banner (small text): "This is an
  educational readiness snapshot based on what you told us — not investment
  advice, municipal advisory advice, or a loan decision."

---

## 9. HealthcareReadiness.tsx

- L212 h1: "Healthcare Bond Readiness Assessment" — KEEP.
- L213–215 subtitle CURRENT: "Score your facility across critical readiness
  dimensions in about 10 minutes"
  PROPOSED: "Find out if your facility is bond-ready — free, about 10 minutes"
- Step 1 (L254–256): "What type of healthcare organization are you?" +
  explainer — KEEP.
- Step 1b (L281–284): heading KEEP; FQHC_TRACKS descriptions (L71–73) — KEEP
  (specific and honest; "$50M+ revenue" is guidance, not a market claim).
- Step 2 (L308–311) — KEEP.
- Step 3 (L340–343) CURRENT: "Answer these {n} critical-path questions about
  your facility's readiness."
  PROPOSED: "Answer these {n} questions — they're the ones that most affect
  your cost and timeline."
- QuestionCard badge (L488) CURRENT: "{LEVEL} COI IMPACT" — KEEP the badge, but
  add one gloss line at the top of the assessment step: "COI = cost of
  issuance, the fees to get a deal done. High-impact items are the ones that
  cost you real money if they're missing."
- L496–500 badge CURRENT: "Agent-assistable" → PROPOSED: "We can accelerate
  this" (and L928–930 results badge CURRENT: "Accelerable" → same string, for
  consistency).
- L396 CTA: "See Your Readiness Score" — KEEP (primary for the step).
- Lead gate:
  - L668–674 CURRENT: "Get Your Full Readiness Report" + body — KEEP (this is
    the page's one primary conversion; well built).
  - L729–743 consent text — **KEEP VERBATIM** (compliance substance).
  - L750–752 CURRENT: "We never share your information. Used only for your
    readiness report." — KEEP.
  - L766 CTA "Unlock Full Report" — KEEP. L779 skip link — KEEP.
- Results:
  - L848–851 CURRENT: "~{n} weeks with agent assistance" → PROPOSED: "~{n}
    weeks with Muni-Pal's help"
  - L867–868 CURRENT: "{n} weeks / to advisor-review-ready (agent-assisted)"
    → PROPOSED: "{n} weeks / to advisor-review-ready, with our help"
  - L902–905 gaps intro — KEEP (already advisor-safe and plain).
  - L949–952 CTA block CURRENT: "Ready to Organize Your Gaps for Review?" /
    "Our Bond Readiness Accelerator helps organize document preparation, gap
    analysis, and registered advisor coordination; it does not replace
    professional judgment or transaction advice."
    PROPOSED heading: "Ready to close these gaps?" Body: "The Bond Readiness
    Accelerator organizes your document preparation, gap fixes, and
    coordination with your registered advisor. It does not replace
    professional judgment or transaction advice — it makes their review
    faster and cheaper."
  - L958 CTA "Talk to a Readiness Specialist" — KEEP.
  - L971–975 disclaimer — **KEEP VERBATIM** (names Exchange Act §15B; legal
    substance, LANGUAGE-POLICY §5 says don't touch unilaterally).

---

## 10. Flagged claims — CLAIMS-REGISTER queue (ART-129)

No row, no claim (LANGUAGE-POLICY §4). Nothing below is *new*; every figure is
already live. Each needs a row (claim → source artifact → provenance class →
status) before the rewrite ships, or the honest-relabel/remove treatment.

| # | Claim | Where | Concern |
|---|---|---|---|
| R1 | "$150K–$500K saved on a $100M deal" | PricingPage L536 | Provenance unclear; likely legacy Class D. Register or relabel "illustrative." |
| R2 | "One-tier rating improvement saves $27M+ over 25 years" | PricingPage L538 | Methodology-derived (BBB−AA dollar table = $162M−$135M). Label as derived. |
| R3 | "typically costs less than 0.1% of deal size" | PricingPage L539 | Arithmetic on own pricing — low risk; still needs a row. |
| R4 | 866 transactions / 1,318 financial reports / 239 rating actions | ToolsHub intro, InformationGap L60–63, MIR exec summary | Legacy corpus = Class D quarantine. 866 is used in COPY-STANDARD's own example, but the register must confirm before reuse. |
| R5 | DSCR quartiles 4.30x / 2.10x; 202-day median DCOH; 69% gross pledge; 60% first lien; 1.10x coverage; 31.6% DSRF; LOC 4 / insurance 2 | ParetoAnalysis, BondStructureNorms | Class D-derived benchmarks. Register per claim, or relabel "based on our deal experience." |
| R6 | 156 risk factors / 11 issuances / 46% mitigation (and dropped "23% WTE") | RiskProfileNarrative L271–274 | Same provenance; small sample — say so if kept. |
| R7 | "$25M+ cyber coverage for systems > $500M revenue"; "30–90 days" billing outage | RiskProfileNarrative L319–338 | Reads as rating-agency expectation — needs a citable source or "in our experience" labeling. |
| R8 | Transaction timeline 5–8 months + per-phase week ranges | BondStructureNorms L366–372 | Methodology-derived; label if challenged. |
| R9 | Yield curve table (as-of March 27, 2026); TIC grid; −12.6 / +23.9 / +100 bps; 15/28/12 observations | PricingGrid | Dated ("as of" is 4+ months old under a "What Bonds Cost NOW" header) + Class D provenance. Refresh or retitle. |
| R10 | $5.4M/$5.8M/$6.5M annual; $135M/$145M/$162M 25-yr totals | PricingGrid dollar table | Derived from R9 — same treatment. |
| R11 | Engagement prices ($15–25K, $40–50K, $75K+, "0.04% of deal size") | EngagementPath | Own pricing — low risk; confirm consistency with PricingPage estimator ("from $15K" ✓). |
| R12 | COI-gap ranges, timeline-compression %, "preparation savings" values | ReadinessAssess results (API-driven) | Model outputs shown as dollar claims — register the model/methodology once, label outputs "estimated." |
| R13 | "AdventHealth (FL), Texas Children's Hospital (TX)" | ParetoAnalysis L75 | Not a number — borrowed authority via third-party names. **Remove** (proposed in §4.2). |
| R14 | "AAA MMD" (brand) | MIR L1024/L1049, CreditSpreadMonitor subtitle, PricingGrid notes | Third-party mark. Replaced with "AAA benchmark curve" throughout (Decision 4); confirm with counsel. |

---

## 11. Cross-page terminology — one gloss, used everywhere

Gloss appears once per page at the term's first use; after that, the bare term.

| Term | The one gloss (use verbatim) |
|---|---|
| DSCR | "debt-service coverage — cash flow vs. annual payments" |
| COI / cost of issuance | "the fees to get a deal done" |
| Spread | "the premium over the benchmark rate" |
| All-in TIC | "true interest cost — the full annual cost of borrowing, every fee included" |
| Days cash on hand (DCOH) | "how many days you could operate on cash reserves alone" |
| bps | "(100 bps = 1%)" — parenthetical at first use |
| AAA benchmark curve | replaces every "AAA MMD" — no further gloss needed |
| Conduit issuer | "an authority that issues the bonds on your behalf" |
| Par | avoid; say "the face amount" / "per $1,000 borrowed" |
| DSRF | avoid; say "reserve fund" |
| Free readiness assessment | canonical funnel phrase; the tool's proper name is "Bond Readiness Assessment" |
| "our municipal bond corpus" | never; say "real municipal bond transactions from public disclosure filings" or "the deals we've analyzed" |
| "sensing" | never, anywhere visitor-facing |
| "BFMS", "agent displacement", "critical path to close", "pilot qualification" | never; internal only |

---

## 12. §7 checklist self-assessment (combined, post-rewrite)

| # | Checklist item | Status | Notes |
|---|---|---|---|
| 1 | Headline states reader's outcome, not mechanism | ✅ | Every h1/card headline rewritten outcome-first (ToolsHub "Free Bond Tools" is descriptive; card headlines carry the outcomes). |
| 2 | First-time CFO can state the offer in one sentence | ✅ | Sentence test applied to every proposed string; jargon either killed or glossed. |
| 3 | Every quantitative claim has a CLAIMS-REGISTER row | ⚠️ **BLOCKED** | 14 flags in §10. Deck reuses only existing numbers, but rows R1–R12 must exist (or claims relabeled/removed) before ship. |
| 4 | Observed vs. methodology-derived labeled honestly | ⚠️ Partial | Proposals add honest labels (PricingPage attribution, "from observed deals", "estimated"); final wording depends on register outcomes for R5/R9/R10. |
| 5 | Zero banned jargon; allowed terms glossed | ✅ | corpus (×14), sensing (×6), BFMS (×2), agent-displacement, Pareto label, pilot-jargon — all removed. Glosses per §11, once per page. |
| 6 | Zero EMMA/MSRB or internal-tooling references | ✅ | Source pages already carried zero EMMA/MSRB in these ten files (pre-cleaned); rewrite introduces none. HealthcareReadiness disclaimer's "Securities Exchange Act §15B" retained per LANGUAGE-POLICY §5 (statute cite, not an MSRB mark). Re-run the §6 grep gate on the built bundle before deploy. |
| 7 | Exactly one primary CTA; assessment funnel reachable | ✅ | Per page: ToolsHub → assessment card primary; Pricing → Subscribe (free path funnels to assessment); MIR → "Take the Free Readiness Assessment"; Benchmark → "Compare my deal" + new assessment funnel link; Spread Monitor → "Update Analysis" + new funnel link; Export → "Get Your Report"; ReadinessAssess → "See my readiness score"; HealthcareReadiness → "Unlock Full Report". |
| 8 | Proof adjacent to claim | ✅ | Kept/strengthened ("866 real transactions" in the intro that makes the claim; "based on {n} actual deals" stays beside the COI estimate). |
| 9 | Time/effort/cost of next step stated | ✅ | "Free, about 10 minutes" attached to every assessment mention; "free" added to export and tools intro. (Decision 3: 10 vs 15 min.) |
| 10 | What-this-isn't disclaimer where results shown | ⚠️ 1 gap fixed | Present on Pricing, Export consent, HealthcareReadiness. **Was missing on ReadinessAssess results** — addition proposed in §8. PDF footer's "contact us for professional advisory services" replaced with a what-this-isn't line. |

**Net:** the deck passes 7/10 outright; items 3 and 4 are blocked on the ART-129
claims register (by design — this deck flags rather than repeats), and item 10
is fixed by one proposed addition.
