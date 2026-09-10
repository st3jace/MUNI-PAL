# DECISION REQUEST — lab/twin-bfms (2026-09-10)

Written for Stephen. Short words. One idea per line. Two rulings needed, three build choices.
Source of the ask: COS working paper `LAB-BRIEF.md` (2026-09-10, scratchpad; sha256 `f031201cc35a3651da7b45f67e485c0995ab9f04f066e6274d258ef9fa621cb4`), section 1.
Reset ruling: `C:\Users\st3ja\braintrust\workspace\cos\2026-09-10-RESET-plain-plan.md`.
Nothing here is filed until you file it. The build ran on your in-session instruction of 2026-09-10 (quoted in `lab/README.md`).

## What you asked

- Fork the full BFMS (pre-issuance to post-issuance), not the 10-Day Obligation Register.
- Build an internal R&D copy that makes synthetic data and tests the whole bond process, pre to post.
- Keep building while three blockers stay open: attorney (TR-1), MA hire, the MSRB data purchase (no-go).

## What is built

- A folder `lab/twin-bfms/` inside the MUNI-PAL repo, beside `gtm/`, `fulfillment/`, `ops/`. No new repo. No long branch.
- Internal. Synthetic only. Not for sale. Not public. It never touches Railway, Vercel, Notion, email, Telegram or Linear.
- It drives the real BFMS API (`src/munipal/main.py`, 17 routers) in-process through the test harness (`tests/conftest.py`).
- It turns the manual section 5 checklist (`docs/pilot/pilot-navigation-system.md`, WP1–WP6, never run) into a test that runs on one command.
- "twin-bfms" is a label, not a claim (DEC-009 section 9.8). Every generated file carries the synthetic legend (`C:\Users\st3ja\muni-twin\QUARANTINE.md:66-67`).

## Two rulings

### D1 — Admit the lab by override (DEC-010)

The stage gate says Muni = Stage 2 Advertise, constraint DEMAND (`INDUSTRIALIZATION/STAGE-DIAGNOSIS.md` section 1). The lab does not sell. So it needs your override, logged (`ENGINEERING-DOCTRINE.md` section 5d; `experiments/PATTERN.md`).

- **Option A — Admit now, with the scope fence.** Conditions: internal only; synthetic only; nothing for sale; nothing public; muni-twin OUT-list untouched (the lab consumes twin fixtures, it is not the twin program); fence tests are the enforcing channel; review 2026-11-25 with EXP-011. Drafts: `lab/twin-bfms/governance/DEC-010.draft.jsonl`, `lab/twin-bfms/governance/EXP-012.draft.jsonl`.
- **Option B — Refuse.** P1 (design + drafts) is the stopping point. Nothing under `lab/` is kept. The section 5 checklist stays manual. Wait for EXP-011's verdict first.
- Context to pick fast: OUT-002 (2026-09-02) found the real binder is operator throughput, not demand. The lab removes a decision from your path. Cost is $0 cash, agent hours only. Risk tier R0: no client, no money, no real data.
- **COS position: A.**

### D2 — The public API entrypoint (finding F1)

- **Option A — Switch Railway to `munipal.sensing_app`.** That is what the doc says (`docs/architecture/SENSING_PILOT_FUNNEL.md:84-86`, ELA-56) and what the fence tests assert (`tests/unit/test_public_sensing_deployment_boundary.py`). Two repo changes must land first, proven by tests: (1) mount `stripe.router` in `src/munipal/sensing_app.py` — today only `main.py` mounts it and the public `frontend/src/pages/tools/PricingPage.tsx` calls it; (2) add the obligation-register intake/privacy routes to `allowed_public_routes` in `src/munipal/services/sensing_pilot_funnel.py` (this also clears pre-existing red test F2-2). Then you change `railway.toml:2`. Your hands only.
- **Option B — Keep `munipal.main` behind auth.** Zero deploy risk today. Leaves the full BFMS route set on the public `/openapi.json` and leaves the doc and the fence tests contradicting production.
- Context to pick fast: the Obligation Register (the one thing we sell) is mounted in both apps, so A does not break the offer once Stripe is mounted. B is a known contradiction in the docs until fixed.
- **COS position: A**, staged: repo changes first (tests green), then your Railway flip. The lab is admitted under either outcome.

## Three build choices (defaults applied; change them if you want)

- **Variant set.** Default: LAB01 base, LAB02 `late_afs`, LAB03 `drop_required_artifact: site_control_permits`; the `deal_status=on_hold` knob is unit-tested only, no LAB04 pack. Promote on_hold to a committed pack? (adds a pack, a golden, ~10 min per suite run)
- **Golden policy.** Default: status-only goldens that encode known BFMS gaps as expected `fail` / `unknown`. A `src/` improvement reddens the lab test until the golden is re-reviewed. Alternative: the e2e test asserts only lab invariants and carries BFMS gaps as report-only rows.
- **BONDI reference.** Default: `generate.py` is never run; its constants are ast-transcribed to `lab/twin-bfms/fixtures/bondi-reference/format.json` with a source sha256 (`fixtures/bondi-reference/PROVENANCE.md`). The parity fence compares against the OneDrive file when present, else skips with a reason.

## Things you should know

- F1. `api.muni-pal.io` runs `uvicorn munipal.main:app` (`railway.toml:2`). Docs and fence tests say `sensing_app`. Production contradicts the repo.
- F2. Two tests are red on master today (520 passed, 2 failed): OpenAPI snapshot drift (`tests/contract/test_openapi_contract.py`) and the sensing scope test (`tests/unit/test_sensing_pilot_funnel_contract.py`). Not fixed silently. Reported here.
- F3. The old OneDrive synthetic packs are not golden: lineage unproven, real firm names inside (`C:\Users\st3ja\muni-twin\QUARANTINE.md`). The lab makes its own packs.
- F4. The section 5 end-to-end protocol was never automated. The lab makes it a test.
- F5–F15. Eleven BFMS behaviours the build observed, each with a path: `lab/twin-bfms/governance/FINDINGS.md`. One needs a `src/` rename by your hands (F7, `src/munipal/services/pilot_onboarding.py:189`).

## What happens next

- If D1 = A: you file DEC-010 and EXP-012 into `INDUSTRIALIZATION/experiments/registry.jsonl` (PIT law: agents never append). COS commits `lab/` once, locally. No push.
- If D1 = B: `lab/` is removed before any commit; this file and the drafts survive in the scratchpad record.
- If D2 = A: the two repo changes land with tests; you flip `railway.toml` when green. If D2 = B: the lab fence still lands; F1 stays open in the journal.
- Review 2026-11-25 with EXP-011. Kill lines are in the drafts. A lab that demos well but changes no decision is retired, not renewed.
