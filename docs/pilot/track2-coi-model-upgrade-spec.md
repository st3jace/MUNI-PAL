# Track 2 — COI Model Upgrade Feature Spec

**Status:** Draft v1
**Date:** 2026-04-07
**Owner:** Bond Strategist (executor) + CEO (decision authority on claim language)
**Estimated effort:** 5–8 working days, end-to-end
**Dependency on Track 1 (pilot):** None. Track 2 runs in parallel and does not block on Adventist.

---

## Purpose

The COI prediction model currently reports a $2.78/1000 holdout MAE — a downgrade from the previously claimed $1.80. The downgrade was caused by missing predictors, not model architecture. This spec defines a one-week sprint to add the missing predictors using **structured tabular features only** (no spectral analysis, no emma-core integration, no new crawl), refit with proper temporal cross-validation, and report MAE *sliced by sub-sector and rating bucket* so the model's strengths and weaknesses can be claimed honestly.

The deliverable is not a better single MAE number. The deliverable is a set of **slice-specific accuracy claims** that we can put in front of buyers and counsel without flinching.

> **Why this matters now:** Track 1 (pilot) addresses the operational claims (#3, #5, #9). Track 2 addresses the analytical claims (#10, and indirectly #1, #4). Both tracks must move for the revised board report to hold together. Track 2 is faster, cheaper, and entirely under our control — there is no excuse for it not being done within a week.

---

## Scope

### In scope
- Add structured features to the 39-deal Full Itemized COI dataset
- Refit the existing regression model with the expanded feature set
- Replace random 80/20 split with **walk-forward temporal cross-validation**
- Report MAE **globally** AND **by sub-sector** AND **by rating bucket** AND **by deal-size bucket**
- Generate the slice-specific claim language for marketing review
- Update the Confidence Matrix in the board report (Claim #10)

### Explicitly out of scope
- Crawling new deals (that's the corpus expansion workstream — separate)
- Changing the model class (no XGBoost, no neural nets — keep the regression so the coefficients remain interpretable to bond professionals)
- Touching emma-core (different problem, different product)
- Re-running the holdout against deals not in the current 39-deal set
- Building any UI changes — this is a backend model refit, not a feature

### Anti-scope (things to *not* do because they're tempting)
- Do not engineer interaction features until the main effects are clean. Premature interactions hide weak main effects.
- Do not impute missing values silently. Missingness is data — encode it explicitly (see §4).
- Do not drop the existing $2.78 model results. Keep them as the v1 baseline so the improvement (or lack of it) is provable.

---

## Features to Add

The current model uses (per Bond Strategist's prior work) some subset of: par size, year, sub-sector, possibly sale method. The features below are additions or formalizations.

| # | Feature | Type | Source | Why it matters | Imputation strategy |
|---|---|---|---|---|---|
| 1 | **Underlying rating at issuance (Moody's)** | Ordinal (Aaa=1 ... C=21) | OS cover, rating agency reports | Credit quality is the missing-predictor confessed in the original revision memo. Single biggest expected lift. | Encode missing as separate "unrated" category. Do not impute. |
| 2 | **Underlying rating at issuance (S&P)** | Ordinal | OS cover | Some deals have S&P only or both. Use whichever is available; if both, use the lower (more conservative). | "Unrated" category. |
| 3 | **Credit enhancement flag** | Categorical: none / insured / LOC / state credit / other | OS cover | Insured deals price differently and have different COI structures (insurance premium is itself a COI line item). | None = explicit. |
| 4 | **Enhancer identity** | Categorical: AGM/Assured, BAM, FHA/HUD §242, state credit program, LOC, none, other | OS cover | Different enhancers have fundamentally different cost structures. FHA/HUD §242 in particular has its own closing cost regime that reshapes the entire COI profile — omitting it collapses meaningful variance into noise. State credit programs (Cal-Mortgage, DASNY enhanced, etc.) similarly distinct. | "None" if no enhancement. |
| 5 | **Obligor type** | Categorical: standalone community hospital / academic medical center / multi-hospital system / obligated group / FQHC / SL community / SL system / behavioral | OS cover, dataset | System deals have different MA and counsel cost structures than single-facility deals. **Split standalone community hospital from academic medical center** — AMCs have complex conduit structures, multiple obligated groups, and materially higher counsel costs. Treating them as one category collapses meaningful variance. | Required field — flag rows where unclear and review manually. |
| 6 | **Deal structure** | Categorical: new money / refunding / mixed | OS cover, use of proceeds | Refundings have different counsel intensity and different rating agency dynamics than new money. | Required field. |
| 7 | **Number of series** | Integer | OS cover | More series = more counsel work = higher COI. Cheap to extract, likely meaningful. | Default to 1 if unclear. |
| 8 | **Tax status** | Categorical: tax-exempt / taxable / mixed | OS cover | Taxable healthcare deals have different investor base and different cost structures. | Required field. |
| 9 | **Rate mode** | Categorical: fixed / variable / mixed | OS cover | VRDOs have remarketing agent fees as a recurring COI component. | Default to fixed if unclear. |
| 10 | **Sale method** | Categorical: negotiated / competitive / private placement | OS cover | Already in some versions of the model — formalize. Negotiated is the dominant healthcare mode. | Required field. |
| 11 | **Lead UW identity** | Categorical: top-10 named + "other" | OS cover | Healthcare-specific top 10: Ziegler (dominant in SL), BofA Securities, JPMorgan, Citigroup, Morgan Stanley, RBC Capital, Piper Sandler, Goldman Sachs, Barclays, Wells Fargo. (Raymond James dropped — less dominant in HC than Goldman. Barclays and Wells Fargo added — both materially active in large hospital system deals.) UW identity correlates with COI level. | "Other" bucket. |
| 12 | **Co-manager count** | Integer | OS cover | More co-managers = more underwriter discount distribution but not necessarily more total UW cost. Test the effect. | Default to 0. |
| 13 | **Issuance year** | Integer | Already present | Captures secular trend. **Critical:** must be the predictor we control for when claiming repeat-issuer effects. | Required. |
| 14 | **Sub-sector** | Categorical: hospital / SL-CCRC / FQHC / behavioral | Already present | Already in model. Formalize as one-hot. | Required. |
| 15 | **Par size (log)** | Continuous | Already present | Log-transform — COI scales sub-linearly with par. Confirm log is better than linear via residual plot. | Required. |
| 16 | **State** | Categorical: top-10 + other | OS cover | State-level legal regimes (state issuer requirements, state counsel norms) materially affect COI in some states. | "Other" bucket. |
| 17 | **Issuer type** | Categorical: state authority / county / city / 501(c)(3) conduit / other | OS cover | Conduit issuer cost structures differ. | Required. |

**Total: 17 features.** Not all will survive feature selection. The hypothesis is that #1 (rating), #5 (obligor type), #6 (deal structure), and #11 (lead UW) are the four with the largest expected lift.

---

## Data Collection Protocol

Adding 17 features × 39 deals = ~660 cells. Some are already in the dataset; the new fields need to be extracted from the OS PDFs.

**Process:**
1. Build a feature-extraction spreadsheet template with one row per deal, one column per feature, plus a "source page" column for each new field so the extraction is auditable.
2. Bond Strategist (or research-facility analyst) extracts each field from each OS, **reading the cover and front matter** rather than the full document. Estimated 15 minutes per deal × 39 = ~10 hours total.
3. **Two-pass quality control:** the extractor flags any uncertain field. A second person (CEO or another analyst) reviews flagged fields against the source PDF.
4. **Do not paraphrase categorical values.** Use the controlled vocabulary in §3 exactly. Free-text drift (e.g., "Acute Care Hospital" vs "Hospital") is the #1 cause of garbage features.
5. Save the completed spreadsheet as `data/coi_dataset/itemized_v2_features.csv` with a row-level changelog.

**Time estimate:** 15 minutes per deal is optimistic for straightforward covers; deals with multiple series, complex conduit structures, or poorly formatted OS documents will run 25–30 minutes each. Budget **20 hours for extraction** (not 10) + 4 hours for QC = **~3 days total**, not 2. This is a 1-day slip from the initial estimate, not a sprint risk — but set expectations correctly with the day-by-day sequencing in §9.

---

## Model Refit Protocol

### Architecture
- **Same model class as v1.** Linear regression, ridge regression, or whatever the current model uses. **Do not change the model class** in this sprint — the goal is to test whether features improve accuracy, not to confound feature improvement with model improvement.
- One-hot encode all categoricals.
- Log-transform par size. Check residuals to confirm log is appropriate.
- Standardize continuous features.

### Cross-validation: walk-forward, not random
The original $1.80 → $2.78 revision was caused in part by walk-forward CV exposing the temporal leakage in random splits. Stick with walk-forward.

**Specific protocol:**
- Sort deals by issuance date.
- Use the earliest 60% as initial training set.
- Predict the next deal, log the error, add it to training, predict the next deal, etc.
- Final reported MAE is the mean absolute error across all walk-forward predictions.
- Also report: median AE, 90th percentile AE, max AE. The mean alone hides outlier behavior.
- **Report the walk-forward MAE with a bootstrap 95% confidence interval** (e.g., "MAE = $2.10 ± $0.45, 95% CI [$1.65, $2.55]"). With n=39 and walk-forward evaluation, the per-step MAE will be noisy. A point estimate implies false precision. A sophisticated buyer — or counsel reviewing marketing language — will expect to see the interval.

### Feature selection
- Fit the full model first. Report all coefficients with confidence intervals.
- Drop features whose coefficient CIs cross zero AND whose removal does not increase walk-forward MAE.
- **Document every dropped feature** in the model card (§6). Dropped is not deleted — future data may revive a feature.

### Slice reporting
This is the deliverable that matters most.

After the final model is fit, report MAE on these slices:

| Slice | Why |
|---|---|
| Global (all 39) | Headline number, comparable to v1's $2.78 |
| Hospital sub-sector only | Largest slice (n≈25), most defensible claim |
| Senior living only | Smallest slice (n≈1 per master CSV) — report but flag as not statistically meaningful |
| Investment grade only (rating ≤ Baa3 or BBB-) | The slice we expect to be most accurate |
| Below investment grade or unrated | The slice we expect to be least accurate — name it explicitly |
| Par > $100M | Large deals, where COI/$1000 stabilizes |
| Par < $50M | Small deals, where COI/$1000 has high variance |
| 2020 onward | Recent deals, less affected by secular trend errors |
| Negotiated only | Dominant sale method |

Each slice gets: n, mean AE, median AE, 90th percentile AE.

---

## Deliverables

1. **`data/coi_dataset/itemized_v2_features.csv`** — the expanded dataset
2. **`models/coi_v2/model.pkl`** (or equivalent) — the refit model
3. **`models/coi_v2/model_card.md`** — the model card (§6 below)
4. **`docs/coi_v2_results.md`** — the results memo with all slice MAEs and the marketing language proposal
5. **Updated Confidence Matrix entry for Claim #10** — proposed diff against the current board report
6. **Marketing language proposal** — three drafted sentences, ranked from most-defensible to most-aggressive, for CEO selection

---

## Model Card Requirements

The model card must include:

- **Intended use:** What this model is for (predicting COI for healthcare municipal bond issuances at the pre-pricing stage).
- **Out-of-scope use:** What this model is *not* for (predicting COI for non-healthcare deals; predicting COI for distressed credits without a meaningful credit feature; predicting COI more than 18 months into the future).
- **Training data:** n=39 itemized deals, date range, sub-sector breakdown, rating distribution, par size distribution.
- **Features used:** Final list after feature selection.
- **Features dropped:** With reason.
- **Performance:** All slice MAEs from §5.
- **Known limitations:** At least three. Suggested starters: (1) sub-sector imbalance — hospital is well-represented, SL is a single deal; (2) rating coverage — n unrated deals; (3) no recession-period deals in the training set.
- **Monitoring plan:** How we will detect model drift (e.g., compare predicted vs actual on every new deal added to the dataset, alert if rolling MAE exceeds threshold).
- **Versioning:** v2.0, supersedes v1. v1 results preserved for comparison.

The model card is the artifact counsel and buyers will both ask to see. Write it like both audiences are reading it.

---

## Marketing Language Proposal

The output of the sprint must include three drafted sentences, ranked, for CEO selection. Example structure:

**Most defensible (lowest claim):**
> "Across 39 healthcare bond issuances with full itemized COI data, our model predicts total cost of issuance with a mean absolute error of $[X]/1000 of par, with accuracy improving to $[Y]/1000 for investment-grade hospital deals (n=[Z])."

**Middle:**
> "Our COI prediction model achieves $[Y]/1000 accuracy on investment-grade hospital deals — the slice that represents [%] of healthcare municipal bond issuance by volume."

**Most aggressive (still defensible):**
> "For investment-grade hospital borrowers, Muni-Pal predicts cost of issuance to within $[Y]/1000 — typically representing less than [%] of total deal cost."

**Note:** The CEO picks one. The aggressive version may be fine if the slice MAE supports it. The point is that the choice is made deliberately, with the data in hand, not as a marketing wish.

---

## Decision Rules

Walk-forward CV results determine what we claim:

| Investment-grade hospital slice MAE | Action |
|---|---|
| < $1.50/1000 | Strong claim. Lead with this slice in marketing. Investigate the lift over v1 carefully — if it's much better than expected, look for leakage. |
| $1.50–$2.10/1000 | Defensible claim. Use the most-aggressive marketing language. This is the expected outcome and would recover the original $1.80 headline honestly. |
| $2.10–$2.50/1000 | Modest improvement. Use middle marketing language. Acknowledge that more data is needed. |
| $2.50–$2.78/1000 | Marginal improvement. Use most-defensible marketing language. Investigate whether the model needs structural changes (different model class, interaction features) before claiming material improvement. |
| > $2.78/1000 | The features did not help. Do not ship. Diagnose: extraction errors? Wrong features? Bad QC? Investigate before any marketing change. |

**Important:** the CEO does not pick the marketing language until after the sprint completes. The decision rules above bind the choice to the data.

---

## Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Feature extraction errors corrupt the dataset | Two-pass QC. Source page recorded for every extracted field. |
| Walk-forward CV gives unstable estimates because n=39 is small | Report variance across walk-forward steps, not just the mean. If variance is high, say so in the model card. |
| One sub-sector dominates the global MAE | This is *why* we report sliced. The global number is informational; the slice numbers are the claims. |
| Bond Strategist starts feature engineering / model class changes mid-sprint | Scope is locked. Anything beyond the 17 features in §3 and the existing model class is out of scope. Add to a v3 backlog instead. |
| The model gets *worse* with new features | That's a real finding. Investigate (collinearity? overfit? extraction error?) and report honestly. Do not ship a worse model and do not hide the result. |
| Sprint slips past one week | Hard cap at 8 working days. If not done by then, ship what's done and finish in a follow-up. Better to have v1.5 in hand than v2 in flight. |

---

## Sequencing and Hand-off

| Day | Activity | Owner |
|---|---|---|
| 1 | Build extraction template; pull all 39 OS PDFs into one folder | Bond Strategist |
| 2–3 | Extract features for all 39 deals | Bond Strategist + analyst if available |
| 3 | QC pass on flagged fields | CEO or second analyst |
| 4 | Refit model, run walk-forward CV, generate slice MAEs | Bond Strategist |
| 5 | Write model card and results memo | Bond Strategist |
| 5 | Marketing language proposal (3 ranked options) | Bond Strategist |
| 6 | CEO review of results memo and marketing language | CEO |
| 6 | CEO selects marketing language; updates Confidence Matrix entry for Claim #10 | CEO |
| 7 | Buffer / rework day | — |
| 8 | Hard ship date | — |

---

## Definition of Done

- [ ] All 17 features extracted for all 39 deals; QC complete; dataset saved
- [ ] Walk-forward CV results computed and reported globally and on all slices in §5
- [ ] Model card published and reviewed by CEO
- [ ] Three marketing language options drafted; one selected by CEO
- [ ] Confidence Matrix Claim #10 updated with diff against board report Rev 2
- [ ] v1 results preserved alongside v2 for comparison
- [ ] Model card has at least three named limitations
- [ ] Sprint retrospective: 30 minutes, what worked / what didn't / what to change for v3

---

## What this sprint does NOT solve

To be explicit, so nobody confuses Track 2 with a complete answer to the board report:

- It does **not** address Claim #9 (timeline compression). Only the pilot can.
- It does **not** address Claim #3 (displacement %). Only the pilot can.
- It does **not** address Claim #5 (direct savings). Only the pilot can.
- It does **not** expand the dataset beyond 39 deals. That requires the corpus expansion workstream (LAU-251 unblock).
- It does **not** address sub-sector claims #7/#8 in any meaningful way — n=1 for senior living remains n=1 after the refit.

Track 2 fixes one specific thing: the credibility of the COI prediction claim. That's enough to justify the week, but only if we're honest about what's still broken after.

---

## Interaction with the Adventist Pilot

The Adventist pilot (Track 1) will produce a new, genuinely out-of-sample data point: the actual closing COI compared against the v2 model's frozen prediction. This will be the **first true out-of-sample test of v2**.

**Rules for handling this data point:**
1. The v2 model is frozen at ship date. The Adventist prediction is computed from the frozen v2 and stored in `pilot/adventist-2026/frozen-predictions.md` per §5 of the measurement protocol.
2. When the pilot closes, the Adventist actual COI is compared to the v2 prediction and reported **separately** from the walk-forward CV results. Do not fold it into the training set.
3. Adventist becomes part of the training set only **after** the pilot post-mortem is complete and the comparison has been reported in its pure out-of-sample form.
4. If the Adventist prediction misses badly, that's data — investigate whether it's a feature gap, a model limitation, or a sub-sector issue. Do not retroactively retrain to "fix" the miss.

This is the cleanest test of v2 we will have. Protect it.