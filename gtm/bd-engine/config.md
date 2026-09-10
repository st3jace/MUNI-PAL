# BD Engine Config

*Edit this file to tune the engine. The daily agent reads it on every run.*

## Daily quota (Core Four)

The Rule of 100 here = **~100 minutes/day of advertising input**, mapped to counts appropriate for a niche B2B market. Consistency beats volume; the ratchet rule below handles growth.

| Channel | Daily quota | Notes |
|---|---|---|
| Warm outreach (1-to-1, people who know you) | 10 touches | Prior contacts, network, past collaborators, referral sources |
| Cold outreach (1-to-1, don't know you) | 10 new contacts | LinkedIn / email to ICP-fit operators and intermediaries |
| Content (1-to-many) | 1 post | Proof-led; bond-readiness insight, deal anatomy, operator education |
| Engagement comments | 10 comments | Best-comment-on-the-thread in spaces where the ICP reads |
| Paid ads | OFF | Enable only after organic loop produces consistent funnel data |

**Ratchet rule:** quotas may only go UP, and only after 4 consecutive weeks ≥80% hit-rate. Never lower a quota mid-slump — that's the failure mode the engine exists to prevent.

**List-building counts.** If `prospects.csv` has fewer than 5 sendable warm or 10 sendable cold prospects, the day's quota for that channel converts to list-building (researching and adding qualified names). An outreach you can't send is a list problem, not a quota waiver.

## Strategic focus (Stephen, 2026-09-08 — SUPERSEDES 2026-06-10)

**Two-cohort operator GTM.** Launch Shop replaces the SVIDA technical-assistance income (last scheduled payment 2026-11-16) by attracting **operators** who want help navigating bond finance. The IDA becomes a lead-generation client (conduit option, not obligation). Charter: `LAUNCH SHOP/GTM/00-GTM-PROGRAM-CHARTER.md`.

- **Cohort 1 — sector operators:** healthcare, education, housing, opportunistic (water/wastewater). Front door muni-pal.io tools + Skool community "Bond Finance for Operators".
- **Cohort 2 — WTE co-GP:** waste-to-energy developers, counties, feedstock/offtake, impact capital; objective = co-GP + first demonstration unit, starting with Caldor (UCS). Skool community "WTE Demonstration Unit".
- The 06-10 "IDA-only origination, defer new-client acquisition" rule is **withdrawn**. New-client (operator) acquisition is now the primary motion for BOTH cohorts.
- The engine's 81-day finding stands: drafting is not the constraint, sending is. Until Stephen decides D1 (send authority) the engine drafts; once D1 = "Claude sends after Telegram approval", the pack carries a `SEND-READY` block per touch.

## ICP (who we're advertising to)

**Cohort 1 — sector operators (primary):** CFOs, executive directors, developers of hospitals/FQHCs/senior living, charter and private schools, affordable and workforce housing, water/wastewater districts and developers; pursuing or considering tax-exempt / IRB bond financing for a facility; typically told "you're not ready" or unaware bond finance is accessible. Pain: readiness, disclosure burden, no map of the process, no way to judge cost of issuance. Arizona fit is a bonus (SVIDA conduit option), never a filter.

**Cohort 2 — WTE (primary):** waste-to-energy / pyrolysis / gasification developers with a named project, county solid-waste directors, feedstock and offtake counterparties, impact capital. Pain: no running unit anywhere, capital stack unpapered, permits ahead of everything else. Lead with Caldor's build log.

**Secondary — issuers & intermediaries (nurture only):** IDAs/EDCs, bond counsel, municipal advisors, placement agents. Awareness targets; one relationship = many operator referrals.


## Offers the outreach points to

Ladder (charter §3; nothing above rung 1 is sold before counsel answers `LAUNCH SHOP/GTM/01-COUNSEL-BRIEF-REGULATORY-FRAMEWORK.md`):
0. **Free** — muni-pal.io Readiness Assessment + Market Intelligence Report; free Skool community (per cohort).
1. **Paid community** ($99–$199/mo) — Classroom modules, templates, monthly office hour.
2. **Navigator retainer** ($1,000–$2,500/mo) — 2 working sessions/mo, readiness roadmap, document coordination, AI-ops enablement. COUNSEL GATE.
3. **Diagnostic / Engagement** ($15K–$75K) — Bond Strategist 3-tier. COUNSEL GATE.
4. **Co-GP** (WTE only) — equity + dev fee in the project company.

Entry point for everything: a free readiness conversation (the "hidden-cost interview" — see templates) or a Skool join.


## Prospect sources

- `prospects.csv` (this directory) — the working list.
- Clay (MCP, workspace "ELaunch Shop") — company/contact search + enrichment; lists per cohort. Champion Social (localhost:4251) is DOWN and parked; do not probe it.
- Resend segments: "Cohort 1 - Sector Operators…" and "Cohort 2 - WTE Co-GP…" — the send rail.
- EMMA filings (housing-corpus crawl output) — issuers/operators with recent or pending activity in target sectors.

## Hard rules

1. **Draft, never send.** All outreach goes to `outbox/` for Stephen's review. The agent never emails, posts, or messages a prospect directly.
2. **Proof > promise.** Every draft leads with a result or a specific insight, never a capability claim. Pull from `proof/index.md`.
3. **No fabricated specifics.** If the proof library lacks a relevant artifact, the draft uses honest positioning ("we built the system we use on live engagements"), not invented numbers.
4. **Log everything.** No run ends without the daily-log append.
