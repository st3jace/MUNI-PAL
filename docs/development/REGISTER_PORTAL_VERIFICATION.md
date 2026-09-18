# Register portal verification — 2026-09-17

Base: `a1fda08b8ee024de3a7c21ebe650f265357d9397` (`feature/durable-ask-chat`).
Implementation: `feature/obligation-register-portal`.

## Results

- New backend tests: **25 passed** across the focused runs (deal access/payment/delivery,
  document extraction, migration/reconnection persistence and full SQL export).
- Focused portal + Ask/auth/authorization/billing/contract/intake runs:
  **87 passed + 89 passed**. The enhanced report-byte persistence test also passed.
- New frontend tests: **8 passed**, including a regression proving private Register
  requests ignore the legacy public `VITE_API_URL`. The earlier portal plus
  Ask/navigation focused run passed 16 tests.
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
  isolated file-backed SQLite database. Hosted PostgreSQL and Railway image
  verification are recorded below; local Docker was unavailable.
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
Backend connectivity was subsequently verified below. Live payments remain untested.

The separate `docker/Dockerfile.portal` packages the locked dependencies and migrations
for the private backend. Its hosted build and smoke test subsequently passed below.

The application wheel built successfully and contains the portal routes and all four
Register skill-kit resources. Vercel produced a successful hosted frontend preview.
GitHub's first gate failed before frontend tests because `frontend/package-lock.json`
was ignored while the workflow required `npm ci`. The lockfile is now tracked; Vercel
also uses `npm ci`. CI now uses the tested Python 3.12/uv.lock environment and includes
the Register and Ask suites. Existing unrelated test failures are not suppressed.
The subsequent GitHub run `35272494896` passed the backend gate, generated-artifact
verification and test discovery, then reported the same frontend result: 30 passed,
five failures in AdvisoryPackages, Readiness and PilotNavigation. The Vercel build
for `6c5f91f` succeeded. The pull-request gate remains red for those existing failures.

### Hosted backend smoke test

Railway deployment `79d1c925-218d-4dce-a4a9-0cc8e1e5200d` became active at
`https://muni-pal-portal-production.up.railway.app`. The production image built;
startup migrations succeeded, `/health` returned healthy, and `/health/ready`
confirmed database connectivity. Redis is absent and causes the aggregate response
to say degraded; the Register workflow does not depend on Redis.

Seventeen hosted checks passed: account registration/login, profile persistence,
refresh-token rejection, deal creation/readback, document upload/download with exact
bytes and no-store headers, same-organization cross-owner denial, unpaid build denial,
and denial of client-issued quotes. Two synthetic QA accounts and a clearly labeled
synthetic deal/document were used; no customer files or payments were involved.
Both synthetic accounts were then deactivated in Supabase and read back as inactive.
Stripe test-mode verification was subsequently completed below; live payments remain disabled.

### Hosted frontend and proxy verification

Production Vercel deployment `BwPiELHZmdXq4wtfateDXyVA3VJa` built commit `586dd8d`
and was explicitly promoted to the public domains, clearing the temporary rollback.
The earlier `19d5533` frontend briefly reached production and was rolled back after
discovering that Register requests used the legacy sensing API environment value.
The corrected client uses relative URLs, like authentication, and a focused
regression test proves it ignores that legacy variable. All eight Register frontend
tests pass after this fix.

Nine public-domain checks passed at `https://muni-pal.io`: home, Register (both
trailing-slash forms) and authentication pages return HTML; Register account/deal
and authentication profile APIs return JSON 401 without credentials; invalid login
is rejected; an unsigned Stripe webhook returns 400. The browser displays the
Register sign-in/create-account entrance. These checks supplement the 17 hosted
backend checks; they do not establish paid checkout readiness.

The release remains on the feature branch and the PR is unmerged. Operator account
setup and Stripe test-mode verification were subsequently completed below.
Backups/retention and live-mode configuration remain launch gates. The existing unrelated full-suite
failures described above remain unresolved. Vercel warns that the existing Node 20
build runtime must be upgraded before September 30, 2026.

### Hosted Stripe sandbox verification

Launch Shop account `acct_19wrEUFDH0RHRrjH` is connected in **test mode**. The separate
destination `we_1UGokGFDH0RHRrjHlWK9ML3E` sends the four Register events to the Railway
portal webhook using API version `2026-08-26.dahlia`. Existing destinations were not
changed. The user entered the test API key and signing secret in Railway directly.

The first actual signed checkout event exposed `AttributeError: get`: Stripe 15
returns `StripeObject` instances, whereas the earlier mocked tests returned dicts.
Commit `137ca1f` converts the verified event recursively with `to_dict()` before
billing dispatch. Two new regression cases reproduce the original failure with real
HMAC signatures and the actual SDK, then pass with the fix. They also cover tampered
payload rejection, duplicate completion and refunds arriving before completion.
The combined Register/Stripe integration suite now passes **28 tests**. Focused lint
passes with existing B008/B904 baseline findings excluded; diff checks pass.
Railway deployed the fix as `7ea680fb-873b-43b3-a331-4804a94bdf2f`.

A $10 synthetic quote was seeded through database administration for deal
`707f3fc2-f836-4920-b417-1060c739dddc` (no professional engagement). The hosted test
used real client API authentication and Stripe Checkout; operator quote API behavior
is covered by automated tests, not by this database-seeded fixture.

Verified against the public portal and actual Stripe test events:

- Repeated checkout requests reuse the same session; another client cannot pay it.
- A declined test card leaves report generation locked.
- A successful test card creates payment `pi_3UGpIQFDH0RHRrjH0vRcIzXE`.
- Replaying the original failed event after deployment returns HTTP 200 and marks
  the deal paid, without another charge.
- The paid client builds and downloads a valid ZIP with eight package files;
  another client receives 404. The purchase does not grant a subscription.
- A $2 partial refund reaches the webhook with HTTP 200 and preserves access;
  a second report version builds and downloads successfully.
- Refunding the remaining $8 returns HTTP 200 and changes the deal to refunded;
  report generation and download both return 402.
- Replaying checkout completion after the full refund returns HTTP 200 and leaves
  access revoked.

Both synthetic accounts were deactivated afterward and verified inactive. Their
clearly labeled test deal and two report versions remain as an audit fixture.
The runtime test driver retained credentials only in memory and was stopped.
No real funds moved and no receipt or client email was sent. Hosted testing covered
card decline/success and refunds; delayed payment methods and expiry have automated
coverage but were not exercised against Stripe in this run. Live configuration,
engagement/privacy retention terms and the broader release gates above remain outstanding.

### Backups and recovery — September 17, 2026

Supabase Pro was enabled by the owner. Its managed backup page showed a physical
recovery point at 2026-09-17 19:40 UTC. The independent private Railway bucket and
nightly backup service are deployed with 30-day operational recovery retention.
The backup uses a consistent database snapshot, verifies a temporary restore,
encrypts with age X25519, uploads and downloads the encrypted object to verify it.
Only the public encryption recipient is hosted; the private recovery identity
is outside source control in an owner-only Windows directory for vault custody.

A hosted backup finished at 2026-09-18 03:05:39 UTC. A separate recovery rehearsal
downloaded and decrypted that object, restored all 40 public application tables,
and matched all row fingerprints, document/report hashes, RLS, grants, policies
and migration head at 03:06:17 UTC. Production was never a restore target. Seven
focused tests passed for retention bounds and stale/future/unverified receipts;
focused Ruff and formatting passed. The managed Supabase restore itself was not
performed, and no production recovery-time commitment is inferred.

Backup cron is 09:00 UTC daily (02:00 Arizona); the separate bucket-only monitor
checks hourly at minute 15 and fails if no verified snapshot exists within 26 hours.
Railway's account notification rules already enable email and in-app alerts for
failed/crashed deployments and high-severity events. See `ops/backups/README.md`
for service IDs, operator recovery, pre-migration backups and Stripe reconciliation.

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
