# Summers Analytical Framework — Municipal Bond Adaptation

**Version:** 1.0 | **Created:** 2026-02-18
**Source Papers:**
- Paper 1: "An Intuitive True Total Risk-Adjusted Performance Measure and Characteristics Matrix" (Summers, 2023)
- Paper 2: "The Standard Model of Complex Economic Systems" (Summers, 2023)
**Implementation:** `emma/bond_os_extractor/src/analysis/` (Phases 1-6)

---

## 1. FRAMEWORK OVERVIEW

The Summers framework is a **dual-methodology** system that integrates fundamental analysis with Hilbert space signal extraction to produce comprehensive, four-moment-aware risk-adjusted performance measures. Originally developed for leveraged liquid assets with daily return data, this document specifies how to apply and adapt it for **municipal bonds** — illiquid, irregularly-traded fixed income instruments with sparse data.

### 1.1 The Pipeline

```
Phase 1: Fundamental Screening (F_i)
    ↓ Investable universe (F_i >= threshold)
Phase 2: S_Omega & SIC Matrix
    ↓ Risk-adjusted performance, risk/return/liquidity characteristics
Phase 3: Benchmark & Composite Ranking (CRI)
    ↓ Relative value, sector positioning
Phase 4: Hilbert Space Signal Extraction
    ↓ Spectral entropy, wavelet trends, DMD modes
Phase 5: Extended Risk Measures (IRS)
    ↓ Signal-adjusted Omega variants
Phase 6: Synthetic Return Series
    ↓ Return data for obligors without equity tickers
```

### 1.2 The Core Innovation

Traditional risk measures (Sharpe, Sortino, VaR) rely on variance (2nd moment) and assume Gaussian returns. Financial returns are demonstrably non-Gaussian — they exhibit fat tails (excess kurtosis) and asymmetry (skewness). The Omega ratio captures all four statistical moments by evaluating the **entire probability distribution** of returns relative to a threshold. Summers transforms the Omega ratio into:

1. **S_Omega**: An intuitive percentage-scaled performance measure relative to the market
2. **SIC Matrix**: A 3x1 matrix decomposing risk, return, and liquidity into annualized terms
3. **Functional extensions**: Hilbert space methods that capture temporal structure and path dependencies

---

## 2. PHASE 1: FUNDAMENTAL SCREENING

### 2.1 Mathematical Specification

The fundamental score F_i for obligor i is a weighted composite:

```
F_i = w_FS * FinancialStability_i + w_P * Profitability_i + w_CQ * CreditQuality_i
    + w_SQ * StructuralQuality_i + w_GM * GrowthMomentum_i
```

Current weights (Summers Paper 2, Section 4.2):
- w_FS = 0.30 (Financial Stability)
- w_P  = 0.20 (Profitability)
- w_CQ = 0.25 (Credit Quality)
- w_SQ = 0.15 (Structural Quality)
- w_GM = 0.10 (Growth/Momentum)

Investable threshold: F_i >= 50.0 (on 0-100 scale)

### 2.2 Implementation Reference
- **File**: `emma/bond_os_extractor/src/analysis/scoring_engine.py`
- **Key functions**: `_score_financial_stability()`, `_score_profitability()`, `_score_credit_quality()`, `_score_structural_quality()`, `_score_growth_momentum()`
- **Current results**: 40 obligors scored, 7 investable (WM 68.3, RSG 67.9, Brevard County 67.2, LA 67.2, CWST 55.0)

### 2.3 Municipal Bond Adaptation

**The fundamental challenge**: Most municipal bond issuers do not have publicly-traded equity, and their financial reporting is annual (not quarterly). The scoring dimensions must be translated to municipal credit metrics.

#### Financial Stability (0.30)
**Equity metrics → Municipal equivalents:**
| Equity Metric | Municipal Equivalent | Data Source |
|--------------|---------------------|-------------|
| Current ratio | Days cash on hand | CAFR/audit |
| Debt-to-equity | Debt per capita or debt/AV | CAFR/audit |
| Cash coverage | Unrestricted net position / DS | CAFR/audit |
| DSCR | DSCR (same concept, different calculation) | Continuing disclosure |

**Sector-specific stability metrics:**
- *Waste*: Franchise exclusivity duration, customer concentration, flow control protections
- *Healthcare (hospital)*: Days cash on hand (150-300+ for IG), cushion ratio, debt-to-capitalization
- *Healthcare (CCRC)*: Entrance fee refund reserves, actuarial funded ratio, working capital
- *Healthcare (senior living)*: Operating reserve fund adequacy, accounts receivable aging
- *Healthcare (behavioral)*: Medicaid pending days, state budget allocation stability

#### Profitability (0.20)
**Equity metrics → Municipal equivalents:**
| Equity Metric | Municipal Equivalent | Target Range |
|--------------|---------------------|--------------|
| Operating margin | Operating margin (revenue - O&M) / revenue | Waste: 20-35%, Hospital: 2-8%, CCRC: 5-15% |
| Net margin | Excess margin (change in net position / revenue) | Positive trend |
| ROA | Return on net assets | >2% |
| EBITDA margin | EBITDA / total revenue | Sector-dependent |

#### Credit Quality (0.25)
This dimension translates directly — rating scales, trajectory, and outlook work identically for municipal credits.
- **Rating conversion**: 21-point scale (AAA=21, AA+=20, ..., D=1) — same scale for Moody's mapped to S&P equivalents
- **Trajectory**: Count of upgrades minus downgrades over trailing 24 months
- **Outlook**: Positive (+10 pts), Stable (0), Developing (-5), Negative (-10)

#### Structural Quality (0.15)
**This dimension is MORE informative for municipal bonds than for equities**, because bond indenture covenants provide explicit structural protections.
- Credit enhancement present (DSRF, insurance, LOC, surety): +25 pts
- Additional bonds test strength: tight (1.50x+) = +20, moderate (1.25-1.50x) = +10, weak (<1.25x) = 0
- Rate covenant: present (+10) / absent (0)
- Revenue pledge: gross (+15) / net (+10) / none (0)
- Lien position: senior (+15) / subordinate (+5) / none (0)

#### Growth/Momentum (0.10)
**Equity metrics → Municipal equivalents:**
| Equity Metric | Municipal Equivalent |
|--------------|---------------------|
| Revenue CAGR | Revenue CAGR (same, but annual) |
| Stock price momentum | N/A for most munis (use spread tightening as proxy) |
| Rating upgrades | Rating trajectory (same) |
| EPS growth | Net income/excess growth |

### 2.4 Adaptation Status
The existing scoring engine (`scoring_engine.py`) handles dual-channel data (equity + bond). For pure municipal credits without equity tickers, the bond-only data path is used. The agent should recommend enhancements to:
1. Add sector-specific scoring templates (waste vs. healthcare vs. future sectors)
2. Incorporate CAFR/audit data as a primary input source for municipal fundamentals
3. Define healthcare-specific stability and profitability metrics (see tables above)

---

## 3. PHASE 2: S_OMEGA AND SIC MATRIX

### 3.1 Mathematical Specification

**Omega Ratio** (Keating-Shadwick, 2002):
```
Omega(theta) = integral[theta to inf](1 - F(r))dr / integral[-inf to theta](F(r))dr
```

**Discrete form** (Kapsos et al., 2014):
```
Omega(theta, R_i) = E[r_ik - theta]+ / E[theta - r_ik]+
```
where (x)+ = max(x, 0)

**Summers Total Risk-Adjusted Performance Measure (S_Omega)**:
```
S_Omega = r_f + E[r_f - r_mk]+ * (E(R_i) - r_f) / E[r_f - r_ik]+
```
or equivalently:
```
S_Omega = r_f + E[r_f - r_mk]+ * (Omega(r_f, R_i) - 1)
```

where:
- r_f = risk-free rate
- r_mk = k-th market return
- r_ik = k-th asset return
- E(R_i) = geometric mean of asset returns
- E[r_f - r_mk]+ = expected downside return of the market
- E[r_f - r_ik]+ = expected downside return of the asset

**Summers Investment Characteristics Matrix (SIC)**:
```
SIC = [R_A(R_i), E_A(R_i), MDDD_S]
```
where:
- R_A = (E[r_f - r_ik]+ + 1)^n_Y - 1  (annualized risk — downside expectation)
- E_A = (E(R_i) + 1)^n_Y - 1  (annualized expected return — geometric mean)
- MDDD_S = MDDD_A + t_R  (Summers max drawdown duration: recovery to peak + recovery of expected return)
- n_Y = number of return periods per year

**Black Swan Probability**:
```
P_BSE(n) = (1/n) * 100%
```

**Accuracy**:
```
A(S_Omega) = 1 - P_BSE(n)
```

### 3.2 Implementation Reference
- **Files**: `omega.py`, `return_series.py`
- **Key classes**: `ReturnSeries`, `SOmegaResult`, `SICMatrix`
- **Key functions**: `compute_omega()`, `compute_s_omega()`, `compute_sic()`, `compute_omega_curve()`

### 3.3 Municipal Bond Adaptation

**Problem**: Municipal bonds trade ~4 times per year on average. Daily return data is unavailable. The S_Omega calculation requires sufficient data points for statistical validity.

**Adaptation strategies**:

1. **Minimum observation threshold**: Currently MIN_OBSERVATIONS = 8 in `synthetic_returns.py`. For S_Omega reliability, recommend:
   - n >= 8: SIC matrix only (R_A, E_A, MDDD_S individually meaningful)
   - n >= 20: S_Omega computation acceptable with caveats
   - n >= 50: S_Omega computation reliable
   - n >= 100: Full confidence in S_Omega
   - Always report P_BSE and A(S_Omega) alongside results

2. **Return frequency normalization**: The `periods_per_year` calculation must handle irregular municipal bond trading. The existing code handles `frequency="irregular"` but defaults to 252 in some paths — verify this is corrected (see Phase 6 fix note in MEMORY.md).

3. **Risk-free rate for tax-exempt securities**: S_Omega uses r_f as the threshold. For tax-exempt bonds:
   ```
   r_f_taxexempt = r_f_treasury * (1 - marginal_tax_rate)
   ```
   Example: If 10Y Treasury = 4.50% and tax rate = 37%, r_f_taxexempt = 2.84%
   This adjustment is critical — using the full Treasury rate as threshold would systematically penalize tax-exempt bonds.

4. **Market benchmark construction**: Cannot use equity indices. Options:
   - EMMA-derived benchmark: Equal-weighted returns from all sector bonds (existing: 1,044 dates from 167 waste sector bonds)
   - AAA MMD as proxy for municipal risk-free rate
   - Sector-specific index (if available from ICE BofA or Bloomberg)
   - For healthcare: will need to build from EMMA healthcare bond trade data

5. **When S_Omega is unreliable**: For obligors with very sparse trade data, fall back to:
   - SIC matrix components individually (R_A tells you annual risk; E_A tells you expected return; MDDD_S tells you liquidity horizon)
   - Fundamental score F_i as the primary ranking metric
   - Qualitative comparable analysis in lieu of quantitative S_Omega

---

## 4. PHASE 3: BENCHMARK & COMPOSITE RANKING

### 4.1 Mathematical Specification

**S_Omega-weighted benchmark**:
```
w_i = max(S_Omega_i, 0) / sum(max(S_Omega_j, 0))
```

**SIC Efficiency** (return per unit of risk):
```
Efficiency = E_A / R_A
```

**Composite Ranking Index (CRI)** (0-100):
```
CRI = 0.40 * rank_s_omega + 0.25 * rank_efficiency + 0.20 * rank_drawdown + 0.15 * rank_f_score
```
where rank_score = (n - rank + 1) / n * 100

**Herfindahl Concentration Index**:
```
HHI = sum(w_i^2)
effective_n = 1 / HHI
```

**Relative Value Signals**:
```
"overweight"  if S_Omega_spread > 0 AND CRI_rank <= n/3
"underweight" if S_Omega_spread < 0 OR CRI_rank > 2n/3
"equal"       otherwise
```

### 4.2 Implementation Reference
- **File**: `benchmark.py`
- **Key classes**: `ConstituentAnalysis`, `SectorBenchmark`, `BenchmarkAnalysis`

### 4.3 Municipal Bond Adaptation

**Thin market effects**: With only 3-6 assets in the investable universe (waste sector), the benchmark is heavily concentrated. HHI will be high and effective_n low.

**Recommendations**:
- Report HHI and effective_n prominently — the user should understand when the benchmark is statistically thin
- For healthcare sector expansion: need minimum 5 investable-grade credits before benchmark construction is meaningful
- Consider cross-sector benchmarking as the universe grows (waste + healthcare combined)
- Weight the CRI components differently for municipal bonds: increase fundamental quality weight (from 0.15 to 0.25) and decrease S_Omega weight (from 0.40 to 0.30) when S_Omega data quality is low

---

## 5. PHASE 4: HILBERT SPACE SIGNAL EXTRACTION

### 5.1 Mathematical Specification

The Standard Model treats financial returns as elements of L^2([0,T]), the Hilbert space of square-integrable functions. Three complementary decomposition methods:

**5.1.1 FFT Spectral Analysis**
```
X(f) = <x, e_f> = integral x(t) * e^(-2*pi*i*f*t) dt
S(w) = |<x, e_w>|^2   (power spectral density)
```
- Shannon entropy: H = -sum(p * log(p)) / log(N), normalized to [0,1]
- SNR: Power(top 10%) / Power(bottom 90%) in dB
- Dominant frequencies: Top peaks with periods and power fractions
- Hann window applied to reduce spectral leakage

**5.1.2 DWT Multi-Resolution Analysis (Wavelet)**
```
x(t) = sum_k c_{J,k} * phi_{J,k}(t) + sum_{j<=J} sum_k d_{j,k} * psi_{j,k}(t)
```
- 8-level Haar/Daubechies-4 decomposition (manual implementation, no pywt dependency)
- Detail levels D1-D7 at scales: 2-4 days through 128-256 days
- Approximation A7: >256 days (trend component)
- Trend-to-Noise ratio: E_trend / E_noise
- Energy distribution per scale

**5.1.3 DMD / Koopman Operator**
For dynamical system x_{t+1} = F(x_t), the Koopman operator K acts on observables:
```
[Kg](x) = g(F(x))
```
DMD provides data-driven approximation:
- Time-delay embedding: enriches state space (n_delays=5)
- SVD decomposition of data matrices X, X'
- Eigendecomposition reveals: frequencies, growth rates, spatial weights
- Stability: |eigenvalue| <= 1 (mean-reverting) vs growing modes

### 5.2 Implementation Reference
- **File**: `hilbert.py`
- **Key insight**: Raw returns are white noise; cumulative log-returns carry dynamical structure (the DMD fix)
- **Current results**: Spectral entropy ~0.94, SNR ~-3dB (confirms efficient market noise for equity returns)

### 5.3 Municipal Bond Adaptation

**Irregular sampling problem**: FFT requires regular (evenly-spaced) time series. Municipal bonds trade irregularly.

**Adaptation strategies**:

1. **Interpolation before FFT**: Resample irregular trade data to regular monthly intervals using linear or cubic interpolation. Accept the information loss — monthly resolution is appropriate for muni credits.

2. **Wavelet decomposition at lower resolution**: With monthly data, the decomposition levels shift:
   - Level 1: 2-month cycles (not 2-4 days)
   - Level 2: 4-month cycles
   - Level 3: 8-month cycles
   - Level 4: 16-month cycles
   - Level 5+: Multi-year trends
   This is actually more informative for munis — relevant credit cycles operate at quarterly/annual scales, not intraday.

3. **DMD embedding dimension**: With fewer data points, reduce n_delays. For monthly muni data:
   - 5 years of monthly data = 60 points
   - n_delays = 3 (enriches to 3N dimensions) is more appropriate than 5
   - Minimum viable: 36 data points with n_delays = 2

4. **Interpretation shift**: For municipal bonds, Hilbert space signals should be interpreted differently:
   - **Spectral entropy near 1.0**: Expected and not concerning — municipal bond returns ARE largely noise-like at high frequencies. The signal exists at low frequencies (credit cycles, economic cycles).
   - **Wavelet trend energy**: More informative for munis — look for trend components at 12-36 month scales corresponding to credit improvement/deterioration cycles.
   - **DMD stable modes**: Stable modes in muni returns likely correspond to coupon carry (the steady-state return of holding a bond to maturity).

5. **Signal quality expectations**: Set different "strong/moderate/weak" thresholds for municipal bonds:
   - **Strong signal**: H < 0.90 (more lenient than 0.85 for equities) AND T/N > 0.03
   - **Moderate signal**: H < 0.97 AND T/N > 0.005
   - **Weak signal**: Everything else (most muni credits will fall here — this is expected, not a failure)

---

## 6. PHASE 5: EXTENDED RISK MEASURES

### 6.1 Mathematical Specification

Three extended Omega variants that incorporate signal quality from Phase 4:

**Spectral Omega**:
```
Omega_S = Omega * (1 + alpha_S * (1 - H_norm))
```
where alpha_S = 0.25, H_norm = normalized spectral entropy [0,1]

**Wavelet Omega**:
```
Omega_W = Omega * (1 + alpha_W * log(1 + T/N))
```
where alpha_W = 0.15, T/N = trend-to-noise energy ratio

**Dynamic Omega**:
```
Omega_D = Omega * (1 + alpha_D * (f_stable - 0.5))
```
where alpha_D = 0.10, f_stable = energy-weighted fraction of stable DMD modes

**Integrated Risk Score (IRS)**:
```
IRS = 0.40 * Omega_S + 0.35 * Omega_W + 0.25 * Omega_D
```

**Signal quality classification**:
```
"strong"   if H < 0.85 AND T/N > 0.05
"moderate" if H < 0.95 AND T/N > 0.01
"weak"     otherwise
```

### 6.2 Implementation Reference
- **File**: `extended_risk.py`
- **Current results**: City of LA IRS=10.86 (#1), Mission 5.79 (#2), Brevard 2.36 (#3), RSG 1.12 (#4), WM 1.09 (#5), CWST 1.08 (#6)

### 6.3 Municipal Bond Adaptation

**Alpha coefficient recalibration**: The current alpha values (0.25, 0.15, 0.10) were tuned for equity markets where signal quality varies meaningfully across assets. For municipal bonds where most credits will show "weak" signal quality, these coefficients may need adjustment:

**Proposed muni-adapted coefficients**:
- alpha_S_muni = 0.35 (increase spectral premium — when a muni credit DOES show spectral structure, it's more meaningful because it's rarer)
- alpha_W_muni = 0.25 (increase wavelet premium — trend detection at quarterly/annual scales is the most informative signal for munis)
- alpha_D_muni = 0.10 (keep dynamic coefficient — DMD is least reliable with sparse data)

**IRS weight adjustment for munis**:
```
IRS_muni = 0.30 * Omega_S + 0.45 * Omega_W + 0.25 * Omega_D
```
Rationale: Shift weight from spectral (global frequency, less informative for irregular data) to wavelet (time-localized, better for regime detection in credit cycles).

**Validation requirement**: These adjustments are hypotheses. The agent should:
1. Document the proposed changes as a model proposal
2. Run both equity-calibrated and muni-calibrated versions on the existing corpus
3. Compare rankings to assess whether recalibration changes relative positioning
4. Only adopt if the muni-calibrated version produces more intuitively correct rankings

---

## 7. PHASE 6: SYNTHETIC RETURN SERIES

### 7.1 Cascading Priority Model

For obligors without equity tickers, the synthetic return builder constructs return series from bond data using a 4-priority cascade:

**Priority 1 — EMMA Secondary Market Trades** (highest fidelity):
```
Total Return = (P_t - P_{t-1} + Accrued_Coupon) / P_{t-1}
Accrued_Coupon = Annual_Coupon_Rate * Days_Between / 365
```

**Priority 2 — Rating Event Shocks** (spread-duration model):
```
Return = -Delta_Spread_bps * Modified_Duration / 10000
```
Only inserted if no EMMA trade within +/- 5 days of rating action.

**Priority 3 — Fundamental Drift** (DSCR/revenue → spread):
```
DSCR_improvement: -50 bps per +0.1x DSCR
Revenue_growth: -30 bps per +10% revenue growth
Return = spread_change_to_return(delta_bps, mod_duration)
```

**Priority 4 — Coupon Carry Interpolation** (fills gaps > 180 days):
```
Monthly_Carry = Annual_Coupon_Rate / 12
```

**Modified Duration Estimate**:
```
ModDur ≈ (Maturity * (1 - Coupon/2)) / (1 + Yield/2)
```

### 7.2 Implementation Reference
- **Files**: `synthetic_returns.py`, `spread_table.py`, `return_series.py`
- **Key function**: `build_synthetic_returns()` — main orchestrator
- **Minimum observations**: 8 (MIN_OBSERVATIONS in config)

### 7.3 Municipal Bond Adaptation Status

This phase is already muni-adapted — it was designed specifically for municipal bond obligors. Key notes:
- The spread table (`spread_table.py`) covers S&P (AAA-D) and Moody's (Aaa-Ca) → bps over AAA MMD
- For healthcare sector expansion: verify that the spread table adequately covers healthcare-typical ratings (A to BBB range for hospitals; BBB to BB for CCRCs)
- May need healthcare-specific spread adjustments (healthcare bonds typically trade 10-25 bps wider than general revenue at same rating)

---

## 8. ANALYTICAL EVOLUTION PROTOCOL

This section defines how the agent should approach extending and improving the Summers framework.

### 8.1 Citation Study Protocol

Paper 2 cites 95 references. Priority citations for municipal bond application:

**Highest priority** (directly relevant to muni adaptation):
- [8] Keating & Shadwick (2002) — Omega ratio foundational paper
- [9] Kapsos et al. (2014) — Discrete Omega reformulation
- [14] Modigliani & Modigliani (1997) — M2 measure
- [28] Percival & Walden (2000) — Wavelet methods for time series
- [29] Gencay et al. (2001) — Wavelets in finance and economics
- [40] Schmid (2010) — Dynamic Mode Decomposition

**High priority** (inform theoretical understanding):
- [1] Mandelbrot (1963) — Fat tails in financial data
- [25] Taleb (2007) — Black swan theory
- [27] Ramsay & Silverman (2005) — Functional data analysis
- [33] Dashti & Stuart (2017) — Bayesian inverse problems
- [88] Lo (2004) — Adaptive Markets Hypothesis

**Medium priority** (potential extensions):
- [31] Calvet & Fisher (2002) — Multifractality in asset returns
- [44] Cuturi et al. — RKHS for financial time series
- [58] Rasmussen & Williams — Gaussian processes

### 8.2 Model Development Workflow

When proposing a new analytical model:

1. **Hypothesis Document** (`research/models/proposals/MODEL_NAME_proposal.md`):
   ```yaml
   ---
   model_name: "Name"
   hypothesis: "What this model does and why"
   summers_section: "Which section of the Summers papers it extends"
   muni_motivation: "Why this is needed for municipal bonds specifically"
   status: proposed | approved | implemented | validated | rejected
   ---
   ```

2. **Mathematical Specification**: LaTeX-compatible equations with variable definitions

3. **Implementation Plan**: Python module spec, input data requirements, computational complexity

4. **Validation Strategy**: What data to test against, what "success" looks like, how to compare to baseline

5. **User Approval Gate**: Models are never auto-deployed. The user reviews the proposal and decides.

### 8.3 Dataset Building Workflow

When building new datasets:

1. **Gap Identification**: What sector/metric is missing? What analysis is blocked by the gap?

2. **Source Inventory**: Where can the data be obtained?
   - EMMA: Bond filings, trade data, continuing disclosures
   - EDGAR: SEC filings (for 501(c)(3) and PAB issuers)
   - Rating agency publications: Methodology docs, sector studies
   - GFOA: Best practices, benchmarking data
   - State-specific: State treasurer reports, debt databases
   - CMS (for healthcare): Medicare Cost Reports, Medicaid data

3. **Schema Design**: Define fields, types, validation rules, sources per field

4. **Collection Plan**: Manual extraction, crawler modification, or API access

5. **Quality Protocol**: Validation rules, completeness thresholds, anomaly detection

6. **Storage**: `research/datasets/` with full schema documentation per Section 4.2 of charter

### 8.4 Capability Log

Maintain `research/agent/capability_log.md` with running record of:
- Date, action type (literature review / model proposal / dataset creation / framework extension)
- Summary of what was learned or produced
- Impact on the Summers framework adaptation
- Open questions for follow-up

---

## 9. FUTURE EXTENSIONS

### 9.1 Bayesian Signal Integration (Paper 2, Section 4.3.5)

The full Summers framework includes Bayesian integration of spectral, wavelet, and DMD signals:
```
P(x|S) ∝ P(S|x) * P(x)
```
where S = {S_F, S_W, S_P} are the extracted signals and x is the market state in Hilbert space.

This is **not yet implemented** in the existing pipeline. For municipal bonds, the Bayesian layer would:
- Adaptively weight signal types based on data quality (sparse data → higher prior weight on wavelet trends)
- Incorporate regime detection (bull/bear municipal markets, rate cycle position)
- Update signal weights as new trade data arrives

### 9.2 Network-Adjusted Omega (Paper 2, Section 5.3)
```
Omega_N(theta, R_i) = E[r_ik - theta]+ / (C_i * E[theta - r_ik]+)
```
where C_i is the centrality of asset i in the correlation network.

For municipal bonds: network effects are relevant (sector contagion, geographic correlation, credit enhancer exposure). Building the correlation network requires sufficient cross-asset trade data.

### 9.3 Functional Omega Extension (Paper 2, Section 5.2)
```
Omega_F(theta, tau) = E[(C_tau[r] - theta)+] / E[(theta - C_tau[r])+]
```
where C_tau[r] is the cumulative return operator over window tau.

This extension captures path dependencies — particularly relevant for CAB structures where accretion creates non-linear return paths.

### 9.4 Cross-Sector Factor Models

As the corpus expands beyond waste/environmental, opportunities emerge for:
- Cross-sector credit factor extraction (common factors driving muni defaults)
- Sector rotation signals (shifting allocation between waste, healthcare, future sectors)
- Systematic risk decomposition (rate risk vs credit risk vs sector risk)

---

## 10. IMPORTANT CAVEATS

1. **Summers' methodology was developed for liquid assets with dense return data**. Every adaptation in this document represents an extension beyond the original paper's validated domain. Results should be interpreted with appropriate humility.

2. **Municipal bond markets are structurally different from equity markets**: buy-and-hold investor base, tax-advantaged returns, credit-driven rather than growth-driven, politically-influenced supply. These structural differences may limit the applicability of signal extraction methods designed for equity markets.

3. **The synthetic return cascade (Phase 6) introduces model risk**: P2 (rating shocks) and P3 (fundamental drift) returns are model-estimated, not market-observed. They should be weighted less than P1 (actual trades) in any analysis.

4. **Small sample sizes are the norm, not the exception**: Municipal bond analysis will frequently operate at the minimum viability threshold. Report confidence intervals and P_BSE alongside all quantitative results.

5. **The agent should actively seek to improve these adaptations** through literature study, empirical testing, and user feedback. The muni adaptation is a living document, not a fixed specification.
