# PRFAQ-lite — lab/twin-bfms: the internal synthetic pre-to-post BFMS test bed (DRAFT 2026-09-10, dated 2026-11-25)

**Status: DRAFT — admission requires DEC-010 (Stephen's override ruling). EXP-012 files with it.**
Drafts: `lab/twin-bfms/governance/DEC-010.draft.jsonl`, `lab/twin-bfms/governance/EXP-012.draft.jsonl`. Ask: `lab/twin-bfms/governance/decision-request.md`.
Build authority today: Stephen's in-session instruction of 2026-09-10 (quoted in `lab/README.md`); the registry lines stay DRAFT until filed.

**Line / Stage / Constraint (5d gate):** Municipal bonds — ACQ stage 2 Advertise — constraint DEMAND per
`INDUSTRIALIZATION/STAGE-DIAGNOSIS.md` section 1 (ratified 2026-08-04). Caveat on record: OUT-002 (2026-09-02,
`INDUSTRIALIZATION/experiments/registry.jsonl`) found the observed binder across three lines is OPERATOR THROUGHPUT, not the
named constraint; Stephen has not re-ratified. **Why an override:** the lab does not sell and does not attack DEMAND directly.
It removes one decision from the single-human path (a manual checklist becomes a test). That is the OUT-002 test, not the N10 test.
Admission is by explicit override, DEC-007 pattern (`INDUSTRIALIZATION/ENGINEERING-DOCTRINE.md` section 5d; `experiments/PATTERN.md`).

Sources: COS working paper `LAB-BRIEF.md` (2026-09-10, scratchpad; sha256 `f031201cc35a3651da7b45f67e485c0995ab9f04f066e6274d258ef9fa621cb4`);
`C:\Users\st3ja\braintrust\workspace\cos\2026-09-10-RESET-plain-plan.md`.

---

*Future-dated announcement, 2026-11-25:*

The MUNI-PAL repo now holds an internal synthetic test bed under `lab/twin-bfms/` that drives the full Bond Facility
Management System, pre-issuance through post-issuance, on one command with no human in the loop. A lab-generated deal in
BONDI's deal-v0 shape enters at intake and is pushed through the seven pilot stages and nine deal phases inside the existing
test harness (`tests/conftest.py`). Every stage returns one of four verdicts: pass, fail, unknown, not_applicable. The MA gate
reads `not_applicable (internal lab; no client)` and always will. The section 5 checklist that sat at PARTIAL for months
(`docs/pilot/pilot-navigation-system.md`) is now a test that runs in the suite (`tests/integration/test_lab_e2e_housing.py`).
Defects the run found in BFMS are pinned by failing tests that predate their fixes (`lab/twin-bfms/governance/FINDINGS.md`).
The Obligation Register demo (`fulfillment/demo/`) consumes a lab scenario. Nothing shipped to a client. Nothing is public.
Nothing is for sale. Every generated file carries the synthetic legend on its face. twin-bfms is a label, not a claim (DEC-009 section 9.8).

**For whom:** the build team (a fixture pack and a harness instead of two frozen entities); the pilot gate
(`pilot_smoke_test_green` can now mean something before a real client exists); the Obligation Register demo
(a second synthetic deal, post-close, to show against).

**FAQ (self-falsification):**

- *Why now?* The 9/10 reset made MUNI-PAL the one repo and named the Obligation Register the one offer
  (`C:\Users\st3ja\braintrust\workspace\cos\2026-09-10-RESET-plain-plan.md`). The full BFMS is the prior offer and has never been
  driven end-to-end by anything but hands. Three blockers (attorney, MA, the MSRB data purchase) stop selling, not testing.
  Testing costs $0 cash. Waiting costs the same defects found later.
- *Why so thin?* One harness, one deal shape, nineteen stages (S00–S18, `lab/twin-bfms/docs/STAGE-MAP.md`), four verdicts.
  No simulator. No new synth engine (BONDI owns the contract; Arthur owns the port). No UI. No new repo. The quarantined synth
  branch and the old OneDrive packs stay out. A thin lab that runs beats a rich lab that waits on a constant audit.
- *Biggest risk?* A toy that demos well and changes no decision. Mitigation: the kill line counts defects found and consumer
  pulls (`lab/twin-bfms/docs/CONSUMER-PULLS.md`), not stages green. Zero defects by 11/25 is a kill, because a run that finds
  nothing in ~132 endpoints is not testing anything. As of 2026-09-10 the build already carries eleven (F5–F15).
- *What kills it?* EXP-012: fewer than 5 of 7 pilot stages driven by 10/10; zero BFMS defects surfaced; zero attested consumer
  pulls; any new red in the suite; any fence breach (public surface, MSRB platform string outside the CDA quote, Class D input,
  MA gate satisfied, sizing/pricing engine called) = VOID.
- *What survives a kill?* The process map of what BFMS actually requires at each stage (`docs/STAGE-MAP.md`), the defect list
  with its failing tests (`governance/FINDINGS.md`), and the finding that the section 5 checklist cannot be automated as written.
  Written down at filing, not discovered after.
- *Compliance?* `C:\Users\st3ja\muni-twin\QUARANTINE.md` classes A/B/C only, D void; DEC-008 zero platform references outside the
  pinned Rule 15c2-12 quote; TR-1 hard stop — outputs never leave the repo or local disk; status-based UPL/MA rule — no client,
  no advice, no deal verdict words; BFMS spec section 1 — no sizing, pricing or approval; on-face synthetic legends; fictional
  names collision-checked; "twin-bfms" is a label, not a claim (DEC-009 section 9.8). Enforcement table: `lab/twin-bfms/LAW.md`.
