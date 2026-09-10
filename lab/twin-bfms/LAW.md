# LAW — what binds lab/twin-bfms and what enforces it

Source: COS working paper `LAB-BRIEF.md` (2026-09-10, scratchpad; sha256 `f031201cc35a3651da7b45f67e485c0995ab9f04f066e6274d258ef9fa621cb4`), section 4.
Reset ruling: `C:\Users\st3ja\braintrust\workspace\cos\2026-09-10-RESET-plain-plan.md`.
Constants that transcribe these rules live in `lab/twin-bfms/labkit/law.py`; the fence vocabulary lives in
`scenarios/names/forbidden-tokens.v1.txt` and `scenarios/names/blocklist.v1.txt` (data files, so no lab `.py` spells a forbidden token).

**twin-bfms is a label, not a claim (DEC-009 section 9.8).**

## Rule → enforcement

| # | rule (source) | how the lab obeys | enforcing test / structure |
|---|---|---|---|
| 1 | Provenance classes A/B/C only, D void; on-face legend on every generated document (`C:\Users\st3ja\muni-twin\QUARANTINE.md`, legend lines 66-67) | `mode == "synthetic"` only (calibration rejected structurally, `labkit/scenario.py`); inputs = `fulfillment/demo` constants + L1 metadata; `MUNIPAL_ROOT` pin standalone / `sensing._EMMA_EXTRACTOR` monkeypatch under pytest so the Class D corpus is never opened (asserted in S00 and the e2e test); legend stamped by the single writer `labkit/provenance.py` | `tests/unit/test_lab_forbidden_tokens.py::test_lab_quarantine_rule3_grep`; `tests/unit/test_lab_pack.py::test_lab_legend_and_envelope_by_construction`; `tests/integration/test_lab_e2e_housing.py` (`_corpus_available` False) |
| 2 | DEC-008: zero MSRB-platform references; synthetic only | the platform token survives once per pack, inside the CDA Rule 15c2-12 quote (`closing-documents/03-continuing-disclosure-agreement.md`, under `## Section 4`, count pinned in `law.EMMA_ALLOWLIST`); OB-01 text, five recipients and the vault recipient scrubbed at re-emission; run outputs scanned in S18; `alembic` never imported | `tests/unit/test_lab_forbidden_tokens.py::test_lab_emma_only_in_cda_quote_pinned`; `tests/unit/test_lab_import_boundary.py::test_lab_never_calls_engines_llm_or_alembic` |
| 3 | TR-1 hard stop: no twin artifact leaves the build team until the counsel reserve is funded (EXP-011 guardrails) | outputs only under `lab/` (repo) and `runs/` (gitignored, local disk); no send/deploy imports; no route added; the external advisory package is never generated | `tests/unit/test_lab_import_boundary.py::test_lab_never_calls_engines_llm_or_alembic`; `::test_lab_not_mounted_or_deployed`; retention rule below |
| 4 | Status-based UPL/MA rule; four-valued honesty; no invented date, document or event (BONDI: unknown is first-class) | `PilotGates` client gates are `Literal["not_applicable"]`; `StageStatus` Literal; `RunReport.lab_statements` validator rejects `compliant` / `approved` (except "approved fact(s)") / `recommend*`; BFMS prose kept as sha256 + 120-char excerpt; scripted reviewer labelled "NOT a human, NOT a Bond Strategist"; absent documents recorded `absent_by_scenario`; the legend's own collision claim printed with `web_or_registry: unknown (not performed)` | `tests/unit/test_lab_honesty.py::test_lab_ma_gate_structural_and_four_valued`; `::test_lab_smoke_gate_rule_table`; `tests/unit/test_lab_forbidden_tokens.py::test_lab_no_computed_dates` (event_log dates ⊆ scenario literals) |
| 5 | BFMS Build Spec section 1: evidence-first; AI proposes, never decides; no sizing / pricing / approval; deterministic; full provenance Artifact→Chunk→Page | rules-only extraction (`extraction_mode == rules_based_fallback`, else fail); every approved fact has a chunk ref; checklist and readiness called twice and byte-identical; S11 (WP5 models) `not_applicable` always; `src/munipal/engines` fenced | `tests/unit/test_lab_import_boundary.py::test_lab_never_calls_engines_llm_or_alembic`; S06/S08/S09 assertions in `labkit/bfms_driver.py`; goldens |
| 6 | BONDI relationship: consume, never fork; Arthur owns the port; nothing under the repo's `synth` source path | own emitter `labkit/events.py` in the emission format; `generate.py` never executed, imported or copied — its constants are ast-transcribed into `fixtures/bondi-reference/format.json` with a source sha256 (`fixtures/bondi-reference/PROVENANCE.md`) | `tests/unit/test_lab_bondi_format.py::test_lab_bondi_emission_format` (parity fence; skips with reason when the OneDrive file is absent); `test_lab_no_forbidden_sources` (the three `synth` import spellings) |
| 7 | Rescue-branch law: nothing from the quarantined synth branch, the OneDrive `synth/` or `emma/` folders enters the repo | only `fulfillment/demo` and `src/munipal` services are reused; the old-pack city names, the branch name, the OneDrive folder name and the rescued module names are fence tokens | `tests/unit/test_lab_forbidden_tokens.py::test_lab_no_forbidden_sources` (one allow-listed line: the F7 path in `governance/FINDINGS.md`) |
| 8 | Registry PIT law (`INDUSTRIALIZATION/experiments/PATTERN.md`): never append to `registry.jsonl`; DRAFT lines only; Stephen files | `governance/EXP-012.draft.jsonl`, `governance/DEC-010.draft.jsonl` with `ts == "<SET-AT-FILING>"` and a note containing DRAFT; no `registry.jsonl` under `lab/` | `tests/unit/test_lab_layout.py::test_lab_layout_gitignore_governance` |
| 9 | "twin-bfms" is a label, not a claim (DEC-009 section 9.8; `C:\Users\st3ja\muni-twin\CHARTER.md:12,363`) | notice in README / LAW / every report (`law.LABEL_NOTICE`); no sentence claims twin status for the artifact | `tests/unit/test_lab_forbidden_tokens.py::test_lab_label_not_claim_and_citation_control` |
| 10 | Fictional names collision-checked against real firms (brief rule 10 list at minimum) | name table `scenarios/names/fictional-names.v1.json` + whole-phrase, case-insensitive blocklist `scenarios/names/blocklist.v1.txt`, checked at load (`labkit/names.py`) and by fence; every entry carries `web_collision_check: "not performed"` | `tests/unit/test_lab_names.py::test_lab_blocklist_complete_and_names_clean` |
| 11 | Stage law (`INDUSTRIALIZATION/STAGE-DIAGNOSIS.md` section 1; `ENGINEERING-DOCTRINE.md` section 5d): non-trivial builds need a PRFAQ-lite naming line, ACQ stage and constraint; work off the named constraint needs a logged override | `governance/PRFAQ-lite.md` (Municipal bonds, ACQ stage 2 Advertise, DEMAND ratified; OUT-002 operator-throughput finding un-ratified); `governance/DEC-010.draft.jsonl` = the override request; build step 0 gated on the ruling; `lab/README.md` states the P1 stopping point | `tests/unit/test_lab_layout.py::test_lab_layout_gitignore_governance` (PRFAQ names line, stage, constraint, OUT-002) |
| 12 | Citation control: never write that a person approved; cite a path | every decision cites `LAB-BRIEF.md` or the reset plan path (`law.ACCEPTED_CITATIONS`); the forbidden phrase is a fence token | `tests/unit/test_lab_forbidden_tokens.py::test_lab_label_not_claim_and_citation_control` |

## Structural fences (not tied to one rule)

| structure | file | asserts |
|---|---|---|
| import boundary | `tests/unit/test_lab_import_boundary.py::test_lab_not_importable_from_src` | `src/munipal/**` never names `labkit`, `twin-bfms`, `twin_bfms`, `lab/`; importing `munipal.main` / `munipal.sensing_app` leaves no `labkit` in `sys.modules` |
| not mounted, not deployed | `::test_lab_not_mounted_or_deployed` | no route path contains `lab` or `twin`; `railway.toml`, `frontend/vercel.json`, `frontend/vite.config*.ts`, `.github/workflows/*` never name `lab/` or `twin-bfms`; `contracts/openapi.v1.json` unchanged by importing labkit |
| scenario shape | `tests/unit/test_lab_scenario.py` | deal-v0 required keys; `^SYN-`; base core == demo core; variants flip exactly one knob |
| pack determinism | `tests/unit/test_lab_pack.py` | two generations byte-identical; committed == regenerated; manifest complete; extractor readability; playbook request match; demo-constant reuse; `_pins.json` current |
| post-close equivalence | `tests/unit/test_lab_post_close.py` | `fulfillment/` tree hash unchanged; LAB01 == demo build row-for-row after scrub; LAB02 deltas exact; four statuses only; `render_html` / `main` never called |
| report seal | `tests/unit/test_lab_report.py` | build → write → verify; flipping one status breaks verify; md re-derivable from json |
| layout | `tests/unit/test_lab_layout.py` | `.gitignore` has `runs/` and `**/_storage/`; `git check-ignore` (read-only) says `runs/x` ignored and `packs/ expected/ scenarios/` tracked-eligible; `docs/CONSUMER-PULLS.md` has four rows |
| e2e | `tests/integration/test_lab_e2e_housing.py` | S00–S18 for LAB01/02/03 against goldens; `extraction_mode == rules_based_fallback`; `_corpus_available` False; < 45 s per scenario |

## Retention rule for `runs/`

- `runs/` is local disk only. Never under OneDrive or any synced folder (a synced `runs/` would carry synthetic packets off the build machine — TR-1).
- `runs/` is gitignored by `lab/twin-bfms/.gitignore` (`runs/*`, `!runs/.gitkeep`, `**/_storage/`, `**/_documents/`, `**/empty-root/`). The shared root `.gitignore` is never edited.
- A run directory is kept only until its golden is frozen and reviewed (`expected/<deal_id>/run-report.expected.json`), then deleted. Goldens carry statuses and counts only, never BFMS prose.
- No run output is ever attached to Vercel, Railway, Notion, email, Telegram or Linear.
- Runtime under pytest uses `tmp_path`; nothing is written under `runs/` by the suite.

## Two pre-existing red tests (not lab law, but lab conduct)

`tests/contract/test_openapi_contract.py::test_openapi_contract_snapshot_is_current` and
`tests/unit/test_sensing_pilot_funnel_contract.py::test_sensing_deployment_scope_blocks_bfms_admin_routes`
were red on master before the lab existed (520 passed / 2 failed, WSL-native, 2026-09-10). The lab never fixes them silently
(finding F2, `governance/FINDINGS.md`). New lab tests add no red.
