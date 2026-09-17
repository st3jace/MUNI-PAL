# Ask where it is — first release

`/ask` is available in both the BFMS portal and the public healthcare website entry point. Signed-in users get an **Ask where it is** navigation link. The website hosting configuration includes the Ask API rewrite; no deployment is performed by these changes.

## Using Ask

Sign in at `/auth?returnTo=/ask`. Choose an owned project, optionally select a document, then choose **New chat**. Ask for a record, for example “annual report” or “dissemination agent”. The scope stays fixed for that conversation; start another chat to change it. Conversations and messages are stored on the server and can be reopened after reload. **Delete chat** deletes the conversation and its messages.

Evidence cards contain the stored document name, section/page/sheet/chunk locator, an exact contiguous excerpt, and the internal chunk ID. **View source** resolves that ID through an authenticated, paywalled endpoint. Source text is displayed as quoted plain text, including any instructions or markup it contains.

Legal sufficiency, default, municipal-advisor approval or opinion, materiality, applicability, controlling-clause, compliance, advice, and deadline-calculation questions receive an explicit refusal. Both the question and refusal are saved. Nothing is sent to counsel or anyone else. A no-hit response means no matching excerpt was found in the searched scope; it does not establish the absence of a record or obligation.

## Local setup and migration

Use the repository's existing dependency setup and PostgreSQL configuration (`USE_SQLITE=false`). No new provider, API key, or LLM service is required. From the repository root:

```powershell
$env:UV_CACHE_DIR="$PWD/.uv-cache"
$env:AUTH_ENFORCEMENT_V2="true"
$env:TENANT_ISOLATION_V2="true"
uv run --no-sync --python .venv/Scripts/python.exe python -I -m alembic upgrade head
uv run --no-sync --python .venv/Scripts/python.exe python -I -m uvicorn munipal.main:app --host 127.0.0.1 --port 4120
```

From `frontend/`, set `VITE_API_PROXY_TARGET=http://127.0.0.1:4120` and run `npm run dev -- --port 4121`. The standalone healthcare configuration uses `VITE_SENSING_API_URL` for the same backend target. Production must also set `AUTH_ENFORCEMENT_V2=true` and `TENANT_ISOLATION_V2=true`; otherwise the portal's compatibility identity mode can prevent a real bearer-token profile from loading even though Ask itself fails closed. These are local setup instructions, not actions run against a live database in this release verification.

Migration `d4e5f6g7h8i0` follows `c3d4e5f6g7h9`. It adds canonical SQLAlchemy `ask_conversations` and `ask_messages` tables, timestamps, owner/project/document foreign keys, and a unique conversation/sequence constraint. An atomic sequence reservation orders user/assistant pairs across workers. A send saves both messages in one transaction. Deleting a user, project, or explicitly scoped artifact cascades the associated chats; deleting a chat cascades its messages. Back up these tables alongside the rest of the application database. Downgrading this migration removes chat history.

The authorized Windows checkout fails only the WSL-path portion of `check_dev_environment.py`; proceed here under the task's explicit exception. Python `-I` avoids Hermes/PYTHONPATH contamination; the repo venv works with it. Tests use isolated SQLite databases, including a file-backed migration/reconnection test; PostgreSQL remains the application database.

## Authentication and billing contract

Every `/api/v1/ask/*` operation requires a valid, unexpired **access** JWT and an existing active database user. Refresh tokens, development headers, fallback users, and superuser bypasses grant no Ask access. The existing auth/role/tenant rollout flags cannot disable these checks.

Ask currently requires `User.subscription_tier == "subscription"`. Free, absent, and `per_project` tiers are denied. The existing data model does not identify which project a per-project purchase covers, so accepting that tier would incorrectly unlock Ask across every project the user owns. Per-project Ask access remains closed until a project-entitlement mapping is implemented. Stripe provisioning remains governed by the existing billing workflow; Ask does not redefine checkout, trial, cancellation, or webhook behavior. This release adds no new billing secret and makes no real Stripe calls during tests.

| Result | Contract |
| --- | --- |
| Missing/invalid identity | `401`, `WWW-Authenticate: Bearer` |
| Free/per-project/no subscription | `403`, `detail.code = subscription_required`, `detail.upgrade_url = /pricing` |
| Deactivated account | `403`, `detail.code = account_inactive` |
| Missing or inaccessible resource | Identical `404`, `detail = Not found` |
| Invalid input | Sanitized `422` without submitted question text |
| Body exceeds 16 KiB | `413` before JSON parsing |
| Chat exceeds 100 question/answer pairs | `409`; start a new chat |

Success and error responses use `Cache-Control: no-store`. Ask never logs raw questions or document excerpts. SQL echo is disabled on application engines so debug mode does not log bound question/document parameters. Private error responses suppress exception details even in debug mode. Conversation text is intentionally retained in the database; apply the existing database access/backup controls.

## Scope and limitations

- Real evidence comes only from existing `Project -> Artifact -> Chunk` records. No `fulfillment/demo` files, reference shelves, or synthetic customer evidence are loaded. No production blocker prevents this authorized path.
- Owner **and** database-backed tenant filters apply in SQL before candidate generation. Ask is intentionally owner-only, including for superusers; organization membership alone grants no access. Saved citations are reauthorized before history is returned. Moved/deleted evidence can make an old conversation unavailable (`404`), rather than disclose an outdated scope.
- Only already chunked text is searchable. Ask does not perform upload, OCR, extraction, semantic search, legal analysis, date arithmetic, or determination of controlling clauses. The public website does not add a document-ingestion workflow; users need records in their existing project workspace.
- Retrieval is deterministic lexical scoring, ported from the demo operating rules. English judgment detection is conservative and rule-based; it can refuse record searches containing judgment terms. Even an unrecognized phrasing produces only source excerpts or no hits, never a generated determination.
- Limits: 2,000 question characters, 32 lexical terms, first 1,000 chunks ordered by artifact ID/sequence/chunk ID, four citations, 1,600 characters per exact excerpt. Candidate truncation is disclosed in the response. Scope menus show up to 100 projects and 200 documents per project. Chat lists paginate 50 at a time; histories contain at most 200 messages.
- Excerpts are snapshots of the stored extraction text, not a guarantee of OCR accuracy. Source resolution returns a bounded opening excerpt from the current chunk. Verify the original document when more context is needed.
- Sending is atomic but does not deduplicate retries after a lost network response. The UI retains the draft and tells the user to reopen the conversation before retrying. Chats have no sharing, export, external delivery, or background model calls.

## Verification

See [ASK_VERIFICATION.md](ASK_VERIFICATION.md) for the exact commands, RED/GREEN evidence, passing checks, and separate baseline/environment blockers.
