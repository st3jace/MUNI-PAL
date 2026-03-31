"""Backfill issuer/borrower names from document filenames.

Healthcare EMMA filings embed the health-system name in the document
filename (e.g. "Hospital_Sisters_Health_System_monthly_Self_Liquid…").
This script uses the deterministic FilenameIssuerExtractor to populate
issuer_name on deal_identity rows that currently lack it, then propagates
names across documents that share the same EMMA submission hash prefix.

Usage:
    python -m emma.bond_os_extractor.src.analysis.backfill_issuers \
        --db emma/bond_os_extractor/data/healthcare/corpus.db
"""

from __future__ import annotations

import argparse
import logging
import sqlite3
from collections import defaultdict
from pathlib import Path

from ..extraction.deterministic import FilenameIssuerExtractor

logger = logging.getLogger("bond_os_extractor.backfill_issuers")


def backfill(db_path: str | Path, *, dry_run: bool = False) -> dict[str, int]:
    """Update deal_identities rows where issuer_name is NULL.

    Strategy:
    1. Per-file extraction using FilenameIssuerExtractor
    2. Hash-group propagation (documents sharing the same EMMA submission
       hash prefix belong to the same issuer)
    """
    db_path = Path(db_path)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    # Load all rows
    rows = conn.execute("""
        SELECT di.rowid, di.document_id, d.source_file,
               di.issuer_name, di.borrower_name, di.official_title
        FROM deal_identities di
        JOIN documents d ON d.id = di.document_id
    """).fetchall()

    # Group by hash prefix (first 33 chars of source_file)
    hash_groups: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        prefix = row["source_file"][:33]
        hash_groups[prefix].append({
            "rowid": row["rowid"],
            "file": row["source_file"],
            "issuer": row["issuer_name"],
            "borrower": row["borrower_name"],
            "has_title": bool(row["official_title"]),
        })

    from_filename = 0
    from_propagation = 0

    # Phase 1: Extract from filenames for rows without issuer_name
    for prefix, docs in hash_groups.items():
        for d in docs:
            if d["issuer"]:
                continue
            ext = FilenameIssuerExtractor(source_file=d["file"])
            result = ext.safe_extract("", "COVER_PAGE")
            borrower = result.get("borrower_name")
            if borrower:
                if not dry_run:
                    conn.execute(
                        """UPDATE deal_identities
                           SET issuer_name = ?, borrower_name = ?
                           WHERE rowid = ?""",
                        (borrower, borrower, d["rowid"]),
                    )
                d["issuer"] = borrower
                from_filename += 1

    # Phase 2: Propagate within hash groups
    for prefix, docs in hash_groups.items():
        named = [d for d in docs if d["issuer"] and len(d["issuer"]) >= 4]
        unnamed = [d for d in docs if not d["issuer"]]
        if named and unnamed:
            # Prefer longest (most informative) name from the group
            best = max(named, key=lambda d: len(d["issuer"]))
            issuer = best["issuer"]
            for d in unnamed:
                if not dry_run:
                    conn.execute(
                        "UPDATE deal_identities SET issuer_name = ? WHERE rowid = ?",
                        (issuer, d["rowid"]),
                    )
                d["issuer"] = issuer
                from_propagation += 1

    if not dry_run:
        conn.commit()

    # Compute final stats
    total = conn.execute("SELECT COUNT(*) FROM deal_identities").fetchone()[0]
    has_issuer = conn.execute(
        "SELECT COUNT(*) FROM deal_identities "
        "WHERE issuer_name IS NOT NULL AND issuer_name != ''"
    ).fetchone()[0]

    conn.close()

    summary = {
        "total": total,
        "from_filename": from_filename,
        "from_propagation": from_propagation,
        "total_named": has_issuer,
        "unknown_rate_pct": round((total - has_issuer) / total * 100, 1),
    }
    logger.info("Backfill complete: %s", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill issuer names from filenames")
    parser.add_argument("--db", required=True, help="Path to corpus SQLite database")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    summary = backfill(args.db, dry_run=args.dry_run)
    print(f"Results: {summary}")


if __name__ == "__main__":
    main()
