# Adventist Health Pilot — Measurement Protocol

**Status:** Draft v1 — pre-registration document
**Date:** 2026-04-07
**Owner:** CEO + Bond Strategist
**Purpose:** Define what we will measure, how, and what the results must show **before** the pilot begins, so post-hoc reinterpretation cannot soften or inflate the findings.

> **Pre-registration principle:** Every threshold, baseline, and decision rule in this document is locked before pilot kickoff. Changes after kickoff must be logged in an amendment section with date, reason, and signature. This is what separates a pilot from an anecdote.

---

## 1. Why Adventist

- Repeat issuer (3 prior deals in dataset)
- Average **−$2.71/1000 vs model** across those deals — already a credible track record
- Warm relationship; lowest-friction path to a real engagement
- Investment-grade hospital system → matches the slice where our COI model is strongest

**Selection bias to acknowledge in any reporting:** Adventist is a sophisticated repeat issuer. Results will *overstate* what Muni-Pal can do for a first-time or unsophisticated borrower. We will state this caveat in every external use of pilot data.

---

## 2. Claims Under Test

Each claim is mapped to a board-report claim number, an operational definition, and a pre-registered decision rule.

| # | Claim | Operationalization | Pre-registered Rule |
|---|---|---|---|
| 9 | Timeline compression | (Adventist's prior deal: kickoff → pricing, in calendar days) vs. (this deal: kickoff → pricing) | Compression ≥15% → AMBER evidence. ≥25% → GREEN evidence (one-deal). <15% → claim withdrawn from marketing. |
| 5a | **Issuer staff time savings** (component of #5) | Hours saved by CFO + finance staff × blended hourly rate, from time diary vs baseline buckets | ≥$20K → AMBER. ≥$40K → GREEN (one-deal). <$20K → claim revised downward to actual range. |
| 5b | **COI delta vs prediction** (informational only) | (Actual closing COI) − (frozen model prediction from §5), line by line | **No causal claim from n=1.** Report as informational. Do NOT claim platform *caused* any COI reduction in pilot #1. Correlation with n=1 is not causation and will be challenged by any deal professional who reads it. |
| 3 | 31% agent-displaceable COI | (Tasks executed by Muni-Pal agents that would otherwise have been billable to MA/counsel/CFO staff) ÷ (total billable task-hours on the deal) | Range, not threshold. Report actual %. The number itself becomes the new claim — we stop claiming 31% and start claiming the observed value with n=1 caveat. |
| 10 | COI prediction accuracy | Predicted COI (model run at deal kickoff, frozen) vs. actual COI at close, line-by-line | Out-of-sample test point. Adds to holdout set. No pass/fail — informational. |

**Not tested in this pilot:**
- Claim #6 (53% reduction via direct placement) — Adventist will not be a direct placement
- Claim #7/#8 (senior living premium) — wrong sub-sector
- Claims #1/#2/#14 (TAM) — not testable in a single pilot

---

## 3. Baseline Definition

**Locked before kickoff. No retroactive baseline shopping.**

### 3.1 Timeline baseline
- **Source:** Adventist's most recent comparable issuance (same obligated group, same deal type — new money vs refunding, same approximate par size ±50%).
- **Metric:** Calendar days from formal engagement letter signature → bond pricing date.
- **Sub-metrics (milestones):** engagement → POS → rating agency presentations → roadshow → pricing. Each milestone date logged.
- **Documentation:** Pull from Adventist's prior Official Statement timeline section + closing memo. If gaps, interview deal team within first pilot week (do NOT wait until close — memory decays).

### 3.2 Hours baseline
- **Source:** Self-reported estimates from Adventist CFO + finance staff for the prior comparable deal, collected in a structured 30-minute interview in pilot week 1.
- **Roles tracked:** CFO, CFO direct staff, internal counsel, external bond counsel, MA, UW counsel.
- **Buckets (not minute-level):** <10h, 10–25h, 25–50h, 50–100h, 100–250h, 250+h per role.
- **Caveat:** Self-reported recall is biased. We will state this in reporting. **Bias direction is likely downward** — issuer staff typically underestimate hours spent on bond deals because much of the work is interstitial (15-minute tasks spread across months, email chains, internal coordination that never gets logged). This means the baseline will understate prior-deal effort, which means reported savings will be *understated*, not inflated. This is favorable for credibility but must be stated in the post-mortem so the direction of bias is transparent.

### 3.3 COI baseline
- Adventist's prior 3 deals already in dataset. Use the most recent comparable (same structure type) as the primary baseline. Use all 3 as a secondary comparison (averaged, secular-trend adjusted).

---

## 4. Instrumentation

**The single biggest failure mode is finishing the pilot with a happy customer and no data.** Instrumentation must be designed so measurement happens *during* the deal, not reconstructed after.

### 4.1 Task log (drives Claim #3)
- **What:** Every task Muni-Pal agents perform on the deal is logged with: timestamp, agent, task type, output, and an annotated counterfactual ("would otherwise have been done by: [role]").
- **Where:** Append-only log in the platform, exportable as CSV.
- **Counterfactual annotation:** Done at task creation by the **Bond Strategist** (not by whoever happens to be available). Annotation quality depends entirely on who does it — rotating annotators produces drift toward whatever is convenient. The Bond Strategist owns initial annotation because they have the domain knowledge to assess "would this task have been done by MA, counsel, or CFO staff" accurately. Not done retrospectively.
- **Quality control:** CEO does a weekly QC pass on the annotations (30 minutes/week). Disputes between Bond Strategist annotation and CEO review resolved in writing, in the log. This separation of annotation and QC is what makes the displacement-% calculation defensible.

### 4.2 Hours diary (drives Claim #5)
- **What:** Adventist CFO + staff fill a 5-minute weekly diary noting hours spent on the deal, by role, in the same buckets as the baseline.
- **Cadence:** Weekly, every Friday, 12 weeks max.
- **Carrot:** Frame as "we'll give you a final time-savings report at close" — make it useful to them, not just to us.
- **Risk:** Compliance will degrade after week 4. Plan for this — Bond Strategist sends a Friday reminder; missing weeks are flagged, not silently zeroed.

### 4.3 Milestone timestamps (drives Claim #9)
- **What:** Every milestone in the baseline list is timestamped as it occurs.
- **Owner:** Bond Strategist, confirmed with Adventist deal lead.
- **No estimation:** If a milestone date is unclear, it is logged as "unclear" not guessed.

### 4.4 COI line items (drives Claim #10)
- **What:** Final closing memo COI table, captured at close, line-by-line, into the dataset.
- **Comparison:** Against the model prediction frozen at kickoff (must be saved as a dated artifact in the pilot folder before any platform work begins).

---

## 5. Frozen Predictions

**Before any Muni-Pal work touches the deal**, the following predictions are recorded, dated, and stored in `pilot/adventist-2026/frozen-predictions.md`:

1. Predicted COI (total + line items), from current model
2. Predicted timeline (kickoff → pricing, calendar days), based on Adventist's prior deals
3. Predicted hours by role, based on baseline interview
4. Expected agent displacement % (use the 31% headline as the prior to be tested)

**Why frozen:** Without frozen predictions, every result becomes "well, we kind of expected that." Frozen predictions force the comparison to be honest.

---

## 6. Decision Rules and What We Will Say Publicly

After close, results are mapped to decision rules in §2 and translated into one of three claim states:

| State | Marketing language allowed |
|---|---|
| **GREEN (n=1)** | "In our first instrumented pilot, [metric] improved by [X%]." Caveats: "single deal, sophisticated repeat issuer, results may not generalize." |
| **AMBER** | "Early evidence from one pilot suggests [direction]." No specific percentages in headlines. |
| **WITHDRAWN** | Claim removed from all marketing within 7 days of close. No replacement claim invented from the same data. |

**Anti-pattern guardrails:**
- We will not pick the most flattering sub-metric and lead with it. If timeline compression fails but COI prediction is accurate, we report both.
- We will not retroactively redefine "kickoff" to make compression look bigger.
- We will not exclude Adventist staff hours that "weren't really about the deal" unless that exclusion was defined in §4.2 before the pilot.
- We will not claim displacement % higher than the task log supports, even if it "feels" higher.

---

## 7. Reporting

**Internal post-mortem memo** within 14 days of close. Sections:
1. What we predicted (from §5) vs. what happened
2. Each claim's decision-rule evaluation
3. What worked, what didn't, what surprised us
4. Specific marketing language updates (with diffs against current site copy)
5. Confidence Matrix update for the board report

**External case study** only if Adventist consents in writing AND results are GREEN or AMBER. Never publish a WITHDRAWN-state pilot externally — but **do** internally and to the board.

---

## 8. Risks and Confounds

| Risk | Mitigation |
|---|---|
| Adventist deal team is unusually efficient regardless of platform | Acknowledged. Selection bias caveat in §1 stays attached to all reporting. |
| Hawthorne effect (they work harder because they're being measured) | Not fully mitigable in a single pilot. State explicitly. |
| **MA Hawthorne effect** — Adventist's registered MA may work harder, faster, or more transparently than usual because they know Launch Shop is measuring the deal alongside them | Not mitigable. Could inflate or deflate apparent platform contribution depending on direction. State explicitly in post-mortem. If the MA materially changes their behavior, note it as a confound on both #3 (displacement) and #5a (time savings). |
| Market conditions compress timeline independent of platform | Track 10Y UST and HC index spreads at kickoff and pricing; report as confound. |
| Pilot stalls or is cancelled mid-deal | Define abort criteria: if no pricing within 16 weeks of kickoff, pilot is reported as inconclusive, not extended indefinitely. |
| Adventist refuses instrumentation | Walk away from the pilot. An uninstrumented "pilot" is worse than no pilot — it produces stories, not evidence. |
| One pilot is treated as proof | Hard rule: no claim moves to GREEN-without-caveat from a single deal. Second pilot (FQHC or SL) must follow before unqualified claims. |

---

## 9. Pre-Pilot Checklist

Before the pilot officially starts (kickoff date logged in §3.1), the following must be complete and stored in `pilot/adventist-2026/`:

- [ ] This protocol signed by CEO and Bond Strategist
- [ ] Adventist counterpart identified and consented to instrumentation in writing
- [ ] Baseline interview completed; baseline document filed
- [ ] Frozen predictions document filed (§5)
- [ ] Task log infrastructure live in platform; tested with a dummy task
- [ ] Hours diary template sent to Adventist; week 1 reminder scheduled
- [ ] Abort criteria reviewed (§8)
- [ ] Decision-rule thresholds (§2) reviewed and locked

**If any box is unchecked, the pilot has not started — regardless of what's happening on the deal.**

---

## 10. Amendments

Any change to thresholds, baselines, or rules after pilot kickoff must be logged here with date, reason, and signature. An amendment is not invalidating — but an unlogged change is.

| Date | Section | Change | Reason | Signed |
|---|---|---|---|---|
| 2026-04-07 | §2, §8 | Replaced productivity-based decision rules and abort criterion with demand-based equivalents. See Amendment #1 below. | Pilot purpose reframed from "validate productivity claims" to "discover market appetite." Productivity compression is the wrong expectation in pilot #1, where Muni-Pal is a new actor inserted into a working process — overhead in pilot #1 is expected; compression shows up in pilot #2+. Original 15%/25% thresholds had no defensible basis. | CEO (pending) |

---

## Amendment #1 — Demand-First Reframing (2026-04-07)

### What changed
The pilot's primary purpose is now **demand discovery**, not productivity measurement. Productivity instrumentation (task log, hours diary, milestone timestamps) is retained because the data is still useful and nearly free to collect — but it no longer drives the GO/NO-GO decision rules.

### Why
The CEO's stated uncertainty is appetite, not efficiency: *"I literally have no idea about the appetite for Muni-Pal."* A productivity pilot answers a question we are not yet asking. A demand pilot answers the question that determines whether the company has a market at all. Productivity claims can be hardened later, on deals where the workflow is no longer novel.

### Replacement decision rules (supersedes §2 for Claim #9 and the overall pilot verdict)

| State | Definition | Marketing language allowed |
|---|---|---|
| **GREEN** | Adventist signs an engagement for a second deal *before* the first closes, **OR** provides a written reference for outreach, **OR** introduces us to a peer health system with intent | "An institutional healthcare borrower has engaged Muni-Pal for a second deal." Quote the reference if available. |
| **AMBER** | Deal completes, Adventist expresses satisfaction, but no repeat commitment, reference, or introduction | "We have completed our first instrumented engagement with a major health system." No claims of repeat demand. |
| **WITHDRAWN** | Adventist disengages, requests removal of instrumentation, or completes without endorsement | Pilot is reported internally and to the board. No external mention. |

Productivity claims (#3, #5, #9) remain measured per §4 but their decision rules in §2 are downgraded to **informational only** for pilot #1. They become decision-rule-bearing in pilot #2.

### Replacement abort criterion (supersedes §8 row "Pilot stalls or is cancelled mid-deal")

**Abort if any of:**
- Adventist non-responsive to instrumentation requests for 3 consecutive weeks
- Adventist formally requests removal of the platform from the deal
- Deal cancelled by Adventist for reasons unrelated to Muni-Pal
- Adventist counterpart leaves the organization and no replacement champion emerges within 2 weeks

**Do NOT abort if:**
- Timeline runs longer than baseline. *Long timeline in pilot #1 is data, not failure.* Inserting a new actor into an established workflow is expected to add overhead before it removes overhead.
- Hours diary compliance degrades after week 4. Send reminders, log gaps honestly, do not abort.

### What is unchanged
- Frozen predictions (§5) — still recorded, still used for post-mortem comparison
- Instrumentation (§4) — still collected
- Selection-bias caveat (§1) — still attached to all reporting
- Anti-pattern guardrails (§6) — still binding
- Pre-pilot checklist (§9) — still required, with the demand-test consent added

### New checklist item for §9
- [ ] Adventist counterpart has been asked, in writing, the appetite-discovery questions from the baseline interview script (see `pilot/adventist-2026/baseline-interview.md`) and responses are filed