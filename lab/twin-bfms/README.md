# lab/twin-bfms — synthetic pre-to-post drive of the full BFMS

> SYNTHETIC RESEARCH ARTIFACT — MUNI-TWIN — NOT LEGAL ADVICE — NOT PREPARED BY AN ATTORNEY — NOT AN OFFER OF SECURITIES. Fictional names collision-checked against real firms.

**twin-bfms is a label, not a claim (DEC-009 section 9.8).** Internal R&D. Nothing for sale. Nothing public.
Authority: Stephen's in-session instruction of 2026-09-10 (quoted in `lab/README.md`); registry lines stay DRAFT until filed.
Source brief: COS working paper `LAB-BRIEF.md` (2026-09-10, scratchpad; sha256 `f031201cc35a3651da7b45f67e485c0995ab9f04f066e6274d258ef9fa621cb4`).
Reset ruling: `C:\Users\st3ja\braintrust\workspace\cos\2026-09-10-RESET-plain-plan.md`.

## 1. What is driven

Three things that already exist, all read-only:

| consumed | where | how |
|---|---|---|
| the full BFMS ASGI app (17 routers) | `src/munipal/main.py` | in-process, exactly as `tests/conftest.py:26-34,62-111,128-160` does: in-memory SQLite, `httpx.AsyncClient(ASGITransport(app))`, HS256 JWT, `AUTH_ENFORCEMENT_V2=true`, `ANTHROPIC_API_KEY=""` so extraction runs `rules_based_fallback` (`src/munipal/services/extraction/rules_based_extractor.py`) |
| the BONDI deal-v0 emission format | `APPLIED RESEARCH/bondi-bfms/synth-issuance/schema/deal-v0.json` (read live); format transcription `fixtures/bondi-reference/format.json` | consumed, never vendored; the lab emits its own `bondi/` files with `labkit/events.py` |
| the sellable Obligation Register algorithm | `fulfillment/demo/run.py::build()` | `importlib` with `mod.ROOT` pointed at a run-assembled directory; never `main()` / `render_html()` (`run.py:200-259`) |

Out of bounds, by construction and by fence: `src/munipal/engines/**` (sizing / pricing / approval, BFMS spec section 1),
the LLM client, `alembic`, any send or deploy library, any file from the quarantined old synth branch or the old OneDrive packs.

## 2. The four statuses

Every stage, sub-assertion, conformance row and gate is exactly one of
`pass | fail | unknown | not_applicable` (`labkit/types.py`, a pydantic `Literal`; `labkit/law.py::FOUR_VALUES`).

- `pass` / `fail`: observed behaviour matched / did not match the reviewed expectation.
- `unknown`: the scenario does not carry the fact (a `null` date, an uncarried document). Never rounded to pass.
- `not_applicable`: a rule says the lab may not measure it (client gates, WP5 models, sensing, cross-platform). The reason is the rule.

The two client gates are `Literal["not_applicable"]` — a pass cannot be constructed
(`registered_ma_confirmed`, `engagement_scope_signed`; `src/munipal/services/pilot_onboarding.py:180-199`).
`pilot_smoke_test_green = pass` means only that this synthetic run matched its reviewed expectations in-process
(`law.SMOKE_GATE_MEANING`).

No date is ever computed. Every date in `bondi/event_log.csv` is a scenario literal (`tests/unit/test_lab_forbidden_tokens.py`).

## 3. Run (WSL-native only)

```
wsl.exe -d Ubuntu -e bash -lc 'cd ~/Developer/MUNI-PAL && PYTHONPATH=src .venv/bin/python lab/twin-bfms/run_lab.py --scenario lab/twin-bfms/scenarios/SYN-HSG-AZ-2025-LAB01.synthetic.json'
```

- `--asof` is not accepted; `asof` comes from the scenario (`lab.asof`).
- Exit 0 iff the report verifies and no fence-class violation occurred.
- Output: `runs/<run_id>/` with `run_id = <deal_id>__<asof>__<sha256(scenario bytes || repo_commit)[:8]>`.
- `runs/` is gitignored (`lab/twin-bfms/.gitignore`), local disk only, deleted after golden freeze (`LAW.md`, retention rule).

Regenerate the packs (deterministic; refuses to write if the offline extractor self-check fails):

```
wsl.exe -d Ubuntu -e bash -lc 'cd ~/Developer/MUNI-PAL && PYTHONPATH=src .venv/bin/python lab/twin-bfms/labkit/generate_pack.py --help'
```

Operator walkthrough: `docs/WALKTHROUGH.md`.

## 4. How to read a report

`runs/<run_id>/run-report.json` (canonical JSON, hash-sealed) and `run-report.md` (rendered from the json only). Read in this order:

1. Legend line and `label_notice`.
2. Header: `scenario_id`, `seed`, `repo_commit`, `repo_dirty`, `pins` (`run_py_sha256`, `build_fixtures_sha256`, `pack_manifest_sha256`, `bondi_format_json_sha256` — must equal `packs/_pins.json`), `environment.extraction_mode` (must be `rules_based_fallback`), `environment.sensing_corpus_available` (must be `{healthcare: false, waste: false}`).
3. `pilot_gates`: both client gates `not_applicable`; `pilot_smoke_test_green` pass/fail; `known_gaps_accepted` lists the golden-expected F9 and F16 fails.
4. Stage table S00–S18 (`docs/STAGE-MAP.md`): id, station, WP/P, DealPhase, pilot stage, status, reason.
5. Deal trace (six stations): one row per `event_log.csv` row with the BFMS object touched, the evidence document or register row, and the "not carried by scenario" column.
6. `register_summary`: the four register status codes only (`fulfillment/demo/run.py::STATUSES`); `base_equivalence` against the demo build.
7. `bfms_emitted_language`: BFMS-native prose is kept as sha256 + a 120-char excerpt, never restated in `lab_statements`.
8. `golden_diff` (must be empty) and `content_hash` (the e2e test recomputes it).

Goldens: `expected/<deal_id>/run-report.expected.json` — statuses and counts only, derived from an actual run and reviewed by COS, never typed by hand.
Known BFMS gaps are encoded there as expected `fail` / `unknown` (an un-gameable ratchet; a `src/` change reddens the lab test until the golden is re-reviewed).

## 5. The three scenarios

| id | file | knob | exercised path |
|---|---|---|---|
| SYN-HSG-AZ-2025-LAB01 | `scenarios/SYN-HSG-AZ-2025-LAB01.synthetic.json` | none (base) | full S00–S18; register equals the demo build row-for-row (`fulfillment/demo/output/summary.json`: 17 obligations, filed 6 / not filed 1 / evidence missing 2 / not testable 8, gaps 2, open items 3) |
| SYN-HSG-AZ-2025-LAB02 | `scenarios/SYN-HSG-AZ-2025-LAB02.synthetic.json` | `late_afs` | post-close: three FY2025 vault files absent; OB-01 / OB-09 / OB-10 flip to `evidence missing`; constraint `late_afs` stays `unknown` |
| SYN-HSG-AZ-2025-LAB03 | `scenarios/SYN-HSG-AZ-2025-LAB03.synthetic.json` | `drop_required_artifact: site_control_permits` | pre-close: 4 intake files; S06 reports the 7 dropped paths `unknown`; checklist / readiness / disclosure deltas recorded in the golden |

Variants carry `derived_from` + `knob_delta`; `labkit/scenario.py` materialises them and the fence asserts the diff touches exactly the knob keys.
Same fictional family as `fulfillment/demo/scenario/syn-hsg-2025.synthetic.json`; names only from `scenarios/names/fictional-names.v1.json`,
whole-phrase blocklist `scenarios/names/blocklist.v1.txt`. The `deal_status=on_hold` knob is emitter/gate unit-tested only; no LAB04 pack (decision 2, `governance/decision-request.md`).

Committed packs: `packs/<deal_id>/` (text only: `PACK-MANIFEST.json`, `intake/`, `closing-documents/`, `post-close/`, `bondi/`); pins in `packs/_pins.json`.

## 6. Findings (never fixed in `src/`; full text in `governance/FINDINGS.md`)

| id | one line | path |
|---|---|---|
| F1 | production serves `munipal.main:app`; docs and fence say `sensing_app` | `railway.toml:2`; `docs/architecture/SENSING_PILOT_FUNNEL.md:84-86` |
| F2 | two pre-existing red tests on master | `tests/contract/test_openapi_contract.py`; `tests/unit/test_sensing_pilot_funnel_contract.py` |
| F3 | the old OneDrive synthetic packs are not golden | `C:\Users\st3ja\muni-twin\QUARANTINE.md` ("generation lineage unproven") |
| F4 | the pilot-nav section 5 e2e protocol was never automated | `docs/pilot/pilot-navigation-system.md` section 5 |
| F5 | housing vocabulary split across four files | `src/munipal/services/sector_archetypes.py:112-127`; `sector_playbooks.py:395-415`; `readiness_service.py:124-166`; `playbook_data.py` P3.3 |
| F6 | the MSRB platform token outside the CDA quote in the demo | `fulfillment/demo/approved-inputs.csv`; `fulfillment/demo/build_fixtures.py:176-184,228` |
| F7 | pilot gate display_name still names the old pack | `src/munipal/services/pilot_onboarding.py:189` |
| F8 | checklist reads the UCS constant, not the playbook row | `src/munipal/services/checklist_service.py:29,76,105` |
| F9 | no artifact-level hash / dedup | `docs/architecture/BFMS_DATA_MODEL_PRIMITIVES.md` |
| F10 | the sellable demo scenario is not valid deal-v0 (no `stations`) | `fulfillment/demo/scenario/syn-hsg-2025.synthetic.json` |
| F11 | two route defects (playbook detail 500; deal-document status `.value` on str) | `src/munipal/core/schemas/playbook.py:26`; `src/munipal/api/routes/deal_documents.py:233` |
| F12 | `housing.*` paths untyped; fallback ignores project sector | `src/munipal/services/extraction/rules_based_extractor.py:33-50`; `src/munipal/api/routes/extraction.py:168-180` |
| F13 | demo seeder inserts approved facts with no chunks | `scripts/seed_demo_scenarios.py` |
| F14 | alembic seeds carry the platform token / Postgres-only SQL | `alembic/versions/20260226_0001_*`; `alembic/versions/20260127_0002_*` |
| F15 | sensing auto-discovers the Class D corpus unless `MUNIPAL_ROOT` is pinned | `src/munipal/services/sensing.py:33-53` |

## 7. Consumers

Nothing has been pulled yet. Ledger: `docs/CONSUMER-PULLS.md` (four rows, dated when a consumer attests in its own work product).

| consumer | owner | what it would pull |
|---|---|---|
| Obligation Register demo (`fulfillment/demo/`) | Stephen (offer owner) / Arthur (bond builds) | a lab scenario in deal-v0 shape as a second post-close deal |
| pilot gate `pilot_smoke_test_green` (`src/munipal/services/pilot_onboarding.py`) | Stephen | the e2e test replaces the manual section 5 checklist in `docs/pilot/pilot-navigation-system.md` |
| BONDI synth-issuance (`APPLIED RESEARCH/bondi-bfms/`) | BONDI / Arthur (port owner) | the lab's BFMS conformance table (what the six stations carry that BFMS cannot represent) |
| muni-twin EXP-011 review 2026-11-25 (`C:\Users\st3ja\muni-twin\experiments\EXP-011\`) | Stephen (owner) / Arthur + Ben (evaluators) | the defect list with its failing tests, as evidence for or against the twin program's own claims |

## 8. Layout

```
lab/twin-bfms/
  README.md  LAW.md  .gitignore
  labkit/        law types provenance names scenario events generate_pack harness bfms_driver replay post_close report
  run_lab.py
  scenarios/     three deal-v0 scenario files + names/
  packs/         committed generated packs + _pins.json
  fixtures/      bondi-reference/format.json + PROVENANCE.md
  expected/      status-only goldens (derived from runs)
  docs/          STAGE-MAP CONSUMER-PULLS WALKTHROUGH
  governance/    FINDINGS PRFAQ-lite EXP-012.draft.jsonl DEC-010.draft.jsonl decision-request
  runs/          gitignored; local disk only
```

Fence tests: `tests/unit/test_lab_*.py` (ten files) + `tests/integration/test_lab_e2e_housing.py`; bridge `tests/lab_support.py`.

SYNTHETIC RESEARCH ARTIFACT — MUNI-TWIN — NOT LEGAL ADVICE — NOT PREPARED BY AN ATTORNEY — NOT AN OFFER OF SECURITIES. Fictional names collision-checked against real firms.
