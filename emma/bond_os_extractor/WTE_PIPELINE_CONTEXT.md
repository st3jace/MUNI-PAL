# WTE Sector Pipeline: Architecture, Execution & Findings

**Generated**: 2026-03-03
**Corpus**: 51 EMMA securities, 629 PDFs, 284 extracted documents
**Target**: UCS Caldor 2026 — $40M modular pyrolysis biomass-to-value, El Dorado County CA

---

## 1. Pipeline Overview

The WTE (Waste-to-Energy) sector pipeline applies the Summers Methodology
(Phases 1–6) to a purpose-built corpus of EMMA municipal bond documents. It
bridges two data worlds — sparse, document-sourced bond data and dense daily
equity price histories — to produce risk-adjusted performance metrics for the
WTE/resource-recovery universe.

### Execution sequence

```
EMMA Crawl (6-pass)
  → Batch Ingest (284 docs)
    → Fundamental Scoring (Phase 1)
      → S_Omega Returns (Phase 2)
        → Benchmark & CRI (Phase 3)
          → Hilbert Signal Extraction (Phase 4)
            → Extended Omega & IRS (Phase 5)
```

Phase 6 (Synthetic Bond Returns) runs inline during Phase 2 for obligors that
lack equity tickers, building return series from EMMA trades + rating shocks +
fundamental drift + coupon carry.

---

## 2. EMMA Crawl

Six-pass crawl against MSRB EMMA, each targeting a different keyword/size
combination relevant to WTE infrastructure:

| Pass | Keyword | Size Floor | Expected |
|------|---------|-----------|----------|
| 1 | Waste | $100M | 50–150 |
| 2 | Resource Recovery | $50M | 10–40 |
| 3 | Solid Waste | $100M | 30–80 |
| 4 | Environmental | $100M | 20–60 |
| 5 | Biomass Energy | $25M | 5–20 |
| 6 | Energy Recovery | $75M | 5–15 |

**Result**: 51 unique securities, 629 PDFs across 51 CUSIP folders.

Config files: `emma_crawler/config/search_params_wte*.yaml` (6 files)
Output: `emma_crawler/output/wte/`

---

## 3. Batch Ingest

**Command**: `python batch_ingest.py --sector wte --all-types`

### Document routing

Each PDF is routed by filename keywords and first-page content to one of four
extraction paths:

1. **Official Statement** (OS) — fallback for `official_statement`,
   `remarketing_supplement` keywords in filename
2. **Rating Action** — agency + action combo in filename (e.g.,
   `SP_Downgrade`, `Moodys_Affirm`) → 0.98 confidence score
3. **Event Filing** — material event notice keywords
4. **Financial Report** — 10-K/10-Q headers (ALL-CAPS) or municipal CAFR
   patterns (Title Case) detected via page-level scanning

### Extraction tiers

- **Tier 1 (deterministic)**: regex + table parsers for CUSIPs, par amounts,
  dates, ratings, financial tables
- **Tier 2 (AI)**: Claude API extraction for narrative fields (issuer name,
  revenue sources, bond description). Results cached by SHA-256 hash — no
  duplicate API calls on re-runs.

### Safeguards

| Guard | Value | Rationale |
|-------|-------|-----------|
| `MIN_FILE_SIZE_ALL` | 10 KB | Skip empty stubs |
| `MIN_FILE_SIZE` (OS) | 100 KB | OS docs are substantial |
| `MAX_FILE_SIZE` | 30 MB | Skip image-only SEC 10-K scans (0 extractable text, 14+ GB RAM) |
| `MIN_TEXT_LENGTH` | 100 chars | Skip image-only PDFs at module level |
| `quick_hash` dedup | SHA-256 of first 64 KB | Identical PDFs across CUSIP folders |

### Results

| Module | Documents | Examples |
|--------|-----------|----------|
| Event Filing | 144 | Material events, continuing disclosures |
| Financial Report | 83 | 10-K, 10-Q, CAFR, audited financials |
| Rating Action | 29 | S&P/Moody's/Fitch upgrades, downgrades, affirmations |
| Official Statement | 28 | Primary offering documents |
| **Total** | **284** | from 600 eligible PDFs (47% hit rate) |

17 PDFs (32–148 MB) were skipped by the MAX_FILE_SIZE guard, including 89 MB
RSG 10-K scans and 148 MB Dominion Energy filings — all confirmed image-only
with 0 extractable text.

### Unique issuers extracted (~40)

**Corporate borrowers** (behind conduit bonds):
Dominion Energy, Southern Company, Nucor, ArcelorMittal, US Steel, BP,
Waste Management, Republic Services, GFL Environmental, Reworld/Covanta,
Core Natural Resources, Novelis, Waste Pro USA, American Titanium Metal

**Municipal/IDA conduit authorities**:
Cumberland County NJ, FL Development Finance Corp, CA Municipal Finance
Authority, PA EDFA, WV Economic Development Authority, Arkansas Dev Finance,
Iowa Finance Authority, NJ Infrastructure Bank, Brazoria County IDC TX,
Jersey City MUA, Sacramento Sanitation District, Northern CA Sanitation
Agencies, City of Whiting IN, City of Osceola AR, and others

---

## 4. Obligor Mapping

`src/analysis/obligor_mapping.py` — `WTE_OBLIGORS` list with two tiers:

### Tier 1: Corporate borrowers with equity tickers (9)

| Obligor | Ticker | Aliases | Notes |
|---------|--------|---------|-------|
| Dominion Energy Inc | D | virginia electric and power, virginia power fuel securitization | 1,256 daily obs |
| The Southern Company | SO | southern company, development authority of burke county | 1,256 daily obs |
| Nucor Corporation | NUE | nucor, development authority of bartow county | 1,256 daily obs |
| ArcelorMittal | MT | arcelormittal | 1,256 daily obs |
| BP plc | BP | bp p.l.c, city of whiting | 1,256 daily obs |
| Waste Management Inc | WM | waste management, wm holdings | 8,650 daily obs |
| Republic Services Inc | RSG | republic services | 6,943 daily obs |
| GFL Environmental Inc | GFL | gfl environmental | 1,491 daily obs |
| Core Natural Resources Inc | CNR | core natural resources, consol energy | 1,256 daily obs (formerly CEIX) |

### Tier 2: Bond-only obligors (no ticker)

| Obligor | Reason |
|---------|--------|
| United States Steel Corporation | Delisted (Nippon Steel acquisition) |
| Reworld Holding Corporation | Private since 2021 (EQT/Covanta) |
| Novelis Inc | Private (Hindalco/Aditya Birla) |
| Cumberland County (NJ) | Municipal |
| FL Development Finance Corp | State conduit |
| CA Municipal Finance Authority | Municipal |
| PA EDFA | State conduit |
| Northern CA Sanitation Agencies | Municipal |
| Iowa Finance Authority | State conduit |
| NJ Infrastructure Bank | State revolving fund |
| Brazoria County IDC (TX) | County conduit |
| Mission Economic Development Corp | Municipal |
| City of Osceola (AR) | Municipal |
| Jersey City MUA | Municipal utility |
| Sacramento Sanitation District | Municipal utility |

Alias matching maps conduit issuers to the underlying corporate borrower (e.g.,
"Development Authority of Burke County" → Southern Company). This enables the
scoring engine to aggregate extraction data from conduit bonds with the
borrower's equity fundamentals.

---

## 5. Phase 1 — Fundamental Scoring

**File**: `src/analysis/scoring_engine.py`
**Output**: `data/wte/analysis/fundamental_scores.json`

### Formula

```
F_i = 0.30 × FinancialStability
    + 0.20 × Profitability
    + 0.25 × CreditQuality
    + 0.15 × StructuralQuality
    + 0.10 × GrowthMomentum
```

Each dimension is scored 0–100 from both bond extraction data and equity
financials (where available), then blended.

### Dimension details

| Dimension | Weight | Bond inputs | Equity inputs |
|-----------|--------|-------------|---------------|
| Financial Stability | 0.30 | DSCR, leverage, cash coverage | Current ratio, debt/equity |
| Profitability | 0.20 | Operating margin, net margin | ROA, EBITDA margin |
| Credit Quality | 0.25 | Rating level (21-point), trajectory, outlook | Rating actions |
| Structural Quality | 0.15 | Enhancement, covenants, DSRF, lien | — (defaults if missing) |
| Growth/Momentum | 0.10 | Revenue CAGR | Stock price momentum, rating upgrades |

### Investability threshold

F_i >= 50 **and** sufficient data diversity (at least 2 distinct source types
beyond just OS records).

### WTE results

| Obligor | F_i | Status | Data sources |
|---------|-----|--------|--------------|
| Republic Services Inc (RSG) | 70.0 | Investable | 2 financial, 4 rating |
| United States Steel (—) | 67.1 | Investable | 3 financial, 3 rating |
| Dominion Energy Inc (D) | 66.1 | Investable | 1 OS, 7 financial, 1 rating |
| Nucor Corporation (NUE) | 65.0 | Scored | 1 financial |
| The Southern Company (SO) | 62.0 | Scored | 3 financial |
| Waste Management Inc (WM) | 60.4 | Investable | 4 financial, 2 rating |
| Core Natural Resources (CNR) | 55.5 | Scored | 1 financial |
| Sacramento Sanitation District | 54.6 | Scored | 6 financial, 1 rating |
| Jersey City MUA | 46.2 | Scored | 6 financial |
| ... (16 more below 50) | — | Excluded | — |

**25 obligors scored, 4 investable, average F_i = 37.3**

Nucor (65.0) and Southern Company (62.0) score above 50 but are excluded from
the investable universe because they lack rating action data — the scoring
engine requires evidence from at least 2 source types for full qualification.

---

## 6. Phase 2 — S_Omega Return Analysis

**File**: `src/analysis/omega.py`
**Output**: `data/wte/analysis/s_omega_results.json`

### Formula

```
S_Omega = r_f + E[r_f - r_mk]⁺ × (E(R_i) - r_f) / E[r_f - r_ik]⁺
```

Where:
- `r_f` = risk-free rate (4.5% annual → 0.0173% daily)
- `E(R_i)` = geometric mean of asset returns per period
- `E[r_f - r_mk]⁺` = mean excess of risk-free over market (downside, clipped at 0)
- `E[r_f - r_ik]⁺` = mean excess of risk-free over asset (downside, clipped at 0)

### Omega ratio (Keating-Shadwick)

```
Ω(Θ) = E[R_i - Θ]⁺ / E[Θ - R_i]⁺
```

Gain probability integral divided by loss probability integral at threshold Θ.
Ω > 1 means expected gains exceed expected losses at that threshold.

### SIC matrix

Each asset is characterized by three scalars:

| Component | Formula | Interpretation |
|-----------|---------|----------------|
| R_A (Risk) | `((E[r_f - r_ik]⁺ + 1)^252 - 1) × 100` | Annualized downside risk % |
| E_A (Return) | `((E(R_i) + 1)^252 - 1) × 100` | Annualized expected return % |
| MDDD_S | Drawdown duration + recovery time | Max drawdown duration in years |

### Market benchmark

Equal-weighted basket of all 9 WTE sector tickers (D, SO, NUE, MT, BP, WM,
RSG, GFL, CNR). 1,506 trading dates from 2020-03-05 to 2026-03-03.

### Bond benchmark

Built from 48 EMMA secondary market bonds with trade data. 582 trading dates.
Used for synthetic bond return analysis.

### WTE results

| Asset | Type | S_Omega | Omega | E_A | R_A | MDDD_S | Max DD | n |
|-------|------|---------|-------|-----|-----|--------|--------|---|
| US Steel | Bond | 8,932% | 35,659 | 6,639% | 19.7% | 0.4 yr | -9.8% | 80 |
| RSG | Equity | 17.08% | 1.130 | 17.5% | 194.8% | 3.3 yr | -34.0% | 1,532 |
| WM | Equity | 13.24% | 1.098 | 13.8% | 202.8% | 3.9 yr | -30.1% | 1,532 |
| D | Equity | 2.95% | 1.005 | 2.6% | 268.3% | 32.8 yr | -52.2% | 1,255 |

**US Steel outlier**: The synthetic bond return series for USS produces extreme
Omega (35,659x) because EMMA trade prices reflect the Nippon Steel acquisition
premium — sustained price appreciation with near-zero downside variance. This is
a known artifact of event-driven dislocation in the synthetic returns model. The
3 equity assets produce clean, reliable metrics.

**Accuracy**: 98.8%–99.9% (1 - 1/n). P(Black Swan) = 0.07%–1.25%.

---

## 7. Phase 3 — Benchmark & Composite Ranking Index

**File**: `src/analysis/benchmark.py`
**Output**: `data/wte/analysis/benchmark_results.json`

### CRI formula

```
CRI = 0.40 × S_Omega_percentile
    + 0.25 × SIC_efficiency_percentile
    + 0.20 × drawdown_resilience_percentile
    + 0.15 × fundamental_F_i_percentile
```

SIC efficiency = E_A / R_A (return per unit of downside risk).

### Concentration

| Metric | Value | Interpretation |
|--------|-------|----------------|
| Herfindahl Index | 0.9926 | Extremely concentrated |
| Effective N | 1.01 | Single-asset dominated |

The benchmark is heavily skewed by the US Steel synthetic bond outlier (99.6%
weight). Excluding USS, the equity benchmark is well-diversified among RSG, WM,
and D.

### CRI ranking

| Rank | Asset | CRI | Signal | Weight |
|------|-------|-----|--------|--------|
| 1 | US Steel [B] | 96.3 | Overweight | 99.6% |
| 2 | RSG [E] | 78.8 | Underweight | 0.19% |
| 3 | WM [E] | 46.3 | Underweight | 0.15% |
| 4 | D [E] | 28.8 | Underweight | 0.03% |

---

## 8. Phase 4 — Hilbert Space Signal Extraction

**File**: `src/analysis/hilbert.py`
**Output**: `data/wte/analysis/hilbert_results.json`

Three independent decomposition methods:

### 8a. FFT spectral analysis

Applies Hann-windowed FFT to each return series. Measures spectral entropy
(0 = perfect signal, 1 = white noise) and signal-to-noise ratio.

| Asset | Entropy H | SNR (dB) | Dominant period |
|-------|-----------|----------|-----------------|
| RSG | 0.937 | -3.1 | 2.6 days |
| USS | 0.999 | -9.5 | 4.0 weeks |
| D | 0.932 | -3.1 | 2.6 days |
| WM | 0.937 | -3.0 | 2.6 days |
| MARKET | 0.942 | -3.4 | 1.4 weeks |

High entropy (~0.93–0.99) and negative SNR confirm market efficiency — returns
are dominated by noise with minimal exploitable structure.

### 8b. Wavelet decomposition (db4, 8 levels)

Manual 8-level Daubechies-4 wavelet decomposition (no pywt dependency).

| Level | Band | Description |
|-------|------|-------------|
| D1 | 1–2 days | Intraday noise |
| D2 | 2–4 days | Short-term swings |
| D3 | 4–8 days | Weekly cycles |
| D4 | 8–16 days | Bi-weekly |
| D5 | 16–32 days | Monthly |
| D6 | 32–64 days | Quarterly |
| D7 | 64–128 days | Semi-annual |
| D8 | 128–256 days | Annual |
| A8 | >256 days | Long-term trend |

Trend/noise ratio for equity assets: 0.006–0.008 (noise-dominated).
USS bond series: T/N = 0.42 (strongest trend signal — the acquisition premium).

### 8c. DMD / Koopman mode decomposition

Time-delay embedding (n_delays=5) on cumulative log returns for RSG, D, WM.
SVD-based extraction of dynamical modes.

| Mode | Period | Growth | Energy | Stable |
|------|--------|--------|--------|--------|
| 0 (DC/trend) | ∞ | -0.0013 | 54.6% | Yes |
| 1 | 24.9 years | +0.0000 | 22.7% | No |
| 2 | 24.9 years | +0.0000 | 22.7% | No |

Dominant mode is a slowly decaying DC trend (54.6% of variance). The 24.9-year
oscillation captures the ultra-low-frequency co-movement of the three equities.
Reconstruction error = 85.5% — most return variance is stochastic noise not
captured by 3 modes.

---

## 9. Phase 5 — Extended Omega & Integrated Risk Score

**File**: `src/analysis/extended_risk.py`
**Output**: `data/wte/analysis/extended_risk_results.json`

### Extended Omega variants

Three signal-adjusted Omega measures, each incorporating a different
decomposition from Phase 4:

```
Spectral Omega:  Ω_S = Ω × (1 + 0.25 × (1 - H_norm))
Wavelet Omega:   Ω_W = Ω × (1 + 0.15 × ln(1 + T/N))
Dynamic Omega:   Ω_D = Ω × (1 + 0.10 × (f_stable - 0.5))
```

| Parameter | Meaning |
|-----------|---------|
| H_norm | Spectral entropy [0,1]. Lower = more signal → larger boost |
| T/N | Wavelet trend/noise ratio. Higher = more trend → larger boost |
| f_stable | Fraction of stable DMD modes. Higher = more predictable → larger boost |

### Integrated Risk Score

```
IRS = 0.40 × Ω_S + 0.35 × Ω_W + 0.25 × Ω_D
```

### Signal quality classification

| Level | Criteria | Interpretation |
|-------|----------|----------------|
| Strong | H < 0.85 AND T/N > 0.05 | Exploitable structure |
| Moderate | H < 0.95 AND T/N > 0.01 | Some structure |
| Weak | Everything else | Efficient / noise-dominated |

### WTE results

| Rank | Asset | IRS | Signal | Ω_S | Ω_W | Ω_D | S_Omega |
|------|-------|-----|--------|-----|-----|-----|---------|
| 1 | USS [B] | 35,700 | Weak | 35,659 | 35,659 | 35,823 | 8,932% |
| 2 | RSG [E] | 1.139 | Weak | 1.148 | 1.131 | 1.135 | 17.08% |
| 3 | WM [E] | 1.107 | Weak | 1.116 | 1.099 | 1.103 | 13.24% |
| 4 | D [E] | 1.013 | Weak | 1.022 | 1.006 | 1.010 | 2.95% |

All 4 assets classified "weak signal" — consistent with efficient market
hypothesis for large-cap equities and actively traded bonds.

---

## 10. Phase 6 — Synthetic Bond Returns

**File**: `src/analysis/synthetic_returns.py`
**Invoked by**: Phase 2 S_Omega for bond-only obligors

### 4-priority cascade

For obligors without equity tickers (US Steel, Reworld, Novelis, all municipal
issuers), the synthetic returns builder constructs a return series from
bond-specific data sources in priority order:

| Priority | Source | Method | Coverage |
|----------|--------|--------|----------|
| P1 | EMMA secondary market trades | Log returns between consecutive trades | Highest fidelity |
| P2 | Rating event shocks | Spread-duration model (±5 day proximity filter) | Supplements P1 |
| P3 | Fundamental drift | DSCR/revenue changes → spread moves | Fills > 180-day gaps |
| P4 | Coupon carry interpolation | Monthly accrual at coupon rate | Baseline fill |

### Rating-to-spread table

Maps S&P (AAA–D) and Moody's (Aaa–Ca) ratings to basis points over AAA MMD.
Used by P2 to convert rating transitions into return shocks.

### Modified duration model

```
ModDur ≈ (maturity × (1 - cpn/2)) / (1 + yield/2)
```

Used to translate spread changes into price returns:
`ΔP/P ≈ -ModDur × Δspread`

### WTE application

US Steel synthetic series: 80 observations from 78 EMMA trades + 2 rating
shock insertions. Coupon = 5.45%, ModDur = 25.1 years. The series captured the
Nippon Steel acquisition premium, producing the extreme Omega values noted
throughout.

---

## 11. Key Findings for Caldor 2026

### What the WTE universe looks like

1. **Dominated by corporate conduit bonds**: The $100M+ WTE universe is
   primarily large-cap industrial companies (utilities, steel, waste
   management) using IDA conduit structures for facility financing. Pure-play
   WTE operators like Covanta/Reworld went private.

2. **Strong fundamental quality at the top**: RSG (70.0), USS (67.1), D (66.1),
   WM (60.4) all score well on the Summers fundamental scale. The WTE sector
   benefits from essential-service revenue streams and investment-grade credit.

3. **Modest risk-adjusted returns**: RSG leads at 17.08% S_Omega, WM at
   13.24%. Dominion Energy lags at 2.95% — reflecting the utility's
   lower-risk/lower-return profile.

4. **No exploitable signal structure**: All assets show weak Hilbert space
   signals (entropy > 0.93, SNR < -3 dB). The WTE bond and equity markets are
   informationally efficient.

5. **Bond benchmark from 48 EMMA trades**: 582 trading dates provide a
   meaningful municipal bond sector benchmark for spread analysis.

### Implications for Caldor positioning

- **Comparable universe**: IDA conduit revenue bonds in the WTE/resource
  recovery space (e.g., Cumberland County NJ, FL Development Finance Corp,
  Iowa Finance Authority) are the structural comparables.
- **Credit benchmarks**: DSCR benchmarks from 83 financial reports across the
  WTE corpus provide peer data for Caldor's 1.34x base case.
- **Rating agency perspective**: 29 rating actions reveal S&P/Moody's focus
  areas for WTE credits — useful for structuring Caldor's credit story.
- **Pricing guidance**: The 48-bond EMMA trade benchmark provides spread context
  for Caldor's pricing relative to the WTE peer group.

---

## 12. Output Files

All analysis outputs are at `emma/bond_os_extractor/data/wte/analysis/`:

| File | Size | Content |
|------|------|---------|
| `fundamental_scores.json` | 64 KB | 25 obligor scores with dimension breakdowns |
| `s_omega_results.json` | 11 KB | 4-asset S_Omega, Omega curves, SIC matrices |
| `benchmark_results.json` | 5 KB | CRI ranking, benchmark composition, HHI |
| `hilbert_results.json` | 14 KB | FFT, wavelet, DMD decompositions |
| `extended_risk_results.json` | 4 KB | IRS ranking, extended Omega variants |

Extraction outputs: `data/wte/extracted/{event_filing,financial_report,rating_action}/`
Corpus database: `data/wte/corpus.db`
Ticker data: `data/tickers/wte/{D,SO,NUE,MT,BP,WM,RSG,GFL,CNR}/`

---

## 13. Known Issues & Limitations

1. **US Steel synthetic bond outlier**: Omega = 35,659x from Nippon Steel
   acquisition premium. Distorts benchmark (HHI = 0.99). Equity-only analysis
   is more meaningful for sector comparison.

2. **Covanta/Reworld private**: The largest US pure-play WTE operator went
   private in 2021. No equity data available. EMMA bond data exists but
   produces limited return observations.

3. **Conduit vs. borrower ambiguity**: IDA bonds are issued by the conduit
   authority but credit risk resides with the corporate borrower. The obligor
   mapping resolves this via alias matching, but some documents may reference
   the conduit name without identifying the borrower.

4. **Image-only SEC filings**: 17 PDFs (32–148 MB) from RSG, Dominion Energy,
   and others were scanned images with 0 extractable text. The 30 MB cap
   prevents wasted processing but means some 10-K data is missing.

5. **4 of 25 investable**: The pipeline's data diversity requirement (rating
   actions + financial reports) filters out obligors with single-source data.
   Nucor (F_i=65.0) and Southern Company (F_i=62.0) would qualify on score
   alone but lack rating action evidence in the WTE extraction corpus.
