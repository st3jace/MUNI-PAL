"""
Verify Phase 10 corpus database prerequisites before bundle execution.

Usage:
    python scripts/verify_phase10_corpus_prereqs.py
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

REQUIRED_TABLES = (
    "documents",
    "deal_structures",
    "risk_factors",
    "security_packages",
    "financial_reports",
    "rating_actions",
    "classifications",
)

MIN_ROWS = {
    "documents": 1,
    "risk_factors": 1,
}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _sector_dbs() -> dict[str, Path]:
    root = _repo_root() / "emma" / "bond_os_extractor" / "data"
    return {
        "waste": root / "waste" / "corpus.db",
        "healthcare": root / "healthcare" / "corpus.db",
    }


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    ).fetchone()
    return row is not None


def _count_rows(conn: sqlite3.Connection, table: str) -> int:
    row = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
    return int(row[0]) if row else 0


def main() -> int:
    failures: list[str] = []
    for sector, db_path in _sector_dbs().items():
        if not db_path.exists():
            failures.append(
                f"{sector}: missing DB at {db_path.as_posix()}. "
                "Run `python scripts/provision_phase10_corpus_dbs.py` first."
            )
            continue

        try:
            conn = sqlite3.connect(db_path)
        except sqlite3.Error as exc:
            failures.append(f"{sector}: failed to open DB `{db_path.as_posix()}` ({exc}).")
            continue

        try:
            missing_tables = [table for table in REQUIRED_TABLES if not _table_exists(conn, table)]
            if missing_tables:
                failures.append(
                    f"{sector}: missing required tables {missing_tables} in `{db_path.as_posix()}`."
                )
                continue

            counts = {table: _count_rows(conn, table) for table in REQUIRED_TABLES}
            too_small = [
                f"{table}={counts[table]}<{MIN_ROWS[table]}"
                for table in MIN_ROWS
                if counts.get(table, 0) < MIN_ROWS[table]
            ]
            if too_small:
                failures.append(
                    f"{sector}: DB is present but under-populated ({', '.join(too_small)})."
                )
            else:
                print(
                    "[phase10-corpus-preflight] "
                    f"sector={sector} db={db_path.as_posix()} "
                    f"documents={counts['documents']} risk_factors={counts['risk_factors']}"
                )
        finally:
            conn.close()

    if failures:
        print("[phase10-corpus-preflight] status=fail")
        print("[phase10-corpus-preflight] failures:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("[phase10-corpus-preflight] status=pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
