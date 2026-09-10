# lab/ — internal R&D programs

`lab/` is the fourth top-level folder beside `gtm/`, `fulfillment/` and `ops/`
(the 2026-09-10 reset: `C:\Users\st3ja\braintrust\workspace\cos\2026-09-10-RESET-plain-plan.md`, "One repo").

## What it is

- Internal R&D only.
- Nothing for sale.
- Nothing public.
- Synthetic inputs only. Every generated file carries the synthetic legend on its face
  (`C:\Users\st3ja\muni-twin\QUARANTINE.md:66-67`).

## What it is not

- Never mounted by `src/munipal/main.py` or `src/munipal/sensing_app.py`.
- Never referenced by `frontend/vercel.json`, any `frontend/vite.config*.ts`, or `railway.toml`.
- Never imported from `src/`. The only bridge from the test suite is `tests/lab_support.py`.
- Never a client surface. There is no client. The pilot gate `registered_ma_confirmed` is reported
  `not_applicable (internal lab; no client)` by construction (`lab/twin-bfms/labkit/law.py`, `PILOT_GATE_STATUS`).

Fence tests under `tests/unit/test_lab_*.py` enforce each line above in the default suite.

## Programs

| folder | what | status |
|---|---|---|
| `lab/twin-bfms/` | drives the full BFMS (`src/munipal/main.py`, 17 routers) in-process on synthetic housing-conduit deals, pre-issuance through post-issuance, and seals a four-valued report | v0, build 2026-09-10 |

**twin-bfms is a label, not a claim (DEC-009 section 9.8)**; see `C:\Users\st3ja\muni-twin\CHARTER.md:12,363`.
No sentence in this folder claims twin status for any artifact.

## Authority for the build

Stephen's in-session instruction, 2026-09-10:

> "Let's proceed with an internal version that can generate synthetic data and test the entire bond finance process from pre to post"

and

> "keep going, build it once the workflow finishes"

That instruction authorises the build. The registry lines that record it
(`lab/twin-bfms/governance/EXP-012.draft.jsonl`, `lab/twin-bfms/governance/DEC-010.draft.jsonl`)
are DRAFTS until Stephen files them (`INDUSTRIALIZATION/experiments/PATTERN.md`, PIT law: agents never append to `registry.jsonl`).
The one-page ask is `lab/twin-bfms/governance/decision-request.md`.

Stage-law gate (`INDUSTRIALIZATION/ENGINEERING-DOCTRINE.md` section 5d): if the DEC-010 override is refused,
P1 (design + governance drafts) is the stopping point and nothing under `lab/` is kept.

Source brief: COS working paper `LAB-BRIEF.md` (2026-09-10, scratchpad; sha256 `f031201cc35a3651da7b45f67e485c0995ab9f04f066e6274d258ef9fa621cb4`), section 4 = the law the lab obeys.

## Run

WSL-native only. Never anaconda. Never Windows python against the UNC path.

```
wsl.exe -d Ubuntu -e bash -lc 'cd ~/Developer/MUNI-PAL && PYTHONPATH=src .venv/bin/python lab/twin-bfms/run_lab.py --scenario lab/twin-bfms/scenarios/SYN-HSG-AZ-2025-LAB01.synthetic.json'
```

Output lands in `lab/twin-bfms/runs/<run_id>/` (gitignored; local disk only; see `lab/twin-bfms/LAW.md`, retention rule).

## Acceptance bar

```
wsl.exe -d Ubuntu -e bash -lc 'cd ~/Developer/MUNI-PAL && .venv/bin/python -m pytest -q -p no:cacheprovider tests'
```

Green means: the 520 pre-existing passes plus the 43 lab tests pass, and the only red is the two
pre-existing failures on master (`tests/contract/test_openapi_contract.py::test_openapi_contract_snapshot_is_current`,
`tests/unit/test_sensing_pilot_funnel_contract.py::test_sensing_deployment_scope_blocks_bfms_admin_routes`).
The lab never fixes those two silently; they are findings F2 in `lab/twin-bfms/governance/FINDINGS.md`.

Fast loop: `-k "lab and not e2e"`.
