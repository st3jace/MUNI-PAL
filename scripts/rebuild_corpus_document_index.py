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

_ALLOWED_SQL_IDENTIFIERS = {
    "document_index",
    "ix_docidx_doc_type",
    "ix_docidx_issuer",
    "ix_docidx_provenance",
    "ix_docidx_source_hash_doc_type",
    "sqlite_autoindex_document_index_1",
}


def _quote_allowed_identifier(identifier: str) -> str:
    """Quote a known-safe SQLite identifier used in maintenance SQL."""
    if identifier not in _ALLOWED_SQL_IDENTIFIERS:
        raise ValueError(f"Unsafe SQL identifier: {identifier!r}")
    return '"' + identifier.replace('"', '""') + '"'


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

BACKFILL_PROVENANCE_BY_MARKER = {
    "analysis/cchci_obligor_profile.json": "backfill_obligor_profile",
    "research/corpus/healthcare/healthcare_credit_drivers.json": "backfill_research_corpus",
    "risk_implementation_guide.json": "backfill_waste_feedstock",
}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _default_sector_db_map() -> dict[str, Path]:
    root = _repo_root() / "emma" / "bond_os_extractor" / "data"
    return {
        "waste": root / "waste" / "corpus.db",
        "healthcare": root / "healthcare" / "corpus.db",
    }


def _table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    ).fetchone()
    return row is not None


def _infer_provenance_class(source_file: str) -> str:
    normalized = source_file.replace("\\", "/").strip().lower()
    if not normalized:
        return "unknown"
    if normalized == "test.pdf" or normalized.endswith("/test.pdf"):
        return "test_fixture"
    for marker, provenance_class in BACKFILL_PROVENANCE_BY_MARKER.items():
        if marker in normalized:
            return provenance_class
    if normalized.endswith(".pdf"):
        return "extracted_pdf"
    if normalized.endswith(".json"):
        return "extracted_json"
    return "derived_other"


def _has_composite_unique_index(conn: sqlite3.Connection) -> bool:
    rows = conn.execute("PRAGMA index_list(document_index)").fetchall()
    for row in rows:
        index_name = str(row[1] or "")
        is_unique = int(row[2] or 0) == 1
        if not is_unique or not index_name:
            continue
        columns = [
            str(col_row[2] or "")
            for col_row in conn.execute(f"PRAGMA index_info({_quote_allowed_identifier(index_name)})").fetchall()
        ]
        if columns == ["source_hash", "doc_type"]:
            return True
    return False


def _ensure_document_index_schema(conn: sqlite3.Connection) -> None:
    if not _table_exists(conn, "document_index"):
        conn.executescript(
            """
            CREATE TABLE document_index (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_hash TEXT NOT NULL,
                source_file TEXT NOT NULL,
                doc_type TEXT NOT NULL,
                module_record_id TEXT,
                extraction_timestamp TEXT,
                issuer_name TEXT,
                completeness_score REAL,
                provenance_class TEXT NOT NULL DEFAULT 'unknown',
                UNIQUE (source_hash, doc_type)
            );
            CREATE INDEX IF NOT EXISTS ix_docidx_doc_type ON document_index(doc_type);
            CREATE INDEX IF NOT EXISTS ix_docidx_issuer ON document_index(issuer_name);
            CREATE INDEX IF NOT EXISTS ix_docidx_provenance ON document_index(provenance_class);
            """
        )
        return

    columns = [
        str(row[1] or "")
        for row in conn.execute("PRAGMA table_info(document_index)").fetchall()
    ]
    needs_migration = "provenance_class" not in columns or not _has_composite_unique_index(conn)
    if not needs_migration:
        conn.execute(
            "CREATE INDEX IF NOT EXISTS ix_docidx_provenance ON document_index(provenance_class)"
        )
        return

    conn.execute("ALTER TABLE document_index RENAME TO document_index_legacy")
    conn.executescript(
        """
        CREATE TABLE document_index (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_hash TEXT NOT NULL,
            source_file TEXT NOT NULL,
            doc_type TEXT NOT NULL,
            module_record_id TEXT,
            extraction_timestamp TEXT,
            issuer_name TEXT,
            completeness_score REAL,
            provenance_class TEXT NOT NULL DEFAULT 'unknown',
            UNIQUE (source_hash, doc_type)
        );
        CREATE INDEX IF NOT EXISTS ix_docidx_doc_type ON document_index(doc_type);
        CREATE INDEX IF NOT EXISTS ix_docidx_issuer ON document_index(issuer_name);
        CREATE INDEX IF NOT EXISTS ix_docidx_provenance ON document_index(provenance_class);
        """
    )

    legacy_columns = {
        str(row[1] or "")
        for row in conn.execute("PRAGMA table_info(document_index_legacy)").fetchall()
    }
    has_legacy_provenance = "provenance_class" in legacy_columns
    select_sql = (
        "SELECT source_hash, source_file, doc_type, module_record_id, "
        "extraction_timestamp, issuer_name, completeness_score, provenance_class "
        "FROM document_index_legacy"
        if has_legacy_provenance
        else "SELECT source_hash, source_file, doc_type, module_record_id, "
        "extraction_timestamp, issuer_name, completeness_score, NULL FROM document_index_legacy"
    )
    for row in conn.execute(select_sql).fetchall():
        source_hash = str(row[0] or "").strip()
        source_file = str(row[1] or "").strip()
        doc_type = str(row[2] or "").strip()
        if not source_hash or not doc_type:
            continue
        provenance_class = str(row[7] or "").strip() or _infer_provenance_class(source_file)
        conn.execute(
            """
            INSERT INTO document_index (
                source_hash,
                source_file,
                doc_type,
                module_record_id,
                extraction_timestamp,
                issuer_name,
                completeness_score,
                provenance_class
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(source_hash, doc_type) DO UPDATE SET
                source_file = excluded.source_file,
                module_record_id = excluded.module_record_id,
                extraction_timestamp = excluded.extraction_timestamp,
                issuer_name = excluded.issuer_name,
                completeness_score = excluded.completeness_score,
                provenance_class = excluded.provenance_class
            """,
            (
                source_hash,
                source_file,
                doc_type,
                str(row[3] or ""),
                row[4],
                row[5],
                row[6],
                provenance_class,
            ),
        )

    conn.execute("DROP TABLE document_index_legacy")


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
    by_doc_type = dict.fromkeys(DOC_TYPE_ORDER, 0)
    seen_pairs: set[tuple[str, str]] = set()

    try:
        _ensure_document_index_schema(conn)
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
                hash_pair = (source_hash, doc_type)
                if hash_pair in seen_pairs:
                    skipped_collisions += 1
                    continue
                seen_pairs.add(hash_pair)
                source_file = str(row["source_file"] or "")
                provenance_class = _infer_provenance_class(source_file)
                conn.execute(
                    """
                    INSERT INTO document_index (
                        source_hash,
                        source_file,
                        doc_type,
                        module_record_id,
                        extraction_timestamp,
                        issuer_name,
                        completeness_score,
                        provenance_class
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(source_hash, doc_type) DO UPDATE SET
                        source_file = excluded.source_file,
                        module_record_id = excluded.module_record_id,
                        extraction_timestamp = excluded.extraction_timestamp,
                        issuer_name = excluded.issuer_name,
                        completeness_score = excluded.completeness_score,
                        provenance_class = excluded.provenance_class
                    """,
                    (
                        source_hash,
                        source_file,
                        doc_type,
                        str(row["module_record_id"] or ""),
                        row["extraction_timestamp"],
                        row["issuer_name"],
                        row["completeness_score"],
                        provenance_class,
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
