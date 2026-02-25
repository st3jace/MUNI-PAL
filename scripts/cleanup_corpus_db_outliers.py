"""
Remove known non-production outlier rows from Phase 10 corpus DBs.

Usage:
    python scripts/cleanup_corpus_db_outliers.py
    python scripts/cleanup_corpus_db_outliers.py --sector waste
"""

from __future__ import annotations

import argparse
import sqlite3
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CleanupSummary:
    sector: str
    db_path: Path
    removed_rows: dict[str, int]


SOURCE_TABLES = (
    "documents",
    "event_filings",
    "financial_reports",
    "rating_actions",
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _default_sector_db_map() -> dict[str, Path]:
    root = _repo_root() / "emma" / "bond_os_extractor" / "data"
    return {
        "waste": root / "waste" / "corpus.db",
        "healthcare": root / "healthcare" / "corpus.db",
    }


def _delete_test_fixture_rows(conn: sqlite3.Connection) -> dict[str, int]:
    removed: dict[str, int] = {}
    for table in SOURCE_TABLES:
        cursor = conn.execute(
            f"""
            DELETE FROM {table}
            WHERE LOWER(COALESCE(source_file, '')) = 'test.pdf'
               OR source_hash = 'abc123'
            """
        )
        removed[table] = int(cursor.rowcount or 0)
    cursor = conn.execute(
        """
        DELETE FROM document_index
        WHERE LOWER(COALESCE(source_file, '')) = 'test.pdf'
           OR source_hash = 'abc123'
        """
    )
    removed["document_index"] = int(cursor.rowcount or 0)
    return removed


def cleanup_sector(*, sector: str, db_path: Path) -> CleanupSummary:
    if not db_path.exists():
        raise FileNotFoundError(f"Corpus DB not found for sector `{sector}`: {db_path.as_posix()}")
    conn = sqlite3.connect(db_path)
    try:
        removed_rows = _delete_test_fixture_rows(conn)
        conn.commit()
    finally:
        conn.close()
    return CleanupSummary(sector=sector, db_path=db_path, removed_rows=removed_rows)


def cleanup_all(*, sectors: list[str] | None) -> list[CleanupSummary]:
    sector_db_map = _default_sector_db_map()
    selected_sectors = sectors or list(sector_db_map.keys())
    summaries: list[CleanupSummary] = []
    for sector in selected_sectors:
        if sector not in sector_db_map:
            raise ValueError(f"Unsupported sector `{sector}`. Available: {sorted(sector_db_map)}")
        summaries.append(cleanup_sector(sector=sector, db_path=sector_db_map[sector]))
    return summaries


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Remove known outlier rows from corpus DBs.")
    parser.add_argument(
        "--sector",
        action="append",
        default=None,
        help="Sector to clean (repeatable). Defaults to all sectors.",
    )
    return parser


def _format_summary(summary: CleanupSummary) -> str:
    counts = ", ".join(f"{table}={count}" for table, count in summary.removed_rows.items())
    return (
        "[corpus-outlier-cleanup] "
        f"sector={summary.sector} "
        f"db={summary.db_path.as_posix()} "
        f"removed={{ {counts} }}"
    )


def main() -> int:
    args = _build_parser().parse_args()
    summaries = cleanup_all(sectors=args.sector)
    for summary in summaries:
        print(_format_summary(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

