import sqlite3
from pathlib import Path

from scripts.rebuild_corpus_document_index import rebuild_document_index


def _init_db(path: Path) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.executescript(
            """
            CREATE TABLE documents (
                id TEXT PRIMARY KEY,
                source_hash TEXT UNIQUE,
                source_file TEXT,
                extraction_timestamp TEXT,
                completeness_score REAL
            );
            CREATE TABLE deal_identities (
                document_id TEXT PRIMARY KEY,
                issuer_name TEXT
            );
            CREATE TABLE event_filings (
                id TEXT PRIMARY KEY,
                source_hash TEXT UNIQUE,
                source_file TEXT,
                extraction_timestamp TEXT,
                issuer_name TEXT,
                completeness_score REAL
            );
            CREATE TABLE financial_reports (
                id TEXT PRIMARY KEY,
                source_hash TEXT UNIQUE,
                source_file TEXT,
                extraction_timestamp TEXT,
                issuer_name TEXT,
                completeness_score REAL
            );
            CREATE TABLE rating_actions (
                id TEXT PRIMARY KEY,
                source_hash TEXT UNIQUE,
                source_file TEXT,
                extraction_timestamp TEXT,
                issuer_name TEXT,
                completeness_score REAL
            );
            CREATE TABLE document_index (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_hash TEXT UNIQUE,
                source_file TEXT,
                doc_type TEXT,
                module_record_id TEXT,
                extraction_timestamp TEXT,
                issuer_name TEXT,
                completeness_score REAL
            );
            """
        )
        conn.commit()
    finally:
        conn.close()


def test_rebuild_document_index_populates_all_doc_types(tmp_path: Path) -> None:
    db_path = tmp_path / "corpus.db"
    _init_db(db_path)

    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT INTO documents (id, source_hash, source_file, extraction_timestamp, completeness_score) "
            "VALUES ('doc1', 'h-doc1', 'os1.pdf', '2026-02-20T00:00:00Z', 0.91)"
        )
        conn.execute(
            "INSERT INTO deal_identities (document_id, issuer_name) VALUES ('doc1', 'Issuer A')"
        )
        conn.execute(
            "INSERT INTO documents (id, source_hash, source_file, extraction_timestamp, completeness_score) "
            "VALUES ('doc2', 'h-doc2', 'os2.pdf', '2026-02-21T00:00:00Z', 0.89)"
        )
        conn.execute(
            "INSERT INTO event_filings (id, source_hash, source_file, extraction_timestamp, issuer_name, completeness_score) "
            "VALUES ('ef1', 'h-ef1', 'ef1.pdf', '2026-02-21T01:00:00Z', 'Issuer EF', 0.80)"
        )
        conn.execute(
            "INSERT INTO financial_reports (id, source_hash, source_file, extraction_timestamp, issuer_name, completeness_score) "
            "VALUES ('fr1', 'h-fr1', 'fr1.pdf', '2026-02-21T02:00:00Z', 'Issuer FR', 0.83)"
        )
        conn.execute(
            "INSERT INTO rating_actions (id, source_hash, source_file, extraction_timestamp, issuer_name, completeness_score) "
            "VALUES ('ra1', 'h-ra1', 'ra1.pdf', '2026-02-21T03:00:00Z', 'Issuer RA', 0.88)"
        )
        conn.commit()
    finally:
        conn.close()

    summary = rebuild_document_index(
        sector="test",
        db_path=db_path,
        clear_existing=True,
    )

    assert summary.indexed_rows == 5
    assert summary.skipped_collisions == 0
    assert summary.index_count_after == 5
    assert summary.by_doc_type["official_statement"] == 2
    assert summary.by_doc_type["event_filing"] == 1
    assert summary.by_doc_type["financial_report"] == 1
    assert summary.by_doc_type["rating_action"] == 1


def test_rebuild_document_index_prefers_official_statement_on_hash_collision(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "corpus.db"
    _init_db(db_path)

    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT INTO documents (id, source_hash, source_file, extraction_timestamp, completeness_score) "
            "VALUES ('doc1', 'h-shared', 'os1.pdf', '2026-02-20T00:00:00Z', 0.91)"
        )
        conn.execute(
            "INSERT INTO rating_actions (id, source_hash, source_file, extraction_timestamp, issuer_name, completeness_score) "
            "VALUES ('ra1', 'h-shared', 'ra1.pdf', '2026-02-21T03:00:00Z', 'Issuer RA', 0.88)"
        )
        conn.commit()
    finally:
        conn.close()

    summary = rebuild_document_index(
        sector="test",
        db_path=db_path,
        clear_existing=True,
    )

    assert summary.indexed_rows == 2
    assert summary.skipped_collisions == 0
    assert summary.by_doc_type["official_statement"] == 1
    assert summary.by_doc_type["rating_action"] == 1

    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            "SELECT doc_type, module_record_id FROM document_index "
            "WHERE source_hash = 'h-shared' ORDER BY doc_type"
        ).fetchall()
    finally:
        conn.close()

    assert rows == [
        ("official_statement", "doc1"),
        ("rating_action", "ra1"),
    ]


def test_rebuild_document_index_migrates_legacy_schema_and_sets_provenance(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "corpus.db"
    _init_db(db_path)

    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT INTO documents (id, source_hash, source_file, extraction_timestamp, completeness_score) "
            "VALUES ('doc1', 'h-backfill', "
            "'C:/repo/research/corpus/healthcare/healthcare_credit_drivers.json#hospital_revenue_bonds', "
            "'2026-02-21T00:00:00Z', 0.75)"
        )
        conn.commit()
    finally:
        conn.close()

    summary = rebuild_document_index(
        sector="test",
        db_path=db_path,
        clear_existing=True,
    )
    assert summary.indexed_rows == 1

    conn = sqlite3.connect(db_path)
    try:
        columns = [
            row[1]
            for row in conn.execute("PRAGMA table_info(document_index)").fetchall()
        ]
        unique_indexes = conn.execute("PRAGMA index_list(document_index)").fetchall()
        row = conn.execute(
            "SELECT provenance_class FROM document_index "
            "WHERE source_hash = 'h-backfill' AND doc_type = 'official_statement'"
        ).fetchone()
    finally:
        conn.close()

    assert "provenance_class" in columns
    assert any(int(index_row[2]) == 1 for index_row in unique_indexes)
    assert row is not None
    assert row[0] == "backfill_research_corpus"
