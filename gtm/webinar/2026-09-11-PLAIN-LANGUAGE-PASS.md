# Plain-language pass: workshop deck, script, and emails

**Date:** 2026-09-11
**Scope:** `2026-09-11-workshop-deck.html` (+ PPTX twin), `2026-09-11-workshop-SCRIPT.md`, `2026-09-11-invite-and-followup-SEQUENCE.md`
**Reader:** a CFO or controller at a nonprofit, school, hospital, or housing company that borrowed through a bond issue.
**Status:** APPLIED 2026-09-11 (Stephen: apply all). One item held: B-3, the "Items awaiting input" → "Open items list" rename. That name is printed by `fulfillment/demo/run.py` and `lab/twin-bfms/labkit/post_close.py`, and the lab pins `run.py` by hash (`lab/twin-bfms/packs/_pins.json`). Renaming it is a code change with a pin regeneration, not a copy change.

Slide numbers use the new 14-slide order (12 = What you get, 13 = Price, 14 = Start).

---

## A. Our own words. Safe to change.

| # | Word we use | Where | Why a CFO trips on it | Plain version |
|---|---|---|---|---|
| 1 | **custody**, post-close custody, custody question | Slides 1, 2, 3, 10. Invite, Touch −4, calendar hold | In finance, "custody" means a bank that holds your securities or cash. A CFO can think we hold their money. | **record-keeping.** "We keep the records. We do not give advice." The letter §1 already says "record-keeping". |
| 2 | **synthetic** deal, synthetic register | Slides 1, 7. Invite, Touch −2 | In bond finance, "synthetic" means a swap (a "synthetic fixed rate"). | **made-up example deal** |
| 3 | **obligated person(s)** | Slides 1, 11. Invite, calendar hold | SEC rule term. CFOs say "borrower". | **private borrowers on bonds** (nonprofits and companies that borrowed through a bond issue). Keep the legal term on the intake form and letter only. |
| 4 | **undertaking(s)**, live undertakings | Slides 4, 9, 11. Script, invite | Lawyer word. | **reporting promises** |
| 5 | **CDA**, CDA pack, CDA drop | Slide 13. Script close, invite, recording email | Acronym. | **your continuing disclosure agreement and the reports you filed under it** |
| 6 | **instrument count** | Slide 13. Invite, script | Securities word. | **how many bond issues you have** |
| 7 | **drop**, complete drop, drop the binder | Slides 13, 14. Script, emails | Our shop talk. | **send us your documents.** "A complete set" = every item on the checklist we give you. |
| 8 | **working book**, the book | Slides 4, 7, 10. Emails | "The books" means the accounting ledger to a CFO. | **the register** or **your record** |
| 9 | **clerk gap** | Slide 2 label. Calendar agenda | Made-up term. | **Who keeps track after closing?** |
| 10 | **reference seat** | Slide 8 label. Script | Internal name. | **Ask where it is** |
| 11 | **skill file** | Slide 9. Script. Landing page | AI insider word. | **instructions you paste into the AI assistant you already use** |
| 12 | **first mile** | Script, slide 9 | Startup slang. | **the first step** |
| 13 | **No model decides anything in this pipeline.** "Written as tests." "Tested and replayed." | Slide 5 | Software words. | **No AI makes a decision. Every step is a simple check we can run again and show your board.** |
| 14 | **routed**, routing | Slides 5, 6, 8 | Vague. | **sent to your lawyer** (or dissemination agent) |
| 15 | **tolled clock**, outside date | Slide 13 card. Script | Legal words. | **the clock pauses** / **the last day** |
| 16 | **gate question** | Slide 11 | Internal. | **One question decides if this is for you** |
| 17 | **pre-issuance** | Slide 11 script | Deal jargon. | **before the bonds are sold** |
| 18 | **intake** | Slides 13, 14. Emails | Mild. | **the short sign-up form** |
| 19 | **TRA §5.2**, **CDA §4(a)** | Slide 7 table | Acronyms. | **Tax agreement §5.2**, **Disclosure agreement §4(a)** |
| 20 | **Listed event notices** | Slide 7 table | "Listed" is rule talk. | **Event notices** |
| 21 | **activity-reviewed, not counsel-cleared** | Slide 3. Script. SEQUENCE disclaimer | Insider phrase. Without context it can also alarm. | **No lawyer has signed off on this method yet. We say that up front.** Needs Stephen's OK: this is an honesty statement. |

## B. Contract words. Keep the word. Add the plain meaning beside it.

These words are fixed in Arthur's post-close letter
(`braintrust/workspace/arthur/2026-09-09-post-close-letter-and-approved-input-ruling.md`, §3 and §4.6).
Change them only with an Arthur ruling.

| Word | Where it is fixed | Plain meaning to show next to it |
|---|---|---|
| **filed / not filed / evidence missing / not testable** | Letter §4.6 (contract term) | filed = we have the file. not filed = not due yet. evidence missing = due date passed, no file. **not testable = no date to check against.** |
| The **control sentence** on slide 3 ("mechanically transcribes", "which undertaking controls", "successor/refunding effects") | Letter §4, website, code | Put one plain line above it: **"We copy what your documents say and what your lawyer tells us. We never decide what it means."** |
| **Items awaiting input** (deck) vs **Open Items list** (letter §3.5) | Letter §3.5 | The deck and the letter use different names. CFOs already know "open items" from audits. Use **Open items list** everywhere. |
| **Evidence vault** | Letter §3.3 | **a labeled folder of every document and report you sent us** |
| **Dissemination agent** | Letter §4.7 | Define once: **the firm that posts your reports to the MSRB's public site for you** |

## C. Accuracy problems found. Not jargon.

1. ✅ **FIXED 2026-09-11 (asterisk + fine print, letter §6.9 numbers).** **The live landing page promised more than the letter.** `frontend/src/pages/tools/ObligationRegisterLanding.tsx` line 30 says we refund the fee in full if we miss ten business days. Letter §6.9 says: late delivery = a partial refund per business day, with a cap. A full refund comes only after the last day. The ruled numbers (`braintrust/workspace/cos/2026-09-09-DECISION-a2post-pricing-and-guarantee.md`) are 2% per day, 20% cap, last day = day 20. The page and the letter must say the same thing.
2. **DONE.** The old price-slide line "Forever custody needs an owner. That is the paid book." made the product sound like an ongoing service. It is one-time. The line is removed. The new slide 12 says what the client gets.
3. **Optional.** The price slide guarantee does not mention the per-day partial refund. That under-promises, so it is lower risk. It can stay as is.

## D. Done in this pass (2026-09-11)

- Candidate Map now has a definition: Day −7 invite, Touch −2, recording email, and the spoken open (slide 1).
- Slide 2: "The rent roll" is now "The quarterly report" (rent roll, enrollment count, patient census).
- New slide 12, **What you get**, from letter §3 and §7: the six parts, handoff, 30 days of "where is it?" answers, and either side can stop. Timing: who qualifies 27:00–27:45, what you get 27:45–28:30. The price is still said at 28:30.
