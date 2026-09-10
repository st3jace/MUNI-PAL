# Source register — where names come from (no EMMA)

Route (Hermosillo 2026-09-09 §3.1): **issuer or registry → deal → obligated person → sponsor → named human.**
Four steps are public record. Only the last needs Clay.

Every row we add to `prospects.csv` must cite one of the sources below in its `source` column.
"Tested" means we pulled it on the date shown and got named borrowers out of it.

| # | Source | What it gives | Yield | Tested | How to pull |
|---|---|---|---|---|---|
| S1 | **Phoenix IDA — published bond-transaction list** (PDF) | Closed conduit deals 2009→2025: closing month, project, address, amount. ~100 rows. Housing, charter schools, senior living, 501(c)(3), a few industrial | High | 2026-09-10 | `ingest_phoenix_ida.py` → `raw/phoenix-ida.csv` |
| S2 | **CSCDA news archive** (cscda.org/news) | One post per closed issuance: borrower, amount, date. California housing + 501(c)(3). Paginated | High | 2026-09-10 (6 posts seen, archive not walked) | Walk `/news/` pages; parse title + first paragraph |
| S3 | **Arizona Finance Authority — PAB volume cap** (afa.az.gov) | Allocation confirmations name the project and the issuing IDA | Unknown | 2026-09-10: site returns 403 to fetchers | Pull by hand in a browser once; then decide |
| S4 | **Pima IDA TEFRA notices** (pimaida.org) | Current notices only, no archive. Names borrower **before** close, so it feeds Q6 (new issuance in contemplation), not the list | Low for A2-post | 2026-09-10 | Watch monthly; a name here means *do not* pitch A2-post until it closes |
| S5 | **Arizona IDA** (arizonaida.com) | No transaction list. A few projects in news | Low | 2026-09-10 | Skip |
| S6 | **Wisconsin PFA, NH NFA, FL FDFC published financings** | Arthur cleared these (3.3 #4). URLs not yet found; guessed paths 404 | Unknown | — | Find the real list pages by hand |
| S7 | **IRS Form 990 Schedule K** | Filed by the obligated person; lists outstanding tax-exempt issues and self-reports post-issuance compliance procedures. Best qualifier on the table (Hermosillo §3.2) | High if extractable | not yet | Confirm a Schedule K extract is obtainable before planning on it |
| S8 | **State debt registries** (TX BRB, FL DBF) | Issuer + borrower + series for conduit deals | Unknown | not yet | Verify each host's terms of use at the publisher first |

## Rules that travel with every source

- Q1 first, always: a State, subdivision, authority, IDA, district, or instrumentality is **municipal** → nurture file, never the prospect file.
- Q3: **closed**, not authorized, approved, or "cleared the board". S1 is closed by construction. S4 is the opposite.
- A TEFRA notice or a new-issuance announcement expires a row for A2-post (Q6). Move it, do not delete it.
- Housing rows name a property. The obligated person is the LP; the sponsor is who we call. Resolve the sponsor before Clay.
- Healthcare rows are sourced and held. Not called (para 8 gate).
- Record `source`, `source_url`, `retrieved` on every row. A row without them cannot enter a send.
