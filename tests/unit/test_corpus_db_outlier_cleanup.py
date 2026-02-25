import sqlite3
from pathlib import Path

from scripts.cleanup_corpus_db_outliers import cleanup_sector


def _init_db(path: Path) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.executescript(
            """
            CREATE TABLE documents (id TEXT PRIMARY KEY, source_hash TEXT UNIQUE, source_file TEXT);
            CREATE TABLE event_filings (id TEXT PRIMARY KEY, source_hash TEXT UNIQUE, source_file TEXT);
            CREATE TABLE financial_reports (id TEXT PRIMARY KEY, source_hash TEXT UNIQUE, source_file TEXT);
            CREATE TABLE rating_actions (id TEXT PRIMARY KEY, source_hash TEXT UNIQUE, source_file TEXT);
            CREATE TABLE document_index (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_hash TEXT NOT NULL,
                source_file TEXT,
                doc_type TEXT,
                module_record_id TEXT,
                provenance_class TEXT NOT NULL DEFAULT 'unknown',
                UNIQUE (source_hash, doc_type)
            );
            """
        )
        conn.execute(
            "INSERT INTO rating_actions (id, source_hash, source_file) VALUES ('ra1', 'abc123', 'test.pdf')"
        )
        conn.execute(
            "INSERT INTO documents (id, source_hash, source_file) VALUES ('doc1', 'h-real', 'real.pdf')"
        )
        conn.execute(
            "INSERT INTO document_index (source_hash, source_file, doc_type, module_record_id) "
            "VALUES ('abc123', 'test.pdf', 'rating_action', 'ra1')"
        )
        conn.execute(
            "INSERT INTO document_index (source_hash, source_file, doc_type, module_record_id) "
            "VALUES ('h-real', 'real.pdf', 'official_statement', 'doc1')"
        )
        conn.commit()
    finally:
        conn.close()


def test_cleanup_sector_removes_test_fixture_rows(tmp_path: Path) -> None:
    db_path = tmp_path / "corpus.db"
    _init_db(db_path)

    summary = cleanup_sector(sector="test", db_path=db_path)

    assert summary.removed_rows["rating_actions"] == 1
    assert summary.removed_rows["document_index"] == 1

    conn = sqlite3.connect(db_path)
    try:
        remaining_ra = conn.execute("SELECT COUNT(*) FROM rating_actions").fetchone()[0]
        remaining_index = conn.execute(
            "SELECT COUNT(*) FROM document_index WHERE source_hash='h-real'"
        ).fetchone()[0]
    finally:
        conn.close()

    assert remaining_ra == 0
    assert remaining_index == 1

