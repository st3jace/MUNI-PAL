# MUNI-PAL / BFMS — Agent Guide

Bond Facility Management System: evidence-first, advisor-grade platform for municipal bond structuring.

## Canonical location (read first)
- **This WSL checkout is canonical:** `/home/st3ja/Developer/MUNI-PAL`. Do active work here.
- The OneDrive copy (`…/PROJECTS/INNOVATION FACTORY/MUNI-PAL`) is **stale** — never treat it as source of truth (it was moved out of OneDrive to escape sync corruption).
- `V1/` and `V2/` are retained for lineage only. **Do not add new production code, tests, migrations, or frontend work there.** Active app code lives in `src/`, `frontend/`, `tests/`, `contracts/`, `alembic/`.

## Stack
- **Backend:** FastAPI + SQLAlchemy 2 (async) + Pydantic Settings v2. Package `munipal`, entry point `munipal.main:app`, source under `src/munipal/` (plus `src/synth/` for the synthetic-data pipeline). Built with hatchling; deps managed via `uv` + `uv.lock`.
- **Frontend:** React + Vite + Tailwind in `frontend/` (no root `package.json` — run npm from `frontend/`).
- **Database:** PostgreSQL (localhost:5432, user/db `munipal`). **PostgreSQL is canonical — `USE_SQLITE=false`.** `munipal_dev.db` SQLite is opt-in scratch only; the live dev projects are in Postgres.
- **Async:** Celery + Redis for extraction / deliverables.
- **Ports:** backend 4120, frontend 4121 (managed by the Visibility Dashboard).

## Verification commands (canonical — do not rename)
Full list: `docs/development/VERIFICATION_COMMANDS.md`. Use `uv`, **not** bare `python`/`pytest`.
- Backend tests: `/home/st3ja/.local/bin/uv run --extra dev pytest tests -q`
- Backend lint: `/home/st3ja/.local/bin/uv run --extra dev ruff check src tests scripts`
- Backend types: `/home/st3ja/.local/bin/uv run --extra dev mypy src`
- Contract tests: `/home/st3ja/.local/bin/uv run --extra dev pytest tests/contract -q`
- Frontend (from `frontend/`): `npm run test` / `npm run lint` / `npm run build`
- After OpenAPI changes (`contracts/openapi.v1.json`): `cd frontend && npm run generate:api-types`, then review the diff.

Before implementation work: `python scripts/check_dev_environment.py`. See `docs/development/CANONICAL_DEV_PATH.md`.

## Known landmines
- **Schema namespace drift (active critical defect):** two namespaces coexist — `project.*` vs `healthcare.*`. This is the root cause of Readiness ↔ Checklist propagation breaks. When touching cross-section data flow, check which namespace each side uses *before* changing logic; don't add a third path. This is the canonical "fix once, encode so it can't recur" candidate for `/ce-compound`.
- **`.env` drift:** the `.env` has historically drifted to production values, silently breaking local dev (empty DB, CORS blocking all requests, 401s). For Visibility-Dashboard-managed launches, `VISIBILITY-DASHBOARD/backend/services/portMap.js` injects spawn-time env overrides (`USE_SQLITE=false`, `DEBUG=true`, `APP_ENV=development`, `AUTH_ENFORCEMENT_V2=false`, `ROLE_ENFORCEMENT_V2=false`, `TENANT_ISOLATION_V2=false`) that win over `.env`. If launching manually, set these yourself.
- **Alembic on boot is slow (~60s):** migrations run on every backend start even when none are pending. Expect the delay; don't assume the server hung.

## Working conventions
- **Dogfood-first for cross-section / wiring bugs:** drive BFMS in a browser and reproduce before doing static analysis. Behavior in the running app is the source of truth for propagation/wiring issues.
- **Test-first for behavior changes:** write/update the smallest failing test, implement only the scoped change, run the relevant canonical commands, then commit.
- **Linear (ELA team) cadence:** move issue → In Progress; implement scoped change; verify; commit with issue-scoped message; comment in Linear with files changed + verification output + commit hash; move → Done.
- **Anthropic SDK code:** default to the latest Claude models; consult the `claude-api` skill for current model IDs/pricing rather than hardcoding from memory.

## First files when troubleshooting
1. `src/munipal/config.py` — Pydantic Settings, computed `database_url`, `_NonEmptyEnvSource` (treats empty env strings as unset).
2. `src/munipal/main.py` — CORS setup, router registration.
3. `VISIBILITY-DASHBOARD/backend/services/portMap.js` — spawn-time env overrides.
4. `.env` (if present) — `USE_SQLITE`, `APP_ENV`, `DEBUG`, the `*_V2` auth/role/tenant flags.
