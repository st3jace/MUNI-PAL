# Obligation Register launch handoff

These four files are the September 17, 2026 output artifacts, published here for
the Muni-Pal team. They record the setup and verification performed on that date;
they are not a live service-status dashboard.

- [Portal launch notes](Muni-Pal-Portal-Launch-Notes.md)
- [Payment test results](Muni-Pal-Payment-Test-Results.md)
- [Backup and recovery guide](Muni-Pal-Backup-and-Recovery-Guide.md)
- [Initial database setup SQL](Muni-Pal-Database-Setup.sql)

The payment report predates backup configuration. Its backup setup action was
subsequently completed as documented in the backup guide. Client-facing retention
terms and live payment activation remain separate from the technical backup setup.

The SQL file initializes an **empty database** with the application schema and
seed/reference records. It is not a client-data backup and must not be run against
the existing production database. Use the maintained Alembic migrations for
subsequent schema changes.

The private `.agekey` recovery key is intentionally excluded from GitHub. The path
mentioned in the recovery guide refers to the original local handoff folder, not
a file in this repository. Keep that key in the business password vault. No client
document exports, database backup archives, or hosting credentials are included.

Maintained technical references:

- [Portal operation](../../development/REGISTER_PORTAL.md)
- [Portal verification](../../development/REGISTER_PORTAL_VERIFICATION.md)
- [Backup operation and recovery](../../../ops/backups/README.md)
