# WALKTHROUGH — build packs, run LAB01, read the report, run the suite

Operator copy. Every command runs WSL-native from the repo root. Never anaconda. Never Windows python against the UNC path.
twin-bfms is a label, not a claim (DEC-009 section 9.8).

## 0. Preconditions

- Repo: WSL `~/Developer/MUNI-PAL` (UNC `\\wsl.localhost\Ubuntu\home\st3ja\Developer\MUNI-PAL`), branch `master`.
- Python: `.venv/bin/python` (3.11). `PYTHONPATH=src` for anything that imports `munipal`.
- No `ANTHROPIC_API_KEY` in the environment (the harness pins it to `""` anyway; extraction must run `rules_based_fallback`).
- `lab/twin-bfms/runs/` lives on local disk only (`lab/twin-bfms/LAW.md`, retention rule).

Check the baseline first (read-only):

```
wsl.exe -d Ubuntu -e bash -lc 'cd ~/Developer/MUNI-PAL && git rev-parse HEAD && git status --porcelain | head'
```

## 1. Build (or re-verify) the packs

The packs are committed. Regenerating them is deterministic; the generator refuses to write if the offline extractor self-check fails
(`lab/twin-bfms/labkit/generate_pack.py`, `readability_check`).

```
wsl.exe -d Ubuntu -e bash -lc 'cd ~/Developer/MUNI-PAL && PYTHONPATH=src .venv/bin/python lab/twin-bfms/labkit/generate_pack.py --help'
```

Regenerate into a temporary directory and compare against the committed pack (the fence does the same in
`tests/unit/test_lab_pack.py::test_lab_pack_determinism_and_manifest`):

```
wsl.exe -d Ubuntu -e bash -lc 'cd ~/Developer/MUNI-PAL && PYTHONPATH=src .venv/bin/python lab/twin-bfms/labkit/generate_pack.py --scenario lab/twin-bfms/scenarios/SYN-HSG-AZ-2025-LAB01.synthetic.json --out /tmp/lab01 && diff -r /tmp/lab01/SYN-HSG-AZ-2025-LAB01 lab/twin-bfms/packs/SYN-HSG-AZ-2025-LAB01 && echo IDENTICAL'
```

If `diff` reports a change, something upstream moved: check `lab/twin-bfms/packs/_pins.json` against the current sha256 of
`fulfillment/demo/run.py` and `fulfillment/demo/build_fixtures.py`. A demo edit must be followed by a deliberate pack regeneration
and a golden re-review — never by editing a pack file by hand.

What a pack holds (`lab/twin-bfms/packs/<deal_id>/`):

- `PACK-MANIFEST.json` — every file with sha256, `created_from`, and `absent_by_scenario` entries.
- `intake/<NN_FOLDER>/<artifact_key>.txt` — one file per housing required artifact, `Label: value` lines the rules extractor reads.
- `closing-documents/NN-*.md` — the demo's six excerpts re-emitted with the envelope and the legend.
- `post-close/approved-inputs.csv` (+ sidecar), `approval-2026-09-08.md`, `vault/*.txt` — the register inputs.
- `bondi/deal.json`, `event_log.csv` (+ sidecar), `constraint_report.json`, `artifact_manifest.json` — the BONDI-format emission.

## 2. Run LAB01

```
wsl.exe -d Ubuntu -e bash -lc 'cd ~/Developer/MUNI-PAL && PYTHONPATH=src .venv/bin/python lab/twin-bfms/run_lab.py --scenario lab/twin-bfms/scenarios/SYN-HSG-AZ-2025-LAB01.synthetic.json'
```

- `--asof` is not accepted; `asof` is `lab.asof` in the scenario (2026-09-10 for all three).
- Exit 0 iff the report verifies and no fence-class violation occurred. Any other exit code: read the last stage row in the report.
- Output: `lab/twin-bfms/runs/<run_id>/` — `run-report.json`, `run-report.md`, `register-root/`, `_storage/`, `empty-root/`.

Run LAB02 and LAB03 the same way with their scenario files.

## 3. Read the report

Open `runs/<run_id>/run-report.md` (rendered from the json; the json is the sealed record). Check, in order:

1. The legend is the first and the last line; `label_notice` is present.
2. `pins` equal `lab/twin-bfms/packs/_pins.json`; `repo_commit` is the HEAD you noted in step 0; `repo_dirty` is what `git status` said.
3. `environment.extraction_mode == rules_based_fallback`; `environment.sensing_corpus_available == {healthcare: false, waste: false}`; `anthropic_key_present == false`.
4. `pilot_gates`: `registered_ma_confirmed` and `engagement_scope_signed` are `not_applicable` with reason `internal lab; no client`; `pilot_smoke_test_green` is pass or fail; `known_gaps_accepted` lists `S05.artifact_dedup (F9)`, `S05.artifact_level_sha256 (F9)` and `S12.sector_liability_disclaimers_present (F16)`.
5. Stage table: S11 and S17 are `not_applicable` by law; S05 is `fail` by F9 and S12 is `fail` by F16; everything else should match `expected/<deal_id>/run-report.expected.json`. `docs/STAGE-MAP.md` explains each row.
6. Deal trace (six stations): for each `event_log.csv` row, the BFMS object touched, the evidence document or register row, and "not carried by scenario". Rows marked `not_applicable` are what the six stations carry that BFMS cannot represent.
7. `register_summary` (LAB01): 17 obligations; filed 6 / not filed 1 / evidence missing 2 / not testable 8; gaps 2; open items 3; `base_equivalence: pass`. LAB02: filed 3 / evidence missing 5; gaps 5.
8. `bfms_emitted_language`: BFMS prose as sha256 + excerpt. Nothing there is a lab statement.
9. `golden_diff` is empty; `content_hash` is present.

A non-empty `golden_diff` is not a lab bug by itself. It means BFMS behaviour moved. Review the delta with COS; if the new behaviour is correct,
regenerate the golden from the run (never type it) and re-review; if not, it is a new finding for `governance/FINDINGS.md`.

## 4. Run the suite

Fast loop (static fences, packs, report seal; no ASGI drive):

```
wsl.exe -d Ubuntu -e bash -lc 'cd ~/Developer/MUNI-PAL && .venv/bin/python -m pytest -q -p no:cacheprovider tests -k "lab and not e2e"'
```

Full suite (the acceptance bar):

```
wsl.exe -d Ubuntu -e bash -lc 'cd ~/Developer/MUNI-PAL && .venv/bin/python -m pytest -q -p no:cacheprovider tests'
```

Expected: 520 pre-existing passes + 43 lab tests passed (563 total); exactly 2 failed, both pre-existing on master
(`tests/contract/test_openapi_contract.py::test_openapi_contract_snapshot_is_current`,
`tests/unit/test_sensing_pilot_funnel_contract.py::test_sensing_deployment_scope_blocks_bfms_admin_routes`).
Any other red is a lab defect or a new finding. Do not fix the two pre-existing failures from the lab (finding F2).

Lint:

```
wsl.exe -d Ubuntu -e bash -lc 'cd ~/Developer/MUNI-PAL && /home/st3ja/.local/bin/uv run --extra dev ruff check tests lab'
```

## 5. After the run

- Delete `lab/twin-bfms/runs/<run_id>/` once its golden is frozen and reviewed (retention rule).
- Never copy a run directory to OneDrive, a chat, an email, Notion, Linear or a deploy target (TR-1).
- Record any new observation as a finding in `governance/FINDINGS.md` with a path; never patch `src/` from the lab.

SYNTHETIC RESEARCH ARTIFACT — MUNI-TWIN — NOT LEGAL ADVICE — NOT PREPARED BY AN ATTORNEY — NOT AN OFFER OF SECURITIES. Fictional names collision-checked against real firms.
