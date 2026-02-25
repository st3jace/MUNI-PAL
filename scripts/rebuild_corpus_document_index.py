"""
Rebuild cross-module document_index entries for corpus databases.

Usage:
    python scripts/rebuild_corpus_document_index.py
    python scripts/rebuild_corpus_document_index.py --clear-existing
    python scripts/rebuild_corpus_document_index.py --sector healthcare
"""

from __future__ import annotations

import argparse
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class RebuildSummary:
    sector: str
    db_path: Path
    scanned_rows: int
    indexed_rows: int
    skipped_missing_hash: int
    skipped_collisions: int
    index_count_after: int
    by_doc_type: dict[str, int]


DOC_TYPE_ORDER = (
    "official_statement",
    "rating_action",
    "event_filing",
    "financial_report",
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _default_sector_db_map() -> dict[str, Path]:
    root = _repo_root() / "emma" / "bond_os_extractor" / "data"
    return {
        "waste": root / "waste" / "corpus.db",
        "healthcare": root / "healthcare" / "corpus.db",
    }


def _fetch_rows(conn: sqlite3.Connection, *, doc_type: str) -> list[sqlite3.Row]:
    if doc_type == "official_statement":
        return conn.execute(
            """
            SELECT
                d.source_hash AS source_hash,
                d.source_file AS source_file,
                d.id AS module_record_id,
                d.extraction_timestamp AS extraction_timestamp,
                di.issuer_name AS issuer_name,
                d.completeness_score AS completeness_score
            FROM documents d
            LEFT JOIN deal_identities di ON di.document_id = d.id
            """
        ).fetchall()
    if doc_type == "rating_action":
        return conn.execute(
            """
            SELECT
                source_hash,
                source_file,
                id AS module_record_id,
                extraction_timestamp,
                issuer_name,
                completeness_score
            FROM rating_actions
            """
        ).fetchall()
    if doc_type == "event_filing":
        return conn.execute(
            """
            SELECT
                source_hash,
                source_file,
                id AS module_record_id,
                extraction_timestamp,
                issuer_name,
                completeness_score
            FROM event_filings
            """
        ).fetchall()
    if doc_type == "financial_report":
        return conn.execute(
            """
            SELECT
                source_hash,
                source_file,
                id AS module_record_id,
                extraction_timestamp,
                issuer_name,
                completeness_score
            FROM financial_reports
            """
        ).fetchall()
    raise ValueError(f"Unsupported doc_type: {doc_type}")


def rebuild_document_index(
    *,
    sector: str,
    db_path: Path,
    clear_existing: bool,
) -> RebuildSummary:
    if not db_path.exists():
        raise FileNotFoundError(f"Corpus DB not found for sector `{sector}`: {db_path.as_posix()}")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    scanned_rows = 0
    indexed_rows = 0
    skipped_missing_hash = 0
    skipped_collisions = 0
    by_doc_type = {doc_type: 0 for doc_type in DOC_TYPE_ORDER}
    seen_hashes: set[str] = set()

    try:
        if clear_existing:
            conn.execute("DELETE FROM document_index")

        for doc_type in DOC_TYPE_ORDER:
            rows = _fetch_rows(conn, doc_type=doc_type)
            scanned_rows += len(rows)
            for row in rows:
                source_hash = str(row["source_hash"] or "").strip()
                if not source_hash:
                    skipped_missing_hash += 1
                    continue
                if source_hash in seen_hashes:
                    skipped_collisions += 1
                    continue
                seen_hashes.add(source_hash)
                conn.execute(
                    """
                    INSERT INTO document_index (
                        source_hash,
                        source_file,
                        doc_type,
                        module_record_id,
                        extraction_timestamp,
                        issuer_name,
                        completeness_score
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(source_hash) DO UPDATE SET
                        source_file = excluded.source_file,
                        doc_type = excluded.doc_type,
                        module_record_id = excluded.module_record_id,
                        extraction_timestamp = excluded.extraction_timestamp,
                        issuer_name = excluded.issuer_name,
                        completeness_score = excluded.completeness_score
                    """,
                    (
                        source_hash,
                        str(row["source_file"] or ""),
                        doc_type,
                        str(row["module_record_id"] or ""),
                        row["extraction_timestamp"],
                        row["issuer_name"],
                        row["completeness_score"],
                    ),
                )
                indexed_rows += 1
                by_doc_type[doc_type] += 1

        conn.commit()
        index_count_after = int(conn.execute("SELECT COUNT(*) FROM document_index").fetchone()[0])
    finally:
        conn.close()

    return RebuildSummary(
        sector=sector,
        db_path=db_path,
        scanned_rows=scanned_rows,
        indexed_rows=indexed_rows,
        skipped_missing_hash=skipped_missing_hash,
        skipped_collisions=skipped_collisions,
        index_count_after=index_count_after,
        by_doc_type=by_doc_type,
    )


def rebuild_all(
    *,
    sector_db_map: dict[str, Path],
    sectors: list[str] | None,
    clear_existing: bool,
) -> list[RebuildSummary]:
    selected_sectors = sectors or list(sector_db_map.keys())
    summaries: list[RebuildSummary] = []
    for sector in selected_sectors:
        if sector not in sector_db_map:
            raise ValueError(f"Unsupported sector `{sector}`. Available: {sorted(sector_db_map)}")
        summaries.append(
            rebuild_document_index(
                sector=sector,
                db_path=sector_db_map[sector],
                clear_existing=clear_existing,
            )
        )
    return summaries


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Rebuild document_index from corpus source tables.")
    parser.add_argument(
        "--sector",
        action="append",
        default=None,
        help="Sector to rebuild (repeatable). Defaults to all sectors.",
    )
    parser.add_argument(
        "--clear-existing",
        action="store_true",
        help="Delete existing document_index entries before rebuild.",
    )
    return parser


def _format_summary(summary: RebuildSummary) -> str:
    counts = ", ".join(f"{k}={v}" for k, v in summary.by_doc_type.items())
    return (
        "[corpus-document-index-rebuild] "
        f"sector={summary.sector} "
        f"scanned_rows={summary.scanned_rows} "
        f"indexed_rows={summary.indexed_rows} "
        f"skipped_missing_hash={summary.skipped_missing_hash} "
        f"skipped_collisions={summary.skipped_collisions} "
        f"index_count_after={summary.index_count_after} "
        f"by_doc_type={{ {counts} }}"
    )


def main() -> int:
    args = _build_parser().parse_args()
    summaries = rebuild_all(
        sector_db_map=_default_sector_db_map(),
        sectors=args.sector,
        clear_existing=bool(args.clear_existing),
    )
    for summary in summaries:
        print(_format_summary(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
