# CONSUMER PULLS — dated ledger

A pull is attested by the consumer in its own work product, never by the builder
(EXP-012 kill line: zero attested pulls by 2026-11-25 = kill; `lab/twin-bfms/governance/EXP-012.draft.jsonl`).
This file is updated only when a row changes; the date goes in the `status` column.
twin-bfms is a label, not a claim (DEC-009 section 9.8).

| # | consumer | owner | what artifact would be pulled | how a pull is checked | status |
|---|---|---|---|---|---|
| 1 | Obligation Register demo — `fulfillment/demo/` (the sellable offer) | Stephen (offer owner); Arthur (bond builds) | a lab scenario in deal-v0 shape (`lab/twin-bfms/scenarios/SYN-HSG-AZ-2025-LAB0N.synthetic.json`) or a lab pack (`lab/twin-bfms/packs/<deal_id>/post-close/`) used as a second post-close deal | a commit under `fulfillment/demo/` that reads a `lab/twin-bfms/` path, or a demo output whose `deal_id` is a `SYN-…-LABNN` id; `git log -- fulfillment/demo` (read-only) shows the change | not yet pulled |
| 2 | pilot gate `pilot_smoke_test_green` — `src/munipal/services/pilot_onboarding.py:180-199` | Stephen | `tests/integration/test_lab_e2e_housing.py` as the automated form of the manual section 5 checklist in `docs/pilot/pilot-navigation-system.md` | `docs/pilot/pilot-navigation-system.md` section 5 names the lab test as the gate evidence, or `pilot_onboarding.py:189` display_name is renamed to point at it (F7) — a `src/` or `docs/pilot/` change by Stephen's hands, never the lab's | not yet pulled |
| 3 | BONDI synth-issuance — `APPLIED RESEARCH/bondi-bfms/synth-issuance/` | BONDI (engine contract); Arthur (port owner) | the conformance table from a sealed run (`runs/<run_id>/run-report.json`, `conformance_table`): which station events BFMS can represent, which it cannot (`not_applicable`), which the scenario does not carry (`unknown`) | a BONDI working paper or scenario file under `APPLIED RESEARCH/bondi-bfms/` that cites a lab run id or `lab/twin-bfms/docs/STAGE-MAP.md` | not yet pulled |
| 4 | muni-twin EXP-011 review 2026-11-25 — `C:\Users\st3ja\muni-twin\experiments\EXP-011\` | Stephen (owner); Arthur + Ben (evaluators) | `lab/twin-bfms/governance/FINDINGS.md` and the failing tests that pin each surfaced BFMS defect | the EXP-011 review record or an OUT-line in `INDUSTRIALIZATION/experiments/registry.jsonl` cites a lab finding id (F5–F15) or a lab test name; filed by Stephen, never by the lab | not yet pulled |

Rules for editing this file: add a date and a path in `status` (e.g. `pulled 2026-10-03 — fulfillment/demo/…`); never mark a row pulled on the builder's word;
never attach a run output to any external channel to obtain a pull (TR-1; `lab/twin-bfms/LAW.md` rule 3).
