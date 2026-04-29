# Canonical Verification Commands

Run these commands from the canonical native WSL checkout:

    /home/st3ja/Developer/MUNI-PAL

Do not use bare system python for backend tests. The system interpreter may not have pytest or project dependencies installed. Use uv with the dev extra so verification runs against the project dependency set.

## Backend

Fast focused backend/doc guardrail checks:

    /home/st3ja/.local/bin/uv run --extra dev pytest tests/unit/test_agent_source_scope.py tests/unit/test_canonical_workspace_docs.py tests/unit/test_verification_commands_docs.py -q

Full backend test suite:

    /home/st3ja/.local/bin/uv run --extra dev pytest tests -q

Backend lint:

    /home/st3ja/.local/bin/uv run --extra dev ruff check src tests scripts

Backend type check:

    /home/st3ja/.local/bin/uv run --extra dev mypy src

## Frontend

The frontend has no root package.json. Run npm commands from frontend/.

Install dependencies when node_modules is absent or package metadata changes:

    cd frontend
    npm install

Frontend tests:

    cd frontend
    npm run test

Frontend lint:

    cd frontend
    npm run lint

Frontend type check and production build:

    cd frontend
    npm run build

API type generation, when the OpenAPI contract changes:

    cd frontend
    npm run generate:api-types

## Contracts and OpenAPI

The canonical OpenAPI contract lives at:

    contracts/openapi.v1.json

Contract verification:

    /home/st3ja/.local/bin/uv run --extra dev pytest tests/contract -q

Regenerate frontend API types after contract changes:

    cd frontend
    npm run generate:api-types

Then review generated diffs before committing.

## Standard cadence per Linear ELA

For each issue:

1. Move the Linear issue to In Progress.
2. Write or update the smallest failing test first when behavior changes.
3. Implement only that issue's scope.
4. Run focused verification for changed behavior.
5. Run this issue's relevant canonical commands.
6. Commit with a concise issue-scoped message.
7. Comment in Linear with files changed, verification output, and commit hash.
8. Move the issue to Done.

## Validation notes

These commands were validated from the canonical checkout for ELA-26. Backend and contract commands use uv because bare python3 -m pytest is not a valid verifier on this machine. Frontend commands require npm dependencies under frontend/ and should be run from that directory only.

Current frontend status observed during validation:

- npm install completes and installs frontend dependencies locally.
- npm run test is a valid Vitest command, but the existing Readiness page tests currently fail because rendered status text differs from test expectations.
- npm run lint is a valid package script, but ESLint currently has no frontend configuration file.
- npm run build is a valid type/build command, but current generated API/frontend drift produces missing CoiBenchmarking and sector/subsector type errors.

Those failures are now explicit verifier output rather than hidden setup ambiguity; fix them in the relevant frontend/API-drift issues instead of changing the canonical command names.
