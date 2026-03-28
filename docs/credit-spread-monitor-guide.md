# Credit Spread Monitor & All-In Cost of Capital Tool

## How to Talk About This Tool with Borrowers

This guide explains every section of the Credit Spread Monitor page, how each number is calculated, where the data comes from, and how to use it in conversations with prospective borrowers. Written for internal use by the bond facility team.

---

## What This Tool Does (The Elevator Pitch)

The Credit Spread Monitor answers the question every borrower's CFO is asking:

> "If we're rated [X] and want to borrow for [Y] years in the [sector] market, what does money actually cost us all-in, and how does going through your facility compare to PFA or our local HFA?"

It combines three things that no other single tool brings together:

1. **Live benchmark yields** (AAA MMD municipal curve)
2. **Actual trade data** from EMMA (the MSRB's public market transparency system)
3. **Issuer fee structures** for side-by-side comparison

The result is a cost-of-capital grid that mirrors how underwriters and bankers quote the market, but built specifically around our facility's fee economics.

---

## Page Sections Explained

### 1. Parameters Bar

**What it controls:**
- **Sector** — Selects which EMMA corpus to query (waste, healthcare, etc.). Each sector has its own pool of comparable deals, and spread behavior differs across sectors.
- **Representative Par ($)** — The assumed par amount of the bond issue. This matters because issuer fees have minimums (e.g., $3,000/year for IDA Sierra Vista). On a $5M deal, the minimum bites and the effective fee rate is higher. On a $50M deal, the basis-point rate governs. Default is $50M.
- **Out-of-state borrower** — When checked, adds the out-of-state surcharge (3 bps for IDA Sierra Vista at the President's discretion) to the fee calculation. PFA has no geographic restrictions, so its fee doesn't change.

**When talking to borrowers:** Ask them for their expected par amount and whether they're in-state. Plug those in to show them their specific cost picture.

---

### 2. Summary Banner (Dark Header)

**What it shows:**
- **AAA 10yr / AAA 30yr** — The current tax-exempt AAA muni benchmark at 10 and 30 years. This is the "risk-free" floor for municipal borrowing. Everything else is priced as a spread above this.
- **A-rated 30yr TIC** — The all-in True Interest Cost for a typical A-rated, 30-year deal through our facility. This is the headline number for a large chunk of borrowers.
- **Corpus Trades** — How many actual comparable deals from EMMA are informing the analysis.

**Where the data comes from:**
The AAA curve is sourced from FMSbonds.com (a public municipal yield table updated daily). The system attempts to scrape live data; if the scrape fails (FMSbonds uses JavaScript rendering), it falls back to a manually-maintained reference curve. The "AAA curve: reference" label in the corner tells you which source was used.

**Current reference curve (March 2026 snapshot):**

| Tenor | 1yr | 2yr | 3yr | 5yr | 7yr | 10yr | 15yr | 20yr | 25yr | 30yr |
|-------|-----|-----|-----|-----|-----|------|------|------|------|------|
| AAA   | 2.85% | 2.95% | 3.10% | 3.35% | 3.60% | 3.85% | 4.15% | 4.35% | 4.42% | 4.45% |

**When talking to borrowers:** "Today's AAA benchmark 30-year is 4.45%. Your cost builds from there based on your credit rating and the fees of the issuing authority."

---

### 3. Municipal Yield Curves by Rating

**What it shows:**
A table of estimated tax-exempt yields by rating tier (AAA through BB) across 6 tenors (5yr through 30yr).

**How it's calculated:**
Each cell = AAA base yield at that tenor + credit spread for that rating.

The credit spreads come from a reference spread table based on Bloomberg municipal curve analytics and ICE MMD curves:

| Rating | Spread over AAA (bps) | At 30yr AAA of 4.45% |
|--------|-----------------------|----------------------|
| AAA | 0 | 4.45% |
| AA+ | +12 | 4.57% |
| AA | +20 | 4.65% |
| AA- | +32 | 4.77% |
| A+ | +45 | 4.90% |
| A | +62 | 5.07% |
| A- | +82 | 5.27% |
| BBB+ | +110 | 5.55% |
| BBB | +145 | 5.90% |
| BBB- | +190 | 6.35% |
| BB+ | +250 | 6.95% |
| BB | +340 | 7.85% |

These are mid-market indicative spreads. Actual execution depends on deal-specific factors (structure, covenants, investor demand, market conditions).

**When corpus data is available**, the system blends the reference spread with the observed spread from actual EMMA trades (50/50 blend). This grounds the estimates in real market activity for the specific sector.

**When talking to borrowers:** "This table shows you the current yield environment. If you're an A-rated healthcare issuer looking at 30-year money, the market is indicating roughly 5.07% before costs. Here's how we get to your all-in number..."

---

### 4. All-In Cost of Capital Grid

**What it shows:**
A matrix of rating (AA, A, BBB, BB) x tenor (10yr, 20yr, 30yr) showing the full cost buildup:

| Column | What It Is | How It's Calculated |
|--------|------------|---------------------|
| AAA Base | Risk-free muni yield at that tenor | From AAA curve (FMSbonds or reference) |
| Sector Spread | Credit premium for that rating | From spread table, blended with corpus observations |
| Est. Yield | What the market charges for that credit | AAA Base + Sector Spread |
| Issuer + Costs | Fees and structural costs | Issuer fee (annualized) + structural costs |
| All-In TIC | True Interest Cost | Est. Yield + Issuer + Costs |
| Corpus Obs. | What we've actually seen in EMMA trades | Median yield from matched trades (with count) |

**The fee component breakdown (default 95 bps total):**

| Cost Component | Default (bps) | What It Represents |
|----------------|---------------|--------------------|
| Underwriter spread | 75 | Senior manager/underwriting syndicate compensation |
| Bond/issuer counsel | 10 | Legal costs annualized over bond life |
| Trustee/paying agent | 2 | Trust administration fees |
| Rating agency fees | 3 | S&P/Moody's/Fitch fees annualized |
| Bond insurance | 0 | Premium if applicable (not assumed by default) |
| DSRF opportunity cost | 5 | Opportunity cost of funded debt service reserve |
| Capitalized interest | 0 | If applicable during construction period |
| **Total structural** | **95** | |

Plus the issuer's own fee (7 bps for IDA Sierra Vista on a $50M+ deal).

**The TIC formula:**
```
All-In TIC = AAA Base Yield
           + Credit Spread (bps / 100)
           + Issuer Fee (annualized bps / 100)
           + Structural Costs (95 bps / 100)
```

**Example: A-rated, 30-year, $50M, through IDA Sierra Vista:**
```
AAA 30yr base:     4.45%
+ A spread:       +0.62%  (62 bps)
= Est. yield:      5.07%
+ IDA fee:        +0.07%  (7 bps annualized)
+ Structural:     +0.95%  (95 bps)
= All-In TIC:      6.09%
```

**How the issuer fee is annualized:**
The system calculates the effective annual fee including minimums. For IDA Sierra Vista:
- On $50M: 7 bps = $35,000/year (above $3,000 minimum, so 7 bps governs)
- On $5M: 7 bps = $3,500/year (above minimum, still 7 bps effective)
- On $1M: minimum bites — $3,000/$1M = 30 bps effective

For issuers with upfront fees (like PFA: 15 bps + $2,500), the upfront is amortized over the bond maturity and added to the annual rate.

**When talking to borrowers:** Walk them through the column-by-column buildup. The key insight is that the *yield* (what investors demand) is market-driven, but the *fees* (what it costs to get to market) differ by issuer channel. That's where your facility creates value.

---

### 5. Issuer Channel Comparison

**What it shows:**
Side-by-side cost comparison for A-rated and BBB-rated deals at 20yr and 30yr across three issuer channels:
1. **IDA of the City of Sierra Vista** — Our facility
2. **Public Finance Authority (WI)** — National conduit issuer
3. **Local Health Facilities Authority** — Representative local HFA

For each, it shows:
- **Issuer Fee** — The issuer's annualized fee drag in bps
- **Total Costs** — Issuer fee + structural costs
- **Annual on $50M** — Dollar amount the borrower pays the issuer per year
- **All-In TIC** — Bottom-line cost of capital

The "lowest" label highlights which channel has the best all-in economics.

**How issuer fees are structured:**

| | IDA Sierra Vista | PFA Wisconsin | Local HFA |
|---|---|---|---|
| Annual fee | 7 bps | 10 bps | 8 bps |
| Annual minimum | $3,000/yr | $5,000/yr | $4,000/yr |
| Upfront fee | Negotiable | 15 bps + $2,500 | 10 bps + $1,500 |
| Out-of-state surcharge | +3 bps (President's discretion) | None | N/A (local only) |
| Annual on $50M | $35,000 | $50,000 | $40,000 |

**Fee calculation detail for IDA Sierra Vista (from Board-approved 2025 fee language):**
- 7 basis points per annum on outstanding principal, paid annually or semiannually
- $3,000 per year minimum
- President may approve a one-time present-value lump sum in lieu of annual payments (from issuance through first call date)
- Out-of-state surcharge at President's discretion
- Fee shall not impact tax-exempt status; Authority retains right to adjust per resolution
- Final fees are negotiated between borrower's counsel and issuer's counsel during engagement

**When talking to borrowers:** "On a $50M A-rated 30-year deal, our facility saves you $15,000 per year compared to PFA — that's roughly 3-4 basis points of annual drag. Over 30 years that's $450,000 in cumulative savings on issuer fees alone. And unlike PFA, if you can do a lump-sum payment, the President has discretion to accept that."

---

### 6. EMMA Corpus: Observed Spreads

**What it shows:**
Actual credit spreads derived from secondary market trades in EMMA for the selected sector. For each rating bucket:
- **Observations** — Number of securities with matched trades
- **Median Yield** — The middle yield from all matched trades
- **Range** — Min to max observed yield
- **Spread vs AAA** — Median spread over the **tenor-matched** AAA curve point

**Where the data comes from:**
1. The **EMMA crawler** discovers municipal bond securities on MSRB EMMA by sector
2. For each security, it extracts the **snapshot** (issuer, CUSIP, par amount, maturity, coupon) and **trade history** (trade date, price, yield, amount, type)
3. The system then needs a **credit rating** for each bond. It looks in three places, in priority order:
   - EMMA security page ratings (often empty on EMMA due to how rating agencies report)
   - **Rating action PDFs** extracted from continuing disclosures (e.g., "Moody's upgrades Republic Services to Baa1")
   - **Official Statement ratings** extracted during document processing
4. The system matches issuers by name between the EMMA crawler data and the corpus database to assign ratings

**How the tenor-adjusted spread works:**
Rather than comparing all yields to a single benchmark (which would be misleading for mixed tenors), each trade's yield is compared to the AAA curve at the **same maturity point**. For example:
- A 2028-maturity bond yielding 2.76% is compared to AAA 2yr (2.95%), showing a -19 bps spread (cheaper than AAA at that tenor)
- A 2038-maturity bond yielding 3.03% is compared to AAA ~12yr (3.97%), showing a -94 bps spread

Note: Negative spreads typically indicate the trade occurred during a lower-rate environment than the current reference curve. The trade yields are real — the "spread" reflects the time-of-trade rate environment vs today's curve.

**Current corpus sizes:**
- **Waste**: ~198 securities, ~27 with matched trades and ratings
- **Healthcare**: ~363 securities, ~57 with matched trades and ratings

These grow as we run more EMMA crawls and extract more rating data from Official Statements.

**When talking to borrowers:** "These aren't theoretical spreads — these are actual trades that happened in the secondary market for bonds in your sector. We're showing you what the market has actually priced for credits like yours."

---

### 7. Recent Comparable Deals

**What it shows:**
The 20 most recent trades from the EMMA corpus in the selected sector, sorted by trade date. Each row shows:
- **Issuer** — The security name from EMMA (e.g., "Public Finance Authority / Solid Waste Disposal Revenue Bonds")
- **Rating** — The assigned rating bucket (AA, A, BBB, BB)
- **Yield** — The trade yield
- **Par Amount** — The original par amount of the security
- **Maturity** — The bond's maturity date
- **Trade Date** — When the secondary market trade occurred
- **CUSIP** — The bond's unique identifier

**Where the data comes from:**
These are real secondary market trades reported to the MSRB (Municipal Securities Rulemaking Board) and published on EMMA. Every municipal bond trade in the US must be reported to the MSRB within 15 minutes of execution.

**Important caveats for borrower conversations:**
- These are *secondary market* trades (existing bonds trading between investors), not *primary market* pricing (new issuance). Primary market TICs on new deals may differ.
- Trade yields reflect the market conditions *at the time of trade*, not today.
- The rating shown is from our most recent rating action data, not necessarily the rating at the time of trade.

**When talking to borrowers:** "Here are the most recent trades we're tracking in your sector. You can see that A-rated solid waste bonds recently traded at 3.7-4.0% yield. When you add issuance costs, you're looking at roughly [X]% all-in through our facility."

---

### 8. Issuer Fee Schedules

**What it shows:**
Detailed fee cards for each issuer channel showing annual fees, minimums, upfront costs, out-of-state surcharges, and an example calculation on a $50M issue.

**When talking to borrowers:** Point to these cards when a borrower asks "what do you charge?" Show them the full picture — annual fee, minimums, and how it compares. Emphasize that our fees are set by Board resolution and that final terms are negotiated during engagement between borrower's counsel and issuer's counsel.

---

## Data Pipeline: How Everything Connects

```
                                    ┌──────────────────────┐
                                    │  FMSbonds.com        │
                                    │  (AAA MMD yields)    │
                                    └──────────┬───────────┘
                                               │ HTTP scrape (daily cache)
                                               ▼
┌──────────────┐                   ┌──────────────────────┐
│ EMMA (MSRB)  │──── Playwright ──▶│  EMMA Crawler        │
│ Security     │    browser        │  (output/{sector}/)  │
│ Detail Pages │    automation     │  *.json per security │
└──────────────┘                   │  - snapshot          │
                                   │  - trades            │
                                   │  - ratings           │
                                   └──────────┬───────────┘
                                              │
┌──────────────┐                              │
│ Official     │──── AI extraction ──▶ ┌──────┴───────────┐
│ Statements   │    (Claude)          │  Corpus DB        │
│ & Rating     │                      │  (corpus.db)      │
│ Action PDFs  │                      │  - rating_actions │
│              │                      │  - ratings        │
│              │                      │  - deal_identities│
└──────────────┘                      └──────────┬────────┘
                                                 │
                                    ┌────────────┴────────────┐
                                    │ Credit Spread Monitor   │
                                    │                         │
                                    │ 1. Fetch AAA curve      │
                                    │ 2. Load EMMA JSONs      │
                                    │ 3. Match ratings from   │
                                    │    corpus DB            │
                                    │ 4. Compute spreads      │
                                    │    (tenor-adjusted)     │
                                    │ 5. Build cost grid      │
                                    │ 6. Compare issuers      │
                                    └────────────┬────────────┘
                                                 │ JSON API
                                                 ▼
                                    ┌─────────────────────────┐
                                    │ Frontend Page           │
                                    │ /tools/credit-spreads   │
                                    └─────────────────────────┘
```

---

## Key Assumptions & Limitations to Be Transparent About

### What's solid:
- **Trade data is real** — every yield comes from an actual MSRB-reported trade
- **Fee structures are accurate** — IDA Sierra Vista fees match the Board-approved 2025 language exactly
- **Rating assignments** — sourced from S&P, Moody's, and Fitch via extracted rating action reports and Official Statements

### What's estimated:
- **AAA reference curve** — When the live FMSbonds scrape fails, we use a manually-maintained snapshot. This should be updated periodically. The current snapshot is from March 2026.
- **Credit spreads** — The reference spread table (AA +20 bps, A +62 bps, etc.) represents typical mid-market conditions. Actual spreads vary with supply/demand, deal structure, and market sentiment. When corpus data is available, we blend it 50/50 with the reference table.
- **Structural costs (95 bps)** — These are reasonable estimates for a standard 30-year level-debt-service structure with 10-year par call. Actual costs vary by deal. The underwriter spread (75 bps) is the largest component and is negotiable.
- **PFA and Local HFA fees** — These are representative estimates based on public information and market knowledge. Actual PFA fees vary by deal and are negotiable on larger transactions.

### What's not captured:
- **Primary market execution** — Our comps are secondary market trades. New-issue concessions and institutional order dynamics can affect primary market TIC by 5-15 bps.
- **Call structure effects** — We assume a standard 10-year par call. Non-callable bonds, make-whole calls, or extraordinary call provisions affect yield.
- **Bond insurance** — Not included by default (0 bps). If a borrower qualifies for insurance (Assured Guaranty, Build America Mutual), it could tighten spreads by 20-50 bps while adding 30-60 bps of insurance premium — net effect depends on the credit.
- **Market conditions at time of pricing** — The grid shows where the market is *today*. By the time a deal prices (weeks or months later), rates and spreads may have moved.
- **Sector-specific nuances** — Healthcare revenue bonds trade differently than solid waste system bonds. The tool shows sector-specific corpus data, but within healthcare alone there's wide variation (large system AA vs. single-site BBB).

---

## How to Use This in a Borrower Meeting

### Opening:
"Let me show you what the current cost of capital looks like for a [sector] issuer at your rating level. This is our Credit Spread Monitor — it combines live market data with actual trade history from EMMA."

### Walking through the grid:
"The AAA benchmark 30-year is currently at 4.45%. For an [A]-rated credit like yours, the market adds about 62 basis points, putting the estimated yield at 5.07%. On top of that, there are issuance costs — underwriter, counsel, trustee, rating agency — that add about 95 basis points. And our facility fee is just 7 basis points. That puts your all-in True Interest Cost at approximately 6.09%."

### The comparison:
"Now here's where it gets interesting. If you went through PFA instead, their fee structure adds about 10.5 basis points annualized — that's higher upfront costs amortized over the life. On a $50M deal, you're paying them $50,000 a year vs. $35,000 through us. That's a $15,000 annual savings, which compounds over a 30-year bond life."

### The comps:
"And these aren't hypothetical numbers. Here are the most recent actual trades in your sector from EMMA — you can see that [issuer] most recently traded at [X]%, which is right in line with our estimates."

### The credibility closer:
"We built this tool to give you the same kind of market transparency that the big underwriting desks have. We want you to see exactly how the cost breaks down and make an informed decision about your issuance channel."

---

## Updating the Data

### To refresh the AAA curve:
The system caches the FMSbonds scrape daily. To force a refresh, the cache file is at `emma/bond_os_extractor/data/_market/aaa_mmd_cache.json`. Delete it to trigger a fresh scrape on the next API call.

To update the reference fallback curve (when you know FMSbonds isn't being scraped successfully), edit the `REFERENCE_AAA_CURVE` in `emma/bond_os_extractor/src/analysis/yield_curve_fetcher.py`.

### To add more EMMA corpus data:
Run the EMMA crawler for the target sector:
```bash
cd MUNI-PAL/emma/emma_crawler
python -m src.main --search-params search_params_healthcare.yaml --output-dir ./output/healthcare --visible
```
The credit spread monitor automatically picks up new JSON files from the output directory.

### To add a new issuer fee schedule:
Add a new `IssuerFeeSchedule` dataclass instance in `emma/bond_os_extractor/src/analysis/credit_spread_monitor.py` and register it in the `ISSUER_SCHEDULES` dict.

### To adjust structural costs:
Modify the `DEFAULT_STRUCTURAL_COSTS` instance in the same file, or pass custom `StructuralCosts` per-request through the API.
