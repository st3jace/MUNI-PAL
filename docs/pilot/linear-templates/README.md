# Linear Engagement Templates (BFMS External)

One Linear project per **signed** client engagement — created at engagement-letter
signature, never at lead stage (leads live in the funnel / lead-scoring world, not
Linear). Projects land on team **MPC (Muni-Pal Clients)** under the initiative
**BFMS - External (Client Engagements)**.

## Linear architecture (created 2026-08-03)

| Thing | Where |
|---|---|
| Initiative — internal build | `BFMS - Internal (Build & Operate)` — platform/site/corpus projects on ELA + ART |
| Initiative — client work | `BFMS - External (Client Engagements)` — one project per engagement, team MPC |
| Team MPC | Journey workflow states: Gates → Onboarding → WP Delivery → Measurement → Close-out |
| Workspace labels | `tier:*` (subscription/t1/t2/t3/partner), `sector:*` (healthcare/waste/education), `gate:*` (legal/engagement/platform/measurement/commercial) |
| Agent dispatch | Existing `agent:claude` / `agent:arthur` labels + Backlog→Todo approval gate apply to MPC issues too |

## How to stamp a new engagement

1. Copy the tier template into the engagement's working folder as
   `.linear-sync/deliverables.json`:
   - `engagement-t1-diagnostic.deliverables.json` — Tier 1 (credit memo + gap analysis)
   - `engagement-t2-standard.deliverables.json` — Tier 2 (T1 + active deal coordination)
2. Replace every placeholder: `{{CLIENT}}`, `{{SECTOR}}` (healthcare|waste|education),
   `{{SUBSECTOR}}`, `{{PAR}}`.
3. Configure linear-sync for team **MPC** (not ELA/ART) and run `/linear-sync` bootstrap.
4. GraphQL follow-up pass (linear-sync does not push these): apply labels named in each
   issue description (`tier:*`, `sector:*`, `gate:*`) and any due dates.
5. Do **not** re-bootstrap over an existing `.linear-sync/state.json` — it duplicates.
   State lives with the engagement folder; keep it.

## Rules of the road

- **A failed gate is a blocker, not a risk to manage.** M1 must be fully GREEN before
  kickoff work starts.
- Tier 3 has no template yet — extend the T2 template with the s6.5 remediation
  deliverables when the first T3 signs.
- Client documents never attach to Linear issues; they live in the platform vault.
  Issues reference, never carry.
- Compliance voice in every client-facing artifact: "here is what comparables had,"
  never "here is what you need."

Source of truth for all step content: `docs/pilot/pilot-navigation-system.md` +
the Notion Client Journey Storyboard (Bond Facility Management engine page).
