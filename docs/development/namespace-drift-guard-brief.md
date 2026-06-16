# /ce-plan brief — Readiness↔schema path-drift regression guard

> Paste this whole file (or its path) to `/ce-plan` from the canonical WSL repo
> (`/home/st3ja/Developer/MUNI-PAL`). Verified against code on 2026-06-16.

## Problem
BFMS readiness scoring references schema paths via `contributing_paths` and
`critical_paths` inside each playbook's `readiness_config.dimensions`. Those
references can silently drift from the playbook's actual `schema_paths`
definitions. When a referenced path has no `schema_paths` entry, it has no
metadata/criticality and readiness scoring degrades or mis-scores it — the
structural family behind the historical "Readiness updates but Checklist
doesn't" complaints.

The original healthcare instance (`project.service_area` vs
`healthcare.service_area`) was fixed on 2026-04-26, and `SCHEMA_PATH_ALIASES`
was since removed. **But the recommended regression guard was never added, and
at least one live drift instance remains.**

## Verified current state (file:line evidence)
- `src/munipal/services/playbook_data.py:594` `SCHEMA_PATHS = [...]`;
  `:702` `HEALTHCARE_SCHEMA_PATHS`; `:721-722` merge into `SCHEMA_PATHS`.
- `:1379, :1395, :1415, :1432, :1455` `contributing_paths` blocks;
  `:1390, :1410, :1427, :1450, :1477` `critical_paths`.
- **Live drift:** `project.technology` is referenced in a `contributing_paths`
  block (~`:1612`) but has **0** matching `{"path": "project.technology"}`
  entry in `SCHEMA_PATHS`. Confirmed: `project.canonicaldescription`,
  `project.operatingstatus`, `project.location`, `project.designlife` each have
  exactly 1 definition (legit); `project.technology` has none (dangling).
- No existing test asserts `contributing_paths ∪ critical_paths ⊆ schema_paths`.
  `tests/unit/test_readiness_golden_fixtures.py` is snapshot-based;
  `tests/integration/test_playbooks_api.py:68,120,123` only check the key
  exists and criticality filtering — not the subset invariant.

## Goal (the compounding fix)
Add a contract/unit test that, **for every playbook**, asserts every
`readiness_config.dimensions[].contributing_paths` and `[].critical_paths`
entry resolves to a real entry in that playbook's `schema_paths` (apply any
alias resolution that still exists; there should be none now). Make it a
build-time failure so this class of drift can never reach users again.

Then fix whatever the new test surfaces — starting with `project.technology`:
either add its `schema_paths` definition (with correct `criticality`) or
correct the reference to the intended canonical path. Decide which by checking
what fact that dimension is actually meant to score.

## Scope boundaries
- IN: the new test; fixing paths it flags as dangling; a one-line note in
  `docs/development/` if a canonical-path convention is decided.
- OUT: reworking readiness scoring logic; UX/frontend changes; reintroducing an
  alias layer. Do **not** add a third code path to "patch" drift — unify at the
  data definition.

## Acceptance criteria
1. New test fails on `main` as-is (proves it catches `project.technology`).
2. After the fix, the new test passes and the full backend suite is green:
   `/home/st3ja/.local/bin/uv run --extra dev pytest tests -q`
3. Lint/type clean: `ruff check src tests scripts`, `mypy src`.
4. No new `project.*`-vs-canonical divergence introduced.

## After /ce-work: compound it
Run `/ce-compound` to write a `docs/solutions/` entry: symptom
("readiness path with no schema metadata / cross-section mismatch"), root cause
(readiness config referencing undefined schema paths), the guard test as the
permanent fix, and a pointer to this brief. This closes the loop so the next
agent finds the solution before re-debugging it.
