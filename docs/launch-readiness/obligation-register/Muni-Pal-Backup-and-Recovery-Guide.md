# Muni-Pal backup and recovery

Configured September 17, 2026 (Arizona time).

## Protection in place

| Protection | Setup |
|---|---|
| Managed database backups | Supabase Pro, daily, seven days of history |
| Independent backup | Encrypted copy in a private Railway bucket |
| Nightly schedule | 2:00 a.m. Arizona time |
| Independent retention | 30 days; old copies expire after a new backup succeeds |
| Restore verification | Every nightly export is restored into an isolated temporary database and compared with the source snapshot |
| Freshness monitoring | Hourly; reports failure if the newest verified snapshot is more than 26 hours old or its stored object is missing/changed |
| Alerts | Railway account email and in-app notification rules for failures/crashes and high-severity events |

The backup includes application accounts, access/ownership records, uploaded
documents, extracted text, report versions, quotes, payment state and refunds.
It does not copy documents still sitting only in a client's linked cloud folder.
It does not contain hosting passwords/API secrets or Supabase's internal services.
Supabase's managed backup supplies the separate full-database recovery layer.

## Recovery rehearsal completed

A hosted encrypted backup completed at September 17, 8:05:39 p.m. Arizona time.
It was then downloaded, decrypted with the separate recovery key, and restored
into a new temporary database. All 40 application tables matched, including
document/report checksums and database access rules. The rehearsal finished at
8:06:17 p.m. No production records were overwritten.

This proves the current small database can be recovered. A full production cutover
and recovery time under a larger client workload have not been measured.

## One action for the owner

Save `Muni-Pal-Recovery/Muni-Pal-recovery-key.agekey` in the business password
manager as a secure attachment, with the name **Muni-Pal database backup recovery
key**. Keep an emergency copy available to an authorized business owner.

This key is required to decrypt the independent backups. Railway has only the
public encryption key and cannot recreate this private key. The local copy is in
a Windows folder restricted to your user account. Do not put it in GitHub, email,
the client portal, or the backup bucket. Do not remove the local copy until you
have verified that the password-vault copy is available and complete.

Also retain Supabase/Railway recovery access and hosting secrets in the business
vault. A database backup alone cannot recover an inaccessible hosting account.

## What happens during a recovery

1. Pause portal changes and preserve the current state for investigation.
2. Select a clean backup and restore into a separate database where possible.
3. Check accounts, document/report integrity, client isolation and portal access.
4. Reconcile payments and refunds with Stripe since the backup time before
   reopening paid access. Do not charge clients again.
5. Reconnect the portal, run final checks, and reopen it.
6. Record the incident and take a fresh backup.

Daily backups can lose about a day of recent work. They do not promise uninterrupted
service. More frequent recovery remains an optional future upgrade.

## Ongoing operation

- Check Railway alerts promptly; a failed backup must not be treated as success.
- Trigger a fresh verified backup before a database migration.
- Repeat the download/decrypt/recovery rehearsal after changing keys, storage,
  database structure or backup tooling, and periodically as an operational drill.
- Keep client data-retention/deletion terms consistent with the 30-day recovery
  window. This is an operational setting, not a legal retention determination.
- Review storage and job usage as deal volume grows.

The monitor and independent backup share Railway availability. Supabase remains a
different provider. Railway administrators can delete the bucket; these are not
immutable archives or a legal-hold system.

## Costs and links

Supabase showed $25 charged on upgrade and an estimated $35 monthly organization
bill for Launch Shop's two projects, before extra usage. Railway adds storage and
job usage. Point-in-time recovery was not enabled.

- [Supabase daily backups](https://supabase.com/dashboard/project/eywppovcndfuocaphrer/database/backups/scheduled)
- [Nightly backup service](https://railway.com/project/7b974931-50a6-4a91-817b-16edf86c6b46/service/5252b98e-6d2a-4bba-9389-3f322cd24bd6/schedule?environmentId=7362fc32-ca26-4df7-a705-83e4a896791a)
- [Hourly backup monitor](https://railway.com/project/7b974931-50a6-4a91-817b-16edf86c6b46/service/e078f192-cb1d-4f9c-ac9e-f0e8e2bd3a8f/schedule?environmentId=7362fc32-ca26-4df7-a705-83e4a896791a)
- [Railway notification preferences](https://railway.com/account/notifications)

The technical runbook and backup implementation are in the MUNI-PAL repository
under `ops/backups/`.
