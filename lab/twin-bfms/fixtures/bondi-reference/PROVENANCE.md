---
source: synthetic
generator_version: lab-gen-0.1.0
lab_version: 0.1.0
scenario_id: SYN-BONDI-FORMAT-REF
seed: 0
sha256_body: 0fc72a2dacb05d2aaf47ddb480349b69c254517badadf7094a8822a1442f2720
created_from:
  - "labkit/generate_pack.py::write_bondi_reference"
---

> SYNTHETIC RESEARCH ARTIFACT — MUNI-TWIN — NOT LEGAL ADVICE — NOT PREPARED BY AN ATTORNEY — NOT AN OFFER OF SECURITIES. Fictional names collision-checked against real firms.

# BONDI emission-format reference (transcription, not a run)

twin-bfms is a label, not a claim (DEC-009 section 9.8).

## What this folder holds

`format.json` transcribes the EMISSION FORMAT of the BONDI synthetic-issuance runner:
the `event_log.csv` header, the six station names, the event names per sale-method pole
with their actor roles, and the status vocabulary. Nothing else.

## Source

- path (Windows): `C:\Users\st3ja\OneDrive\Documents\MEGA\PROJECTS\INNOVATION FACTORY\APPLIED RESEARCH\bondi-bfms\synth-issuance\generate.py`
- path (WSL): `/mnt/c/Users/st3ja/OneDrive/Documents/MEGA/PROJECTS/INNOVATION FACTORY/APPLIED RESEARCH/bondi-bfms/synth-issuance/generate.py`
- sha256 of generate.py at transcription: `5cdc6f04e124c45c1de59ef9e03d558bcfa0434fed58cdbde52d45d3fe0e555c`
- transcribed on: 2026-09-10 (a provenance record; not a scenario date)
- method: `labkit/generate_pack.py::transcribe_bondi_format` -- `ast.literal_eval` of the
  module-level constants `STATION_EVENTS_CORE`, `STATION_EVENTS_BY_POLE`, `STATION_EVENTS_POST`,
  `SALE_POLES` and the `DictWriter` field names. generate.py was NEVER executed, imported,
  copied or vendored (COS working paper 2026-09-10, section 3.3: consume the format, never fork).

## What is deliberately NOT transcribed

- the pre-close date offsets ("SCENARIO DRESSING") and the Form 8038 due-date helper: the lab never
  computes a date; every date in a lab event log is a scenario literal (brief rule 4).
- BONDI's scenario files and outputs (one calibration scenario carries real names).

## How the fence uses it

`tests/unit/test_lab_bondi_format.py::test_lab_bondi_emission_format` checks every
`packs/*/bondi/event_log.csv` against `format.json`; when the OneDrive file is present it
also ast-parses the same constants from `generate.py` and compares them with `format.json`
(drift alarm, pin key `bondi_format_json_sha256`); when absent or dehydrated it skips that
half with a reason. It never runs generate.py.

## Ownership

BONDI owns the engine contract; Arthur owns the eventual port into `MUNI-PAL/synth/`.
The lab depends on the emission format only and emits its own log with
`lab/twin-bfms/labkit/events.py`.

SYNTHETIC RESEARCH ARTIFACT — MUNI-TWIN — NOT LEGAL ADVICE — NOT PREPARED BY AN ATTORNEY — NOT AN OFFER OF SECURITIES. Fictional names collision-checked against real firms.
