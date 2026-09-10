# BD Engine — Rule of 100

The daily marketing/accountability engine from the [Business Development Framework](../docs/business-development-framework.md) (Sections 8–9). It exists to fix the #1 binding constraint: **inconsistent lead flow caused by inconsistent daily inputs.**

## What it does

Every weekday at ~7:55am a scheduled agent (`bd-rule-of-100`):
1. Checks yesterday's quota completion and computes the streak.
2. Drafts today's Core-Four outreach pack (warm, cold, content, comments) into `outbox/YYYY-MM-DD.md`.
3. Appends an accountability entry to `logs/daily-log.md`.
4. Pushes a condensed summary to Stephen via Telegram.
5. On Fridays, adds a weekly tally (quota hit-rate + funnel movement).

**The engine drafts; Stephen sends.** Nothing goes out the door without human review — consistent with the Bond Strategist Phase-1 control (licensed-professional review is primary).

## Files

| File | Role |
|---|---|
| `config.md` | Quota, ICP, channels, ratchet rules — **edit this to tune the engine** |
| `RUNBOOK.md` | The procedure the scheduled agent executes each morning |
| `prospects.csv` | Working lead list (warm + cold) |
| `funnel.csv` | Event-level sales funnel (contact → schedule → show → offer → close → cash) |
| `templates/outreach-templates.md` | Warm/cold scripts + content angles (CLOSER / proof-led) |
| `proof/index.md` | Proof library — testimonials and result artifacts marketing draws from |
| `outbox/` | Daily draft packs awaiting Stephen's review + send |
| `logs/daily-log.md` | Append-only accountability log |

## The one metric

**Core-Four daily quota hit (Y/N).** Everything else is downstream. The funnel sheet tells you *where* to improve; the streak tells you *whether the engine is alive.*
