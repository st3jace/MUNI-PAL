# Ask release verification — 2026-09-17

No commit, push, deployment, real recipient, or external provider call was performed. All new API fixtures are synthetic and run against isolated test databases. No live application migration was applied.

## Test-first slices

Each implementation slice was preceded by an observed failing run:

| Slice | Observed RED | GREEN after implementation |
| --- | --- | --- |
| Strict paid identity | Ask scope returned 404 instead of 401 | 1 API test |
| Scoped conversations | Missing scope/conversation endpoints; 5 failures | 7 API tests |
| Evidence, refusal and durable ordering | Service import missing; then 7 endpoint failures | 34 service/API tests |
| React chat | Missing Ask module | 5 UI tests |
| Website navigation | Missing AskNavigation module | 2 navigation tests |
| Migration/reconnection | Six UUID column type mismatches | Migration test passed |
| Private errors | Missing no-store header on 403 | 20 API/migration tests |
| Revoked UI scope | Old evidence remained visible after 404 | 9 UI/navigation tests |
| Broader judgment refusal | 6 deadline/judgment phrasing failures | 25 service tests |
| Parent deletion | FK failure deleting a project with chat | Migration/cascade/restart test passed |

The final targeted command also checks existing authentication, project/object authorization, and OpenAPI contracts:

```powershell
# Repository root
$env:UV_CACHE_DIR="$PWD/.uv-cache"
uv run --no-sync --python .venv/Scripts/python.exe python -I -m pytest tests/unit/test_ask_service.py tests/integration/test_ask_api.py tests/integration/test_ask_migration.py tests/integration/test_auth_api.py tests/unit/test_auth_dependencies.py tests/integration/test_project_authorization.py tests/integration/test_object_authorization.py tests/contract -q --basetemp=reports/ask-pytest-temp
```

Final result after fail-closed reviewer-directed fixes: **136 passed**. Coverage includes 401/free/per-project/deactivated checks, refresh-token and compatibility-header rejection, forged project/document IDs, same-tenant and superuser IDOR attempts, source poisoning, exact excerpts, no hits, refusal before candidate generation, conclusion-seeking interrogative and declarative-request grammar, broad legal/default/compliance/violation/breach/permissibility/authorization/municipal-advisor judgment phrasing (including hyphenated forms), tightly anchored non-judgment record lookups using those same terms, appended-text bypass attempts, persisted ordering through a fresh session, migration metadata parity, cascade deletion, request/result/conversation limits, lost entitlement, and sanitized errors. Independent review retained subscription-only access because the current schema cannot safely map a `per_project` purchase to one authorized project, and it removed the legacy Anthropic advisor widget from `/ask` and `/ask/`.

```powershell
# Repository root
uv run --no-sync --python .venv/Scripts/python.exe python -I scripts/generate_openapi_snapshot.py
uv run --no-sync --python .venv/Scripts/python.exe python -I scripts/verify_openapi_generated_artifacts.py --fail-on-mismatch
uv run --no-sync --python .venv/Scripts/python.exe python -I -m alembic heads
$env:USE_SQLITE='false'
uv run --no-sync --python .venv/Scripts/python.exe python -I -m alembic upgrade c3d4e5f6g7h9:head --sql
```

Results: snapshot generated; generated artifact verification **pass**; one head `d4e5f6g7h8i0`; PostgreSQL offline migration SQL generated successfully. Runtime PostgreSQL migration was not exercised. The migration test executes upgrade/downgrade with foreign keys enabled on isolated SQLite, checks schema parity, and reconnects after engine disposal.

```powershell
# frontend/
npm run generate:api-types
npm run generate:api-client
node scripts/verify-ask.mjs
npx tsc -b
node scripts/verify-ask.mjs --build
node --input-type=module -e "import { build } from 'vite'; import config from './vite.config.healthcare.ts'; await build({ ...config({mode: 'production',command: 'build'}), configFile: false });"
npx eslint --no-eslintrc -c .eslintrc.ask.cjs src/pages/Ask.tsx src/services/askApi.ts src/pages/__tests__/Ask.test.tsx src/components/AskNavigation.tsx src/components/Layout.tsx src/components/__tests__/AskNavigation.test.tsx src/components/__tests__/Layout.test.tsx scripts/verify-ask.mjs
```

Results: both generators passed; **12 frontend tests passed**; TypeScript passed; portal and healthcare production builds passed with existing large-chunk warnings; focused ESLint passed. The verification helper loads the same Vite configuration through the programmatic API, avoiding only the sandbox-blocked config bundling step. The standalone healthcare command uses this shell's Node 22 native TypeScript loading. Generated clients also incorporate pre-existing snapshot/client drift for ObligationRegister and a HealthService docstring; no corresponding application behavior was changed.

## Separate baseline/environment blockers

- `uv run --no-sync --python .venv/Scripts/python.exe python -I scripts/check_dev_environment.py`: filesystem/git checks pass; WSL canonical-path check fails, waived by the explicit task instruction.
- The initial `uv` attempt could not write its default cache. Setting `UV_CACHE_DIR` inside this repository resolves it.
- The parent run's Hermes/Pydantic import failure is avoided by the project venv plus `python -I`. The focused 136-test Ask/auth/authorization/contract suite passes. The repository-wide baseline is recorded separately below rather than represented as clean.
- `npm run test -- src/pages/__tests__/Ask.test.tsx` and `npm run build` hit esbuild's `Cannot read directory "../..": Access is denied` during config bundling. The programmatic invocations above pass in the same checkout.
- `npm run lint` fails because the repository has no default ESLint configuration. The new narrowly scoped `.eslintrc.ask.cjs` verifies Ask without changing the global lint baseline.
- `node scripts/verify-ask.mjs --all`: **5 failed, 23 passed**, in unchanged `Readiness` (2), `AdvisoryPackages` (2), and `PilotNavigation` (1) tests. The three new Layout regression tests account for the increase from the earlier 20 passing tests. Assertions and unrelated application behavior were left unchanged.
- Repository-wide Ruff's previously reported **504 errors** were not repaired or represented as clean. New Ask Python files and migration receive a separate focused check.
- The final full backend suite was rerun with its temporary directory outside the repository tree: **662 passed, 7 failed**. The seven failures are confined to unchanged lab fixtures and pins: three synthetic housing golden comparisons, the Bondi format hash pin, committed-pack determinism, an intake-manifest hash, and the `fulfillment/demo/run.py` hash pin. They report CRLF/hash drift in files this branch does not modify; no Ask/auth/project/contract test failed.

## Final review

Reviewed all Ask routes for mandatory paid identity, refresh/development bypasses, owner/tenant filtering before retrieval, resource enumeration, source handling, error/log content, persistence and migration registration. Rechecked entitlement before every endpoint, including history, delete and source resolution. Tests cover revocation and inaccessible saved evidence. No LLM/provider secret was added. Questions and source text stay in the owned database records and React text nodes; they are not application log messages or executable markup.

```powershell
# Repository root; scans only the new Python implementation, tests and migration.
uv run --no-sync --python .venv/Scripts/python.exe python -I -m ruff check src/munipal/api/routes/ask.py src/munipal/api/dependencies.py src/munipal/core/models/ask.py src/munipal/core/schemas/ask.py src/munipal/services/ask_service.py tests/unit/test_ask_service.py tests/integration/test_ask_api.py tests/integration/test_ask_migration.py alembic/versions/20260917_0001_d4e5f6g7h8i0_add_ask_history.py
uv run --no-sync --python .venv/Scripts/python.exe python -I reports/ask_scan_changed.py
git -c core.safecrlf=false diff --check
```

Results: focused Ruff **all checks passed**; credential scan **zero findings**; diff whitespace check passed. The local scan script and JSON output are retained under the ignored `reports/` directory. It scans modified/untracked files from `git diff --name-only` and `git ls-files --others --exclude-standard`, checking private keys, AWS/provider/GitHub credentials, literal JWTs and long credential assignments. It reports file/line/rule only, never matched values. This is a pattern check, not a claim that every possible secret format is detectable.

PostgreSQL-mode import check also passed: `munipal.main:app`, both Ask models, seven registered Ask operations, and PostgreSQL `CREATE TABLE` compilation. The targeted offline deployment-dialect check, `alembic upgrade c3d4e5f6g7h9:d4e5f6g7h8i0 --sql` with an explicit PostgreSQL URL, emitted both Ask tables successfully. A full-history offline run is not supported by an older data-dependent migration that executes a query during SQL generation; the online upgrade/downgrade/re-upgrade behavior is covered by the passing Ask migration integration tests. Healthcare build output was restored to its pre-task tracked contents after verification, and only newly generated build files were removed; no compiled distribution changes or unrelated TypeScript build metadata are part of this handoff.

Authenticated browser QA used an isolated SQLite database and synthetic project/document/chunk records. It verified login with production-safe auth flags, project/document scope controls, durable chat creation, an exact source excerpt and authenticated source view, the “Are we late?” judgment refusal, persistence after navigation/reload, and absence of the legacy Anthropic advisor widget on `/ask`. A reviewer-directed regression pass also verified the equivalent `/ask/` route with zero advisor controls. A first pass found the message autoscroll moving the outer page under the sticky header; the implementation now scrolls only the message log, and the recheck showed `window.scrollY == 0` with the full title and controls visible.
