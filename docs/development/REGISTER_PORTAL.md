# Obligation Register client portal

Built on `feature/durable-ask-chat` at `a1fda08b8ee024de3a7c21ebe650f265357d9397`.
The React portal and standalone healthcare entry point both serve `/register` and
`/register/:dealId`. The public offer page links to the workspace. This code does
not deploy the product or configure hosted accounts.

## Client and operator workflow

1. Clients register/sign in using existing BFMS accounts. The workspace requires a
   valid access JWT and an active database user even when legacy auth flags are off.
2. Open one workspace per closed deal. Eligibility and storage consent are required;
   the initial release accepts private obligated persons only. Record the professional contact.
3. Upload searchable PDF, DOCX, UTF-8 TXT or Markdown files. Documents and extracted
   text persist in SQL; duplicate file hashes within a deal are deduplicated.
4. Alternatively attach a shared Drive, Dropbox, OneDrive, SharePoint or Box URL.
   **This records a link, not OAuth authorization or sync.** An operator opens the
   link through the ordinary cloud UI, obtains access from the client if needed,
   uploads the actual files to the deal, and marks the folder imported with a note.
   The backend never fetches submitted URLs. Unimported folders block package builds.
5. A trusted operator reviews the document pack, verifies scope/eligibility and the
   signed engagement through the existing business process, and issues a USD quote
   with included scope and delivery terms. Set `User.is_superuser=true` only for
   trusted Muni-Pal staff through an audited database administration process.
   The operator inbox uses the same portal and explicitly permits cross-client access.
6. The client pays that quote in Stripe Checkout. The server supplies the amount;
   clients cannot set prices or purchase another user's deal. A quote locks once
   checkout starts. Expired checkout releases the lock with a new idempotency key.
7. Verified payment unlocks candidate generation and report downloads for that deal.
   A return URL alone cannot grant access. Refresh after returning from Checkout.
8. Build the candidate package. Each saved version contains CSV and JSON excerpts,
   a document/hash manifest, the existing DIY skill, checklist, legend and template.
9. Operators can also publish a reviewed ZIP delivery with a client-visible note
   and approval reference. This supports delivering complete register/calendar/gap
   packages produced through the existing approved-input fulfillment process.
   Earlier versions remain downloadable. Publishing is logged by actor and timestamp.
10. Clients implement their approved schedules in their own reminder/automation
    tools. This portal does not activate those services or send marketing emails.

## Engine boundary

The original runner in `fulfillment/demo/run.py` depends on synthetic documents,
approved inputs and vault paths. It is **not safe to invoke that demo as customer
fulfillment**. `register_engine.py` adapts its duty-language matching into a pure
production function that receives only the current deal's stored documents.

The initial automatic output is deliberately a **lexical candidate first pass**,
not a complete interpreted map. It keeps contiguous source paragraphs/page text,
clause identifiers where found and locators. Recipients, frequencies, deadline-rule
fields and obligation summaries remain blank pending the supplied AI skill or team
review. A candidate can bind another party. No matching clause does not establish
the absence of obligations. It does not compute dates, infer applicability, assign
filing status, send documents to an LLM, or convert candidates to approved obligations.
The full existing approved-input register engine remains operator-run; its reviewed
outputs can be published in the portal. The synthetic demo and hash-pinned assets
were not modified or imported into customer records.

Automatic packages are not the completion of the full ten-day engagement. A team
delivery should state what is complete, what remains open, and the written approvals
used for any register rows. The quote/engagement governs the promised scope.

## Database and Supabase

The dedicated **Launch Shop / Muni-Pal** project is now provisioned and initialized:
`eywppovcndfuocaphrer` (US West / Oregon). Its initial schema was verified at
`e5f6g7h8i9j0` with no client accounts or migrated production records. The project
uses the Free plan; backups and production capacity still require setup.

The verified session-pooler settings are host `aws-0-us-west-2.pooler.supabase.com`,
port `5432`, user `postgres.eywppovcndfuocaphrer`, database `postgres`. The password
belongs only in the backend hosting secret settings. Project dashboard:
https://supabase.com/dashboard/project/eywppovcndfuocaphrer

**Supabase works as managed PostgreSQL for the existing SQLAlchemy/Alembic backend.**
Keep BFMS authentication for this release; replacing it with Supabase Auth would
require a separate token verification/user migration project. No browser Supabase
client, anonymous key, service-role key or alternate login system is introduced.

Use a dedicated Supabase project and the direct connection or **session pooler on
port 5432** for this long-running backend. Do not use the transaction pooler with
this connection configuration. Example server settings (supply values securely):

```dotenv
USE_SQLITE=false
POSTGRES_HOST=aws-0-REGION.pooler.supabase.com
POSTGRES_PORT=5432
POSTGRES_USER=postgres.PROJECT_REF
POSTGRES_PASSWORD=<database-password>
POSTGRES_DB=postgres
POSTGRES_SSL=true
AUTH_ENFORCEMENT_V2=true
TENANT_ISOLATION_V2=true
DEBUG=false
JWT_SECRET_KEY=<existing-strong-bfms-jwt-secret>
REGISTER_FRONTEND_URL=https://muni-pal.io
STRIPE_SECRET_KEY=<stripe-server-secret>
STRIPE_WEBHOOK_SECRET=<signature-secret-for-this-endpoint>
```

The settings URL-encode credentials and enable TLS for async API and sync migration
connections. Obtain the real host/user from Supabase's Connect dialog; do not copy
the example literally. Use the server database owner or a carefully granted server
role that can access the API-owned tables. Never expose database credentials to React.

Migration `e5f6g7h8i9j0` follows the durable Ask head `d4e5f6g7h8i0` and creates:

- `register_deals`: ownership/tenant, contact, consent version, quotes and payment state.
- `register_documents`: original bytes, extracted text, file hashes and metadata.
- `register_folders`: shared links and operator import notes.
- `register_reports`: immutable delivery bytes, hash, version and publisher.
- `register_payment_reversals`: durable full-refund revocations, including refunds
  arriving before checkout completion.

The migration enables PostgreSQL RLS on all five new tables, creates no browser
policies, and revokes PUBLIC table grants. **Disable Supabase's Data API for this
project** (or isolate all BFMS tables in an unexposed schema) before adding existing
BFMS data: older BFMS tables predate these RLS protections. This application accesses
Postgres through FastAPI, so the Data API is unnecessary.

For the bounded first release, source files and delivery ZIPs are stored privately
in the database along with their records, not in ephemeral backend disk storage.
This provides transactional persistence and backup coverage, but consumes database
capacity. The intake limits are 10 MB/file, 30 files and 50 MB/deal, 300 PDF pages,
one million extracted characters/file, ten folder links and twenty delivery versions.
ZIP deliveries are limited to 10 MB compressed, 50 MB expanded and 200 entries.
Larger volumes should move bytes behind the same authorization endpoints to private
Supabase Storage/object storage with lifecycle controls. Scanned/blank PDF pages
require OCR before upload. Test real closing packs against these bounds before launch.

Configure backups and retention for all five tables. There is no self-service
deletion/retention or organization-team membership UI in this slice; users see only
their own deals in their current database-backed tenant, while designated operators
have access across clients. Ownership does not flow from a JWT role or supplied tenant.

## Stripe setup

Stripe already exists in BFMS for subscriptions. This release adds **one-time,
quote-per-deal Checkout**, with inline server-controlled USD prices; it does not
require a new Stripe Product/Price for each quote. Use test mode first.

The existing `/api/v1/stripe/webhook` endpoint must receive:

- `checkout.session.completed`
- `checkout.session.async_payment_succeeded`
- `checkout.session.expired`
- `charge.refunded`
- Existing subscription events already used by BFMS.

Fulfillment validates the stored session ID, owner, quote version, payment mode,
paid status, currency, amount and payment intent. Duplicate events are harmless.
Full refunds revoke online report access; partial refunds preserve access (including
the offer's possible service-credit refunds). PostgreSQL advisory locks serialize
refund/completion races, including when events arrive out of order. Downloaded files
cannot be recalled. Dispute handling and subscription lifecycle hardening beyond
existing behavior are not introduced here and need operational handling in Stripe.
Use the existing account's Stripe receipt settings; this release has no invoice
history screen, billing portal or recurring entitlement for registers.

Purchasing a register does **not** change `User.subscription_tier` or unlock Ask.
Ask remains the existing subscription product and searches existing project chunks,
not the new Register intake tables. Connecting Register documents to Ask is a
separate future scope; do not imply that this integration is present.

## Deployment

1. Back up the target database, verify the environment and disable direct Data API
   exposure before migrating any existing BFMS data into Supabase.
2. Review migration SQL, then run `uv run --extra dev alembic upgrade head` on the
   hosted PostgreSQL connection. Inspect new tables, indexes and RLS.
3. Deploy `munipal.main:app`. The public-only `munipal.sensing_app:app` intentionally
   excludes private Register routes. Route `/api/v1/register/*`, `/api/v1/auth/*`
   and `/api/v1/stripe/*` to the main backend. The supplied Vercel rewrites now send
   Register, Ask, authentication and Stripe requests to the separate portal backend
   at `https://muni-pal-portal-production.up.railway.app`. Public sensing requests
   continue to use `https://api.muni-pal.io`.
   The chosen deployment is a **separate service in the existing Railway project**.
   Use `docker/Dockerfile.portal` for its image, with repository root build context;
   it installs `uv.lock` dependencies and runs migrations before starting the API.
   Ensure the service uses its own start command, not the sensing command in the
   existing `railway.toml`. Supply a strong JWT secret and the database/Stripe secrets
   through Railway settings, then point private frontend API rewrites to this service.
   Railway project: `inspiring-victory`; service: `Muni-Pal Portal`
   (`3d8ba4b4-9bd3-468c-a44d-a77de5978127`). The first hosted deployment is active,
   with `/health` healthy and Supabase connectivity verified. Redis is not configured;
   the aggregate readiness response reports that optional broader-BFMS dependency as
   unavailable. This Register workflow does not use Redis/background jobs.
4. Build/deploy the React portal or healthcare frontend. The new routes exist in
   both. Preserve existing API rewrites and backend settings.
5. Configure a trusted operator account. Import one test closing pack; review it;
   issue a quote; verify payment using **Stripe test mode**, webhook delivery,
   refresh/reload persistence, report creation/download, full refund and another
   client's denial. Test fresh and expired Checkout and delayed payment completion.
6. Before accepting live customers, verify hosting upload/time limits (the reverse
   proxy must support these uploads), hosted backups, paid-mode settings, data
   retention expectations and the complete engagement/fulfillment process.

No hosted migration, production deployment, live charge, client communication or
Supabase project creation is performed by the source changes.

Sources: [Supabase connections](https://supabase.com/docs/guides/database/connecting-to-postgres),
[SQLAlchemy with Supabase](https://supabase.com/docs/guides/troubleshooting/using-sqlalchemy-with-supabase-FUqebT),
[Stripe fulfillment](https://docs.stripe.com/checkout/fulfillment).
