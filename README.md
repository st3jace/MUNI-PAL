# Muni-Pal BFMS

Bond Facility Management System - Evidence-first, advisor-grade platform for municipal bond structuring.


## Development Workspace

Active engineering work should run from the native WSL checkout, not the OneDrive-backed Windows tree:

    /home/st3ja/Developer/MUNI-PAL

Before implementation work, run:

    python scripts/check_dev_environment.py

See docs/development/CANONICAL_DEV_PATH.md for the OneDrive policy, setup command, and agent-safe source review scope. See docs/development/VERIFICATION_COMMANDS.md for canonical backend, frontend, contract, lint, and type-check commands.

## Canonical application tree

The Root repository tree is canonical for current BFMS application development. Active application changes belong in these root-level paths:

- `src/` for the FastAPI/backend package.
- `frontend/` for the React frontend.
- `tests/` for unit, integration, and contract coverage.
- `contracts/` for generated/public API contracts.
- `alembic/` for database migrations.
- Root manifests such as `pyproject.toml`, `uv.lock`, and deployment/configuration files.

`V1/` and `V2/` are retained for lineage, auditability, and planning history. They are not the active application tree; do not add new production code, tests, migrations, or frontend work there unless a task explicitly says to edit historical/archive material.

## Quick Start

### Backend

```bash
# Install dependencies
pip install -e ".[dev]"

# Run server (canonical Postgres dev mode)
powershell -ExecutionPolicy Bypass -File scripts/start_backend.ps1 -ListenHost 127.0.0.1 -ListenPort 8000 -Reload

# Validate Redis separately (optional but recommended for hosted Redis)
python scripts/check_redis.py

# Run Celery worker for async extraction / deliverables
powershell -ExecutionPolicy Bypass -File scripts/start_worker.ps1
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

When `AUTH_ENFORCEMENT_V2=true`, set a bearer token for the frontend client:

```bash
# frontend/.env.local
VITE_API_PROXY_TARGET=http://127.0.0.1:8000
VITE_API_BEARER_TOKEN=<jwt token with UUID sub claim>
```

SQLite remains available for scratch work, but it is opt-in. The default `.env`
and `.env.example` now pin `USE_SQLITE=false` so the app stays pointed at the
Postgres dataset that contains the live dev projects.

## Redis Cloud

Muni-Pal accepts a full hosted Redis URL via `REDIS_URL`. Use the exact scheme
shown by your Redis provider. Some endpoints use TLS (`rediss://`), while
others are plain Redis (`redis://`).

```bash
REDIS_URL=rediss://default:<password>@<host>:<port>/0?ssl_cert_reqs=required
CELERY_BROKER_URL=${REDIS_URL}
CELERY_RESULT_BACKEND=${REDIS_URL}
```

Plain Redis example:

```bash
REDIS_URL=redis://default:<password>@<host>:<port>/0
CELERY_BROKER_URL=${REDIS_URL}
CELERY_RESULT_BACKEND=${REDIS_URL}
```

`scripts/check_redis.py` will verify auth + TLS before you start the worker.
On Windows, `scripts/start_worker.ps1` automatically uses Celery's `solo` pool
for local stability.

## API Documentation

When running in debug mode, API docs available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
