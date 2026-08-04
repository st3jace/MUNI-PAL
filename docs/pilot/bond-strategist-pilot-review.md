# Bond Strategist — Pilot Preparation Review

**Date:** 2026-04-08
**Reviewer:** Bond Strategist (Agent 1d1e0338)
**Task:** LAU-271 — Pilot Preparation
**Documents reviewed:** All 5 files in `docs/`

---

## Executive Summary

The pilot preparation package is unusually strong for a pre-revenue startup entering the municipal bond space. The counsel briefing is honest, the measurement protocol is pre-registered and rigorous, and the engagement letter is framed correctly. My review surfaces domain-specific issues that could undermine credibility with Adventist's deal team or create regulatory exposure. Most are fixable before the engagement letter ships.

**Bottom line:** The pilot can proceed. The legal question (MA status) is real and must be resolved by counsel before signing. The domain issues below are corrections, not blockers.

---

## 1. MA Status / Legal Boundary Analysis

### The counsel briefing is excellent

The CEO's memo to counsel is one of the best-framed legal questions I've seen from a non-lawyer in this space. The activity-by-activity breakdown (#1–#15), the honest acknowledgment of gray areas (#5–#8), and the explicit ask for per-activity rulings rather than a global yes/no — all correct.

### My domain read on each activity

| # | Activity | My domain assessment |
|---|----------|---------------------|
| 1 | Document organization | **Safe.** Pure workflow. No municipal bond professional would consider indexing PDFs advisory. |
| 2 | Information request coordination | **Safe with caveat.** Routing requests between borrower and their existing advisors is project management. **But:** if Launch Shop personnel editorialize on responses — "you should emphasize X in your answer to the underwriter" — that becomes advice on the presentation of information to a market participant, which is closer to MA territory. The engagement letter should explicitly state that Launch Shop routes but does not draft or edit substantive responses. |
| 3 | Readiness checklist | **Borderline-safe.** A descriptive checklist derived from historical OS data is closer to a research product than advisory. The key distinction: the checklist says "here is what comparable deals had" not "here is what you need." The current 167-item framework is structured correctly — it reports presence/absence against historical norms. **Risk:** If the framework assigns priority, urgency, or sequencing recommendations ("address this gap before going to market"), it crosses from observation into advice. The framework should report gaps without prescribing action order. |
| 4 | Historical benchmarking | **Safe.** Showing a borrower where they sit in a distribution of comparable deals is market data presentation. Bloomberg, EMMA, and every sell-side research desk do this. The platform is a data vendor here. |
| 5 | COI prediction with model output | **The hardest question.** A predicted COI with a margin of error is analytically indistinguishable from what a municipal advisor produces in a pre-pricing estimate. The distinction the CEO draws — "prediction, not recommendation" — is semantically correct but operationally fragile. If the borrower uses the prediction to evaluate whether their underwriter's proposed COI is reasonable, the prediction has functioned as advice on the terms of a municipal securities transaction. **My read:** This is the single activity most likely to trigger MA status. Counsel should focus here. The IRMA exception may be the only clean path to keep this in scope. |
| 6 | Readiness scoring with implied recommendations | **Borderline.** Identifying gaps is observation; ranking or weighting gaps by impact is advice. The current framework uses COI impact ratings (dollar ranges) on each item — e.g., "Certificate of Need: $50K–$200K impact." That impact rating is effectively advising the borrower on which gaps are expensive. **Mitigation:** Present impact ranges as "historical cost ranges observed in comparable deals" not as "what this will cost you." The framing matters. |
| 7 | Timing observations | **Borderline-safe if passive.** Showing historical seasonal patterns in HC issuance is market data. Answering "is now a good time?" with a directional opinion is advice on the timing of issuance of municipal securities — textbook MA activity. **Rule:** Show the data, do not interpret it. If the borrower asks "should we wait?", the answer is "that's a question for your MA." |
| 8 | Sitting in deal team meetings | **This is the sleeper risk.** Physical (or virtual) presence in deal team calls, with platform outputs visible to the underwriter and MA, creates an implied advisory relationship regardless of whether Launch Shop speaks. The underwriter and MA will perceive Launch Shop as part of the deal team. If a dispute arises later, Adventist's counsel could argue Launch Shop was acting in an advisory capacity based on its presence and its platform's influence on deal decisions. **Mitigation:** If Launch Shop attends, it should be as an observer with a written understanding (shared with UW and MA) that it is a technology vendor, not an advisor. Better: do NOT attend deal team calls. Provide platform access and let the borrower bring outputs to their own meetings. |

### IRMA Exception — Domain Perspective

The CEO's instinct on the IRMA path is directionally correct but incomplete.

**What the CEO gets right:**
- Adventist already has an MA. Launch Shop is not displacing them.
- The IRMA exception under G-42 is a recognized safe harbor.
- It aligns with the actual operating model.

**What the CEO may be missing:**

1. **The IRMA exception under G-42 applies to municipal advisors, not to unregistered persons.** G-42 governs the conduct of *registered* MAs. The IRMA exception allows a registered MA to rely on another MA's advice rather than duplicating the analysis. It does not create a blanket exemption for unregistered persons who happen to be working alongside a registered MA. Counsel needs to confirm whether an unregistered person can invoke the IRMA framework at all, or whether the correct analysis is the Section 15B(e)(4)(C) exclusion for persons providing advice to a client that has an independent registered MA.

2. **The written acknowledgment needs to come from Adventist's MA, not just Adventist.** The MA needs to confirm in writing that (a) they are providing advice on the matters within their registration, (b) they are aware of Launch Shop's role, and (c) they do not consider Launch Shop to be providing municipal advisory services. This is a professional courtesy that most MAs will grant if they understand the relationship — but some MAs may object if they perceive Launch Shop as a competitive threat or a liability risk.

3. **The IRMA path does not solve the COI prediction problem (Activity #5).** Even with an IRMA acknowledgment, if Launch Shop's model output functions as an independent estimate of deal costs that the borrower relies on, the activity itself may constitute advice on a municipal financial product. The IRMA framework addresses *who* is advising, not *what* constitutes advice. Counsel should address Activity #5 separately from the IRMA analysis.

### Recommendations for Counsel Briefing

- Add a question: "Does the Section 15B(e)(4)(C) exclusion (advice to a client with an independent registered MA) apply to Launch Shop's activities, and is this a better path than IRMA?"
- Ask counsel to distinguish between the IRMA exception (which applies to registered MAs) and the independent-MA exclusion (which applies to unregistered persons).
- Flag Activity #5 (COI prediction) as requiring separate analysis regardless of which exclusion path is chosen.

---

## 2. Engagement Letter — Domain Issues

### What's right
- No-fee structure is correct for a pilot. Avoids the "compensation tied to deal" trigger.
- §5(b) per-use veto on external mentions is the right call. Healthcare CFOs are protective of institutional brand.
- §6 termination is clean and unconditional — exactly right.
- §2 explicitly noting the borrower retains responsibility for all third-party costs prevents any argument that Launch Shop is subsidizing deal costs (which could create a different kind of regulatory issue).

### What needs fixing

**§1 — "Review" must be removed or narrowed.**
The word "review" in "document organization, review, and information request coordination" is doing too much work. "Review" implies substantive evaluation of documents. Change to: "document organization, categorization, and information request routing." This is not cosmetic — it is the difference between a project management function and an advisory function.

**§1 — "COI prediction" needs a qualifier.**
"COI prediction and benchmarking against comparable issuances" should be reframed as: "COI benchmarking based on historical comparable issuances, presented as statistical ranges rather than deal-specific projections." This aligns with the data-vendor framing and reduces the "advice" exposure.

**§7 — Needs the MA's acknowledgment as a condition precedent.**
§7 currently disclaims MA status unilaterally. As the CEO correctly notes, a disclaimer cannot cure activity that is in fact advisory. The engagement letter should condition signing on receipt of a written acknowledgment from Adventist's existing MA confirming awareness of Launch Shop's role. This is not just legal hygiene — it is also good deal practice. If the MA learns about Launch Shop mid-deal and objects, the pilot is dead regardless of what §7 says.

**Missing: Notification to underwriter and MA.**
The internal notes correctly flag this: "Any reference to the Borrower's underwriter and MA, who will need to be told this is happening." This is not optional. In my experience, underwriters and MAs who discover a third party in the deal workflow after the fact react badly. The engagement letter should include a condition that the Borrower will notify its existing UW and MA of Launch Shop's role before or contemporaneously with signing. A one-paragraph notice is sufficient.

**Missing: Data security basics.**
The internal notes flag this for v2. I'd move at least a minimal version to v1. Adventist is a large health system subject to HIPAA. Even though bond deal documents are not PHI, Adventist's vendor review will ask about data handling. A single paragraph covering (a) where documents are stored, (b) who has access, (c) encryption at rest/in transit, and (d) deletion upon termination, will prevent the engagement letter from being rejected by Adventist's procurement/compliance team before the CFO even sees it.

---

## 3. Measurement Protocol — Domain Assessment

### What's right — and genuinely impressive

- **Pre-registration with locked thresholds.** This is the gold standard for a pilot. The fact that decision rules are defined before kickoff means the results cannot be cherry-picked. Most startups in this space would never voluntarily constrain their ability to spin results.
- **Amendment #1 (demand-first reframing)** is the correct strategic call. Productivity compression in pilot #1 is unlikely — inserting a new actor into an established workflow always adds overhead before it removes it. The CEO is right that appetite is the existential question.
- **Selection bias acknowledgment.** Stating upfront that Adventist is a sophisticated repeat issuer and results will overstate impact on unsophisticated borrowers is exactly what a credible research design looks like.
- **Anti-pattern guardrails** in §6 are specific and binding. These are the kind of commitments that build credibility with a board — and eventually with institutional buyers who ask "how do you know your numbers are real?"

### Domain corrections

**§2 — Claim #5 ($30K–$85K direct savings) operationalization needs work.**
The formula "hours saved x blended hourly rate, plus any line-item COI reduction attributable to platform-driven decisions" conflates two different things:
1. *Issuer staff time savings* (hours the CFO and finance team didn't spend) — this is measurable via the time diary.
2. *COI line-item reduction attributable to platform* — this is nearly impossible to attribute in a single deal. COI depends on market conditions, UW pricing, counsel billing practices, and dozens of other variables. Claiming that a specific line-item reduction was "attributable to platform-driven decisions" invites challenge from every deal professional on the team.

**Recommendation:** Separate these into two sub-claims. Report issuer time savings (measurable, defensible) and COI delta vs. prediction (informational, not causal). Do not claim that platform activity *caused* COI savings in pilot #1. Correlation with n=1 is not causation.

**§3.2 — Hours baseline recall bias is worse than stated.**
The protocol acknowledges self-reported recall bias but says "the bias direction is unknown." In my experience, it is known: issuer staff *underestimate* hours spent on bond deals because much of the work is interstitial (15-minute tasks spread across months, email chains, internal coordination). The baseline will likely be biased low, which means the comparison deal's hours will also be biased low, which means reported savings will be *understated*. This is actually favorable for credibility — but it should be stated in the confounds section so the post-mortem report can say "our baseline likely understates prior-deal effort, meaning actual savings may be higher than reported."

**§4.1 — Counterfactual annotation is critical and fragile.**
The task log asks the annotator to record "would otherwise have been done by: [role]" at task creation. This is the right design, but the annotation quality depends entirely on who does it and how carefully. If the Bond Strategist is reviewing the log weekly but not doing the initial annotation, the annotations will drift toward whatever is convenient. **Recommendation:** The Bond Strategist should do the initial counterfactual annotation (not just the review), and the CEO should do the weekly QC pass. This adds 30 minutes/week but makes the displacement calculation defensible.

**§8 — Missing confound: Adventist's existing MA may change behavior.**
If Adventist's MA knows they are being measured against a platform, they may work harder, faster, or more transparently than usual — the Hawthorne effect applies to them too, not just to Adventist. This should be listed as a confound because it could either inflate or deflate the apparent platform contribution.

---

## 4. Baseline Interview Script — Domain Assessment

### What's right
- Anchoring on a specific prior deal (referenced by par, year, and use of proceeds) is the correct approach. It signals credibility and saves 10 minutes of context-setting.
- Hour buckets instead of minute-level precision is exactly right for recall-based data.
- The "hardest question" ("would you have taken a cold call?") is the single most important data point in the interview. The script correctly labels it as such.

### Domain corrections

**Part 2 — Missing question: "Who was your MA on that deal, and are they your MA on this one?"**
This is critical for two reasons:
1. The IRMA/exclusion analysis depends on Adventist having a registered MA. We need to confirm this before the engagement letter ships — not discover mid-deal that they used in-house capabilities and didn't engage an external MA.
2. If the MA changed between the baseline deal and this deal, the comparison is confounded. Different MAs have different work styles, billing practices, and information request patterns.

**Part 2 — Missing question: "What was your COI on that deal, and did it surprise you?"**
The protocol collects COI from the closing memo, but the interview should capture the *borrower's perception* of their COI — did they think it was high, low, or normal? Did they compare it to anything? This tells us whether COI benchmarking is a service they would value. If the answer is "I never really looked at it," that's a signal that COI optimization is not a pain point for this borrower.

**Part 3 — Pricing frame question needs a domain anchor.**
When asking "what would you expect to pay for this?", have a fallback range ready if they say "I have no idea." The anchor should be framed as: "For context, a municipal advisor on a deal this size would typically charge $X–$Y. We're not an MA, but does that range help you think about it?" This grounds the conversation and prevents the awkward silence from killing the pricing signal. Based on Adventist's deal sizes ($150M–$250M range), an MA fee would typically be $1.50–$2.50/1000 of par, or roughly $225K–$625K. Muni-Pal's value proposition is a fraction of that — positioning in the $15K–$75K range (per the Accelerator tiers) is credible as a technology-augmented readiness service, not as an MA replacement.

**Part 3 — Add a question about internal approval process for technology vendors.**
Healthcare systems have procurement and IT security review processes that can take 3–6 months. If Adventist's vendor onboarding requires SOC 2, BAA, or IT security review, the pilot timeline could slip significantly. Better to discover this in the baseline interview than after the engagement letter is signed.

---

## 5. Track 2 — COI Model Upgrade Spec

### What's right
- **Scope discipline is excellent.** "Do not change the model class" is the correct constraint. Confounding feature improvement with model improvement is the #1 mistake in this kind of sprint.
- **Walk-forward CV** is the right cross-validation method for time-series financial data. The original random split allowed temporal leakage — this fixes it.
- **Slice reporting** is the key innovation. Global MAE hides sub-sector performance. Reporting by investment-grade hospital slice gives us the defensible claim we need.
- **Feature #1 (credit rating)** is almost certainly the largest expected lift. The Montefiore outlier ($6.86 residual) is a Baa3/BBB- distressed credit — rating as a predictor would have captured most of that error.
- **Anti-scope items** are well-chosen. The temptation to switch to XGBoost or add interaction features mid-sprint is real and must be resisted.

### Domain corrections

**Feature #4 (Enhancer identity) — Expand the categories.**
The spec lists "AGM vs BAM vs Assured vs LOC bank vs none." AGM (Assured Guaranty Municipal) and AGM Corp are sometimes listed separately. BAM (Build America Mutual) is member-owned and has a different cost structure. Also missing: **FHA/HUD mortgage insurance** (Section 242 for hospitals), which is a form of credit enhancement that fundamentally changes COI structure because HUD deals have their own closing cost regime. For healthcare deals specifically, I'd add:
- AGM / Assured (combine — same parent)
- BAM
- FHA/HUD Section 242
- State credit program (e.g., Cal-Mortgage, DASNY enhanced)
- LOC (bank letter of credit)
- None
- Other

**Feature #5 (Obligor type) — "Behavioral" is too narrow.**
The spec lists "behavioral" as a category. In the healthcare muni space, this is a tiny slice. More useful: split "single hospital" into "standalone community hospital" vs "academic medical center" — these have very different COI profiles because academic medical centers often have complex conduit structures, multiple obligated groups, and higher counsel costs.

**Feature #11 (Lead UW identity) — The top 8 list needs updating.**
The spec lists "Ziegler, BofA, JPM, Citi, Morgan Stanley, RBC, Piper, Raymond James." For healthcare specifically:
- **Ziegler** is correct and dominant in senior living, less so in hospitals.
- **BofA Securities** (formerly Merrill Lynch) — correct, major HC underwriter.
- **JPMorgan** — correct.
- **Citigroup** — correct.
- **Morgan Stanley** — correct but less active in HC than in general muni.
- **RBC Capital** — correct, very active in HC.
- **Piper Sandler** — correct.
- **Raymond James** — less dominant than **Goldman Sachs** in HC. Consider swapping.
- **Missing: Barclays** — active in large hospital system deals.
- **Missing: Wells Fargo** — still active in HC despite pulling back from some muni sectors.

**Recommendation:** Use 10 named UW + "other" rather than 8. The marginal cost of two more categories is negligible; the information value is material.

**§4 — Data collection: 15 minutes per deal is optimistic.**
The spec estimates 15 minutes per deal for feature extraction from OS PDFs. For a reviewer who knows exactly where to look on an OS cover, 15 minutes is possible for straightforward deals. But for deals with multiple series, complex conduit structures, or poorly formatted OS documents, 25–30 minutes is more realistic. Budget 20 hours for 39 deals, not 10. This is a 1-day slip, not a sprint risk — but set expectations correctly.

**§5 — Walk-forward CV with n=39 will produce high variance.**
The spec acknowledges this ("report variance across walk-forward steps") but doesn't state the consequence: with 39 deals and 17 potential features, the walk-forward MAE confidence interval will be wide. After feature selection, the effective feature count should be 5–8. Even so, the per-step MAE will be noisy. **Recommendation:** In the model card, report the walk-forward MAE with a bootstrap confidence interval (e.g., "MAE = $X.XX ± $Y.YY, 95% CI"). This is more honest than a point estimate and is what a sophisticated buyer or regulator would expect to see.

**Missing: Holdout set interaction with pilot.**
The spec says "do not re-run the holdout against deals not in the current 39-deal set." Correct. But the Adventist pilot will produce a new out-of-sample data point (Claim #10 in the measurement protocol). The spec should note that the Adventist pilot result will be the first true out-of-sample test of v2, and it should be reported separately from the walk-forward CV results — not folded into the training set until after the pilot post-mortem is complete.

---

## 6. Cross-Document Issues

### Timing sequencing matters

The documents imply a sequence that isn't explicitly stated. Based on dependencies:

1. **Counsel briefing ships first.** The engagement letter cannot be sent until counsel clears the MA question.
2. **MA/UW notification happens before or with the engagement letter.** Adventist's MA must acknowledge Launch Shop's role before the engagement letter is signed.
3. **Baseline interview happens after engagement letter is signed** but before platform work begins.
4. **Frozen predictions are filed after the baseline interview** (because the baseline interview may reveal information that updates the prediction).
5. **Track 2 runs in parallel** with steps 1–4. It does not depend on any of them.

**Recommendation:** Add a one-page sequencing document or Gantt-style timeline showing these dependencies. Without it, the risk is that someone sends the engagement letter before counsel has responded, or starts platform work before the baseline interview is complete.

### The "no local source code checkout" gap persists

From my prior audits: I cannot verify that the DSCR corrections, Five Cs healthcare factors, feedstock_supply removal, and corpus benchmark sectoring are implemented in the running Muni-Pal platform. If the pilot proceeds and the platform produces outputs with domain errors (e.g., feedstock_supply appearing in a hospital readiness report), it will undermine credibility with Adventist's deal team immediately.

**Recommendation:** Before the pilot kickoff, run the platform against a test case (a synthetic Adventist-like profile) and have me review the outputs for domain accuracy. This is a 2-hour exercise that prevents a catastrophic first impression.

### The $75K Accelerator tier and pricing tiers

The baseline interview asks Adventist about pricing expectations. The pilot is unpaid. But the engagement letter's internal notes reference the $75K Accelerator tier. The 3-tier pricing structure I recommended in prior audits ($15K–$25K / $40K–$50K / $75K+) has not been documented. If the baseline interview surfaces a pricing signal and we don't have tiers defined, we'll be improvising pricing in real time.

**Recommendation:** Define the 3-tier structure before the baseline interview so the pricing questions have an internal anchor, even if the tiers are not shared with Adventist.

---

## 7. Overall Assessment

| Document | Grade | Key action |
|----------|-------|------------|
| Counsel briefing | A | Add the Section 15B(e)(4)(C) exclusion question; flag Activity #5 separately |
| Engagement letter | B+ | Fix §1 ("review" → "routing"), add MA notification condition, add minimal data security |
| Measurement protocol | A- | Separate Claim #5 sub-claims; add MA Hawthorne confound; fix counterfactual annotation ownership |
| Baseline interview | B+ | Add MA identity question, COI perception question, vendor procurement question |
| Track 2 COI spec | A- | Update enhancer categories, expand UW list to 10, note pilot as first v2 out-of-sample test |

**The pilot preparation package is ready for legal review.** The corrections above are domain refinements, not structural problems. The biggest risk is the MA status question — and the CEO has correctly identified it as the gating issue and framed it well for counsel.

---

*Bond Strategist — 2026-04-08*
