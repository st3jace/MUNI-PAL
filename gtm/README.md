# gtm/ — front-end acquisition

Everything that finds a prospect and gets them to a first call lives here.

| Folder | What it holds |
|---|---|
| `bd-engine/` | The lead list (`prospects.csv`), funnel, outreach templates, daily outbox, proof library. Moved here from OneDrive 2026-09-10. |
| `sourcing/` | Where new names come from. Non-EMMA sources only: issuer board agendas and minutes, state authority reports, county recorder. |

Rules:
- Outreach goes only to **obligated persons who have already issued** (`entity_type=obligated_person`, `has_issued=Y`).
- Municipal entities are nurture only. Professional firms (counsel, MA) are inbound-only and uncompensated.
- Nothing sends without Stephen. The engine drafts; Stephen sends.
- The 24-ask decision doc and the P-ladder are parked. See `braintrust/workspace/cos/2026-09-10-RESET-plain-plan.md`.
