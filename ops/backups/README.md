# Muni-Pal database backups

The managed Supabase Pro daily backup is the full-platform recovery layer, with
seven days of history. This additional job exports the complete BFMS `public`
schema and data (including account password hashes, documents, ZIP reports,
ownership, quotes, payment/refund state, RLS and grants) into a private Railway
bucket. Supabase internal schemas, provider settings, external folder contents
that have not been imported, and hosting secrets are not part of this export.
Keep provider recovery access and hosting secrets in the business password vault.

## Hosted setup

- Supabase: Launch Shop / Muni-Pal, `eywppovcndfuocaphrer`, Pro.
- Railway project: `7b974931-50a6-4a91-817b-16edf86c6b46`.
- Environment: `7362fc32-ca26-4df7-a705-83e4a896791a` (production).
- Backup service: `5252b98e-6d2a-4bba-9389-3f322cd24bd6` (Muni-Pal Backups).
- Monitor service: `e078f192-cb1d-4f9c-ac9e-f0e8e2bd3a8f` (Muni-Pal Backup Monitor).
- Private bucket: `5e67733f-c800-4e16-baab-779c763d4d6f` (muni-pal-backups), US West.
- Configured backup schedule: `0 9 * * *` (02:00 America/Phoenix).
- Configured monitor schedule: `15 * * * *` (hourly at minute 15).
- Restart policy: Never; cron services exit when complete.
- Backup command: `python3 /app/backup.py backup`.
- Monitor command: `python3 /app/backup.py monitor`.
- No public domain or inbound service endpoint.

Railway no longer accepts legacy railway.json/railway.toml config for new services.
Set the schedules and start commands in service Settings, or use Railway's current
Infrastructure as Code support. These services are CLI-deployed separately from
the portal, so ordinary portal commits do not change backup code.

Build with `docker/Dockerfile.backup`. For a CLI upload, prepare an isolated build
directory containing this Dockerfile as `/Dockerfile` and `ops/backups/backup.py`;
do not upload local recovery keys, exports, or the entire scratch workspace.

Backup variables reference the existing portal POSTGRES_HOST, POSTGRES_PORT,
POSTGRES_USER, POSTGRES_PASSWORD and POSTGRES_DB. TLS is mandatory. AWS_ACCESS_KEY_ID,
AWS_SECRET_ACCESS_KEY, AWS_DEFAULT_REGION, AWS_ENDPOINT_URL and BUCKET_NAME reference
the private bucket. The monitor gets only bucket variables, not database access.
BACKUP_AGE_RECIPIENT contains only the public age X25519 recipient. The private
recovery identity must never be uploaded to Railway, GitHub, logs, or this repository.

The backup worker currently uses the portal's existing database credential to
export rows behind RLS. Its application code performs only read transactions on
the source database. The temporary restore database runs on loopback with a fresh
random password. All raw dumps are transient and removed when the job exits.

## Verification and retention

Each backup takes a PostgreSQL consistent snapshot, exports schema/data, hashes
every table's contents, and checks stored document/report hashes. It restores into
a newly initialized, isolated PostgreSQL cluster and compares the records, RLS,
policies, grants and migration head. The job then encrypts the dump and manifest
using age, uploads the encrypted archive, downloads it again, and verifies its hash.
Only then does it write the success receipt and prune this job's archives older
than 30 days. Other bucket objects and recent archives are never pruned.

The hourly monitor fails if the snapshot is over 26 hours old, is unverified, or
the stored object is missing/changed. Railway account notification rules must send
Deployment Failed, Deployment Crashed and high-severity alerts by email and in-app.
This is a separate job but shares Railway's availability; it cannot deliver a
Railway alert during a platform-wide Railway outage. Supabase remains independent.

Thirty days is operational recovery retention, not a records-retention or legal
hold policy. Backups can contain deleted client records until they expire. Update
engagement/privacy terms and deletion handling consistently. The bucket does not
provide immutable object locks; authorized Railway administrators can delete it.

## Operator recovery rehearsal

Install PostgreSQL 18 client/server tools, age, Python, boto3 and psycopg2. Put the
PostgreSQL and age executables on PATH. Load bucket credentials into process
environment variables using the hosting secret manager; never paste them into
commands, chat, or a tracked file. Run:

```text
python ops/backups/backup.py rehearse --identity /secure/path/Muni-Pal-recovery-key.agekey
```

This downloads and decrypts the most recent archive, validates its manifest,
restores it into a new temporary local PostgreSQL cluster, compares all data and
security metadata, shuts the cluster down, and removes temporary plaintext files.
It cannot restore over a supplied production database. The recovery identity is
kept only on the operator device. Repeat after changing keys, storage, schema,
or backup tooling, and periodically as an operational drill.

Before any database migration, trigger a fresh backup via the backup service's
Cron Runs page and verify a new `backup_verified` log/receipt before proceeding.
Do not mistake a successful deployment/build for a completed backup.

## Actual incident recovery

1. Stop portal writes and pause migrations. Preserve current state for investigation.
2. Select a clean recovery point. Prefer a new database/project over overwriting the
   damaged one. Supabase managed restore is the full-platform option; the encrypted
   archive can rebuild the BFMS public schema on a separately provisioned database.
3. Restore using PostgreSQL tooling with the correct Supabase roles/extensions and
   existing managed schema handled by an operator. The automated rehearsal proves
   the application's public-schema data; it is not an automatic production cutover.
4. Verify account roles, tenant/owner separation, RLS/grants, row/file checksums,
   report downloads and application login. Reconfigure TLS and hosting secrets from
   the password vault. Keep Stripe live secrets out of a rehearsal environment.
5. Reconcile Stripe payments/refunds since the recovery point before enabling
   paid access or processing webhook replays. Never create replacement charges.
   Preserve refund revocation and checkout idempotency protections.
6. Point the portal to the recovered database, run smoke checks, then reopen writes.
7. Take a new backup and record actual data loss and recovery time.

Daily coverage allows roughly 24 hours of data loss. No full production recovery
time is promised from a small test-data rehearsal. PITR remains an optional upgrade.

## Initial evidence

On 2026-09-17 Arizona time, the managed Supabase backup page showed a physical
recovery point at 2026-09-17 19:40 UTC. A hosted encrypted backup completed at
2026-09-18 03:05:39 UTC. A separate download/decrypt/restore rehearsal passed at
03:06:17 UTC, matching all 40 application tables, RLS/grants and document/report
hashes. Freshness check passed. Seven focused tests cover stale/future/unverified
receipts and retention boundaries. No production records were altered by recovery.
