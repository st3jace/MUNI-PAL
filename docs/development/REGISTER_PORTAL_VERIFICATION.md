# Register portal verification — 2026-09-17

Base: `a1fda08b8ee024de3a7c21ebe650f265357d9397` (`feature/durable-ask-chat`).
Implementation: `feature/obligation-register-portal`.

## Results

- New backend tests: **25 passed** across the focused runs (deal access/payment/delivery,
  document extraction, migration/reconnection persistence and full SQL export).
- Focused portal + Ask/auth/authorization/billing/contract/intake runs:
  **87 passed + 89 passed**. The enhanced report-byte persistence test also passed.
- New frontend tests: **7 passed**. Portal plus Ask/navigation focused run: **16 passed**.
- Full backend with repository-pinned dependencies: **686 passed, 7 failed**.
  Failures are the same synthetic lab/hash-pin categories reported on the base:
  three housing end-to-end scenarios, Bondi format equivalence, pack determinism,
  rules-extractor intake and demo-constant hash pin. No files responsible for those
  fixtures/runners were modified in this feature.
- Full frontend: **30 passed, 5 failed**. Existing failures are in the unrelated
  Pilot Navigation and tools/market-intelligence tests; the seven new tests pass.
- React portal build, standalone healthcare build and TypeScript checking passed.
- Focused Ruff and ESLint/React Hooks checks passed.
- OpenAPI snapshot and both generated frontend artifacts were regenerated.
- Alembic reports one head: `e5f6g7h8i9j0`. PostgreSQL migration SQL generation passed.
  Full PostgreSQL bootstrap export also passed after replacing the historical lead
  unsubscribe-token backfill's client-side row fetch with `gen_random_uuid()` on
  PostgreSQL. Both migration tests passed after that targeted change. The full-suite
  count above precedes the addition of this SQL-export regression test.
  New migration upgrade/downgrade and persistence across connections passed in an
  isolated file-backed SQLite database. A hosted PostgreSQL migration remains a
  deployment step; local Docker was unavailable.
- Browser QA against the running local backend: sign-in/return route, deal library,
  paid deal/source list, versioned generation and reload persistence verified.
  A 390px viewport reported no horizontal document overflow. Preview fixtures are
  explicitly labeled synthetic and confined to a local scratch database.

## Meaningful cases covered

Strict access JWTs; refresh/dev-header rejection; inactive accounts; closed/private
borrower and consent gates; cross-owner and moved-tenant denial; server-only quotes;
server-controlled prices; immutable quote during checkout; duplicate checkout reuse;
incorrect session/amount/currency/mode/metadata rejection; unpaid Checkout rejection;
per-deal entitlement (no subscription upgrade); signed webhook dispatch; full refunds
before and after completion; duplicate/out-of-order revocation; cloud-link validation;
manual-import gate; operator-only publication; old report versions retained; private
download authorization; exact source excerpts; no inferred dates/statuses; formula-safe
CSV; DOCX tables; blank/scanned PDF rejection; persisted report bytes after reconnect.

No live Stripe charge, client email, production backend/frontend deployment or
production database migration was part of local verification.

## Reproduction

### Hosted fresh-database verification (September 17, 2026)

Initialized the new Launch Shop / Muni-Pal Supabase project from an empty public
schema. The hosted database reports migration head `e5f6g7h8i9j0`, 40 public tables,
five Register tables with RLS enabled, 13 Register indexes, one seeded playbook,
and zero client accounts. No existing production records were moved.

This exposed and fixed offline PostgreSQL JSON literal escaping in `alembic/env.py`:
the offline dialect must match PostgreSQL's default `standard_conforming_strings=on`.
The first attempts rolled back cleanly; the corrected full migration committed and
the counts above were read back from Supabase. Both migration regression tests pass.
This verifies hosted schema creation, not backend connectivity or live payments.

The separate `docker/Dockerfile.portal` packages the locked dependencies and migrations
for the private backend. Local Docker is unavailable; its image still needs a hosted
build and smoke test before release.

On Windows, create a Python 3.12 environment and install **the dependencies in
`uv.lock`**, then the local package. Use the repository commands with isolated mode:

```powershell
uv run --no-sync --python .venv/Scripts/python.exe python -I -m pytest tests -q --basetemp=../pytest-register-full-locked
uv run --no-sync --python .venv/Scripts/python.exe python -I -m alembic heads
# Set USE_SQLITE=false to emit PostgreSQL SQL without contacting a database:
uv run --no-sync --python .venv/Scripts/python.exe python -I -m alembic upgrade d4e5f6g7h8i0:head --sql
```

From `frontend/`:

```powershell
npm install
npm run test
npm run build
npm run build:healthcare
npm run generate:api-types
npm run generate:api-client
```

Environment notes: the canonical path checker passes repository/scoped-file checks
but reports the existing WSL-path mismatch in this Windows checkout. Initial `uv`
installation hit a Windows PE-resource error; dependencies were installed with pip
from `uv export --frozen` while execution continued through `uv run --no-sync`.
An initial broad run used the default temporary directory, which was inaccessible;
the recorded full result uses a workspace-owned `--basetemp`. The repository has no
ESLint configuration, so focused lint used its installed TypeScript parser and
React Hooks rules explicitly. These local setup workarounds do not alter production
dependencies or the lockfile.
