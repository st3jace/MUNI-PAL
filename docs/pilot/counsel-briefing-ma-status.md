# Counsel Briefing — Municipal Advisor Status Question

**To:** [Counsel name]
**From:** Launch Shop LLC (CEO)
**Date:** 2026-04-07
**Subject:** Whether Muni-Pal's pilot engagement scope crosses into regulated municipal advisor activity under Section 15B / SEC Rule 15Ba1-1 / MSRB Rule G-42
**Decision needed by:** [Date — before Adventist engagement letter is sent]
**Estimated counsel time:** 2–4 hours review + 30 minute call

---

## What I need from you

A written opinion (memo or email is fine; does not need to be a formal legal opinion letter) addressing three specific questions:

1. **Does the scope of services described in §1 of the attached engagement letter constitute "municipal advisory activities" under Section 15B(e)(4) of the Securities Exchange Act of 1934 and SEC Rule 15Ba1-1?** If yes, which specific activities trigger the definition?

2. **If any activities trigger the definition, can the scope be narrowed to avoid registration requirements while preserving the commercial value of the engagement?** Specifically, can the platform continue to (a) coordinate information requests between borrower and existing advisors, (b) organize and review documents, and (c) provide readiness benchmarking against historical data, without crossing the line?

3. **Do any of the available exclusions apply** — in particular the underwriter exclusion, the registered investment adviser exclusion, the engineer exclusion, the response to RFP exclusion, **the Section 15B(e)(4)(C) exclusion for persons providing advice to a client that has an independent registered municipal advisor**, or the independent registered municipal advisor (IRMA) exception under MSRB Rule G-42?

   **Please distinguish between two paths that I may be conflating:**
   - The **IRMA exception under G-42** governs the conduct of *registered* MAs and allows them to rely on another MA's advice. It may not be available to unregistered persons at all.
   - The **Section 15B(e)(4)(C) exclusion** (or its analog) is the path that applies to unregistered persons like Launch Shop when the client has its own registered MA.

   Which path actually applies to us? What would the engagement letter and operational practice need to look like to qualify under the correct path?

4. **Activity #5 (COI prediction with model output) requires separate analysis.** Even if an exclusion covers our general activities, the COI prediction may independently constitute advice on the terms of a municipal financial product. Please address this activity on its own, distinct from the general exclusion analysis.

I am not asking for a formal no-action letter or SEC submission. I am asking for your professional read on whether we can sign the attached engagement letter as drafted, sign it with modifications, or whether the underlying business model needs to be restructured before any pilot proceeds.

---

## Context

Launch Shop operates Muni-Pal, an AI-driven platform that helps healthcare borrowers prepare for and execute municipal bond issuances. We are about to begin our first instrumented pilot engagement with [Adventist Health entity], a repeat issuer in the healthcare municipal bond market. The full engagement letter is attached as Exhibit A; the full pilot measurement protocol is attached as Exhibit B for additional context on how the engagement will operate in practice.

This is not a hypothetical question. The engagement letter is drafted, the borrower counterpart is identified, and the pilot is scheduled to begin within the next several weeks. The MA-status question is the gating legal issue — if we cannot sign as drafted and cannot satisfactorily restructure, the pilot does not happen and the company's go-to-market plan needs to change.

---

## What Muni-Pal actually does on a deal

Below is an honest, plain-English description of the activities the platform and the Launch Shop team will perform during the Adventist engagement. I am giving you the **actual** operational picture, not the marketing description, because the legal question turns on what we actually do, not what we call it.

### Activities we are confident are NOT municipal advisory

1. **Document organization.** The borrower uploads files (PDFs, Word documents, financial statements, prior OS, etc.) to a workspace. The platform indexes, categorizes, and surfaces them. No advice; pure file management.

2. **Information request coordination.** The borrower's underwriter, counsel, or MA sends information requests. The platform helps the borrower locate, prepare, and route responses. The platform is acting as a coordinator and project manager, not as a substantive advisor on what to say.

3. **Readiness checklist.** The platform runs the borrower's documents and answers against a 167-item readiness framework derived from historical Official Statements. Output is a list of items present, items missing, and items unclear. The framework is descriptive of common deal requirements, not prescriptive of what this specific borrower should do.

4. **Historical benchmarking.** The platform shows the borrower how their projected COI compares to a dataset of 86 prior healthcare deals, sliced by sub-sector, par size, and structure. Output is a benchmark range with a confidence interval. The platform does not tell the borrower whether their COI is "good" or "bad"; it shows them where they sit in a distribution.

### Activities where I am uncertain

5. **COI prediction with model output.** The platform runs a regression model and produces a predicted COI for the upcoming deal, with a margin of error. We present this as a prediction, not a recommendation. **But:** if the borrower asks "is this COI reasonable?" and our platform output says "predicted $X ± $Y," is that advice?

6. **Readiness scoring with implied recommendations.** The 167-item framework will inevitably surface gaps. When we tell the borrower "you are missing items 47, 89, and 122," the implicit message is "you should address these before going to market." Is the act of identifying gaps advice, or is it observation?

7. **Timing observations.** Our historical data shows secular COI trends and seasonal patterns. If the borrower asks "is now a good time to come to market?" and we show them the historical data, are we advising on timing or providing market intelligence?

8. **Sitting in deal team meetings.** During the pilot, Launch Shop personnel will likely be present (at the borrower's invitation) on calls with the underwriter, counsel, and MA. We will not speak to deal terms. But our presence and our platform's outputs will be in the room. Does that change the analysis?

### Activities we are confident WOULD be municipal advisory and which we will NOT perform

9. We will not advise on deal structure (par, maturity schedule, call provisions, redemption features, security, covenants).
10. We will not advise on choice of underwriter, counsel, MA, trustee, or any other deal participant.
11. We will not advise on choice of sale method (negotiated vs competitive vs private placement).
12. We will not advise on timing of pricing or market entry.
13. We will not advise on credit enhancement, ratings strategy, or disclosure content.
14. We will not negotiate with any deal participant on the borrower's behalf.
15. We will not be compensated as a percentage of par, COI savings, or any other deal-contingent metric. The pilot is unpaid; future engagements would be flat-fee or subscription.

The line we are trying to walk is: **be useful enough to be worth paying for, without giving advice that requires registration.**

---

## The specific clauses in the engagement letter that worry me

### §1 — Scope of Services

The current language says Launch Shop will provide "document organization, review, and information request coordination with the Borrower's underwriter, counsel, and municipal advisor" and "COI prediction and benchmarking against comparable issuances."

**My concern:** "Review" and "COI prediction" are the soft spots. A reviewer who flags issues is arguably advising. A predictor whose output influences the borrower's expectations is arguably advising on a financial product.

**Question for you:** Can these phrases be tightened (e.g., "document organization and request routing" instead of "review") without making the engagement commercially worthless? Or is the better approach to keep the language and rely on §7?

### §7 — No Advisor Status

The current disclaimer says Launch Shop is not a registered MA and that nothing in the engagement constitutes municipal advisory services. The borrower acknowledges reliance on its existing MA.

**My concern:** A disclaimer cannot cure activity that is in fact municipal advisory. If §1 describes regulated activity, §7 does not save us. Disclaimers help with intent and good faith but they do not redefine the activity.

**Question for you:** Is §7 doing any real work here, or is it cosmetic? If cosmetic, should we strengthen it (e.g., explicit IRMA reliance language) or remove it to avoid creating the impression we thought we needed it?

### §3 — Measurement and Data Rights

We will collect data on what the platform did, what the borrower did, and what the deal cost. We will use this data to improve the platform and to produce a post-engagement report.

**My concern:** I do not think this section creates MA exposure, but I want you to confirm that collecting and using this data — particularly for model improvement that will influence future borrowers — does not change the analysis. If our model gets better because of Adventist's data, and a future borrower relies on the improved model, is there any chain of reasoning that pulls Adventist into a fiduciary or advisory relationship retroactively?

---

## The IRMA exception — my current best guess

My non-lawyer reading of MSRB Rule G-42 suggests that the **IRMA exception** may be our cleanest path: if Adventist has its own registered municipal advisor (which they will, for the actual deal), and that MA acknowledges in writing that they are providing advice on the matters Launch Shop is involved in, then Launch Shop can rely on the IRMA exception and is not itself acting as an MA.

This is appealing because:

1. Adventist already has an MA. We are not displacing them.
2. The IRMA exception is a recognized, written safe harbor, not an interpretive gray area.
3. It aligns with our actual operating intent — we sit alongside the MA, not in their seat.

**Questions for you on the IRMA path:**

a. Is my read of G-42 directionally correct, or am I misunderstanding the exception?
b. What does the IRMA written acknowledgment need to say, and who has to sign it (the MA, the borrower, or both)?
c. Does relying on the IRMA exception create any obligations for Launch Shop in how we communicate with the borrower (e.g., language we must include, language we must avoid)?
d. If the IRMA exception applies cleanly, does that simplify the engagement letter — can we narrow §7 and lean on the IRMA acknowledgment instead?
e. What if a future borrower does NOT have an existing MA and wants to engage Muni-Pal directly? Does that future engagement require a different structure entirely, or can we make IRMA acknowledgment a condition of all engagements?

---

## What is at stake

I want to be transparent about the business consequences of each possible answer, so you can calibrate the level of caution in your opinion.

| Your conclusion | Business consequence |
|---|---|
| Sign as drafted; activities do not trigger MA status | Pilot proceeds on schedule. No restructuring needed. |
| Sign with §1 narrowed; activities are borderline but defensible | Pilot proceeds with modified scope. Some commercial value lost but not fatal. |
| IRMA exception is clean path; need acknowledgment from Adventist's MA | Pilot proceeds; we need a 2-week conversation with Adventist's existing MA before kickoff. Adds time, removes legal risk. |
| Activities cross the line; Launch Shop must register as MA before proceeding | Pilot does not happen on current timeline. Registration takes months. We need to either pause go-to-market or restructure the product to operate strictly as a software vendor with no human-in-the-loop involvement. |
| Activities cross the line and cannot be cured by registration alone (e.g., the AI model itself constitutes regulated activity) | The business model needs fundamental rethinking. I need to know this immediately. |

The worst outcome is not a "no." The worst outcome is a "maybe" that lets us proceed and creates exposure later. If you are uncertain, I would rather hear "I am uncertain, here is what I would need to research" than a hedged green light.

---

## Practical asks

1. **Read Exhibit A (engagement letter) and Exhibit B (pilot protocol) end to end** before our call. The operational details in the protocol may matter more than the letter language.

2. **Tell me which of activities #1–#8 in this memo you consider safe, borderline, or unsafe.** I need a per-activity read, not a global yes/no, because we can drop or restructure individual activities if needed.

3. **Give me your read on the IRMA path** specifically. If this is the right path, the conversation with Adventist's MA needs to start before we send them the engagement letter — the sequence matters.

4. **Flag anything I am not asking about that you think I should be asking about.** I am writing this from a layperson's understanding of the regulatory framework. There may be exposures I do not see — broker-dealer status, investment adviser status, state-level requirements, anti-touting rules, anything else.

5. **30-minute follow-up call** after you have read the materials, to walk through your conclusions and decide on next steps.

---

## Exhibits

- **Exhibit A:** [Engagement letter draft — `docs/pilot-engagement-letter.md`]
- **Exhibit B:** [Pilot measurement protocol — `docs/pilot-measurement-protocol.md`]
- **Exhibit C (on request):** Marketing description of Muni-Pal as currently presented on muni-pal.io
- **Exhibit D (on request):** The 167-item readiness framework, so you can see exactly what kinds of items the platform is checking for

---

## One last thing

I am not looking for the most conservative possible answer. I am looking for the **most accurate** answer. Conservative legal advice that kills the pilot when the law would actually permit it is just as costly to me as aggressive advice that exposes us. Tell me what the rule actually says and where the actual line is, and I will make the business judgment about how close to walk to it.

Thank you.

[CEO]
Launch Shop LLC
