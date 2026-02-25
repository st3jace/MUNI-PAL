import json
import sqlite3
from pathlib import Path

from scripts.verify_corpus_db_reconciliation import evaluate_sector


def _init_db(path: Path) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.executescript(
            """
            CREATE TABLE documents (
                id TEXT PRIMARY KEY,
                source_hash TEXT UNIQUE,
                source_file TEXT
            );
            CREATE TABLE event_filings (
                id TEXT PRIMARY KEY,
                source_hash TEXT UNIQUE,
                source_file TEXT
            );
            CREATE TABLE financial_reports (
                id TEXT PRIMARY KEY,
                source_hash TEXT UNIQUE,
                source_file TEXT
            );
            CREATE TABLE rating_actions (
                id TEXT PRIMARY KEY,
                source_hash TEXT UNIQUE,
                source_file TEXT
            );
            CREATE TABLE document_index (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_hash TEXT NOT NULL,
                source_file TEXT,
                doc_type TEXT,
                module_record_id TEXT,
                extraction_timestamp TEXT,
                issuer_name TEXT,
                completeness_score REAL,
                provenance_class TEXT NOT NULL DEFAULT 'unknown',
                UNIQUE (source_hash, doc_type)
            );
            CREATE TABLE deal_identities (document_id TEXT PRIMARY KEY);
            CREATE TABLE deal_structures (document_id TEXT PRIMARY KEY);
            CREATE TABLE risk_factors (id INTEGER PRIMARY KEY AUTOINCREMENT, document_id TEXT);
            CREATE TABLE security_packages (document_id TEXT PRIMARY KEY);
            """
        )
        conn.commit()
    finally:
        conn.close()


def _write_json(path: Path, source_hash: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"source_hash": source_hash}, indent=2), encoding="utf-8")


def _populate_matching_data(db_path: Path, extracted_root: Path) -> None:
    _write_json(extracted_root / "os1.json", "h-os1")
    _write_json(extracted_root / "event_filing" / "ef1.json", "h-ef1")
    _write_json(extracted_root / "financial_report" / "fr1.json", "h-fr1")
    _write_json(extracted_root / "rating_action" / "ra1.json", "h-ra1")

    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT INTO documents (id, source_hash, source_file) VALUES ('doc1', 'h-os1', 'os1.pdf')"
        )
        conn.execute(
            "INSERT INTO event_filings (id, source_hash, source_file) VALUES ('ef1', 'h-ef1', 'ef1.pdf')"
        )
        conn.execute(
            "INSERT INTO financial_reports (id, source_hash, source_file) VALUES ('fr1', 'h-fr1', 'fr1.pdf')"
        )
        conn.execute(
            "INSERT INTO rating_actions (id, source_hash, source_file) VALUES ('ra1', 'h-ra1', 'ra1.pdf')"
        )
        conn.execute(
            "INSERT INTO document_index (source_hash, source_file, doc_type, module_record_id) "
            "VALUES ('h-os1', 'os1.pdf', 'official_statement', 'doc1')"
        )
        conn.execute(
            "INSERT INTO document_index (source_hash, source_file, doc_type, module_record_id) "
            "VALUES ('h-ef1', 'ef1.pdf', 'event_filing', 'ef1')"
        )
        conn.execute(
            "INSERT INTO document_index (source_hash, source_file, doc_type, module_record_id) "
            "VALUES ('h-fr1', 'fr1.pdf', 'financial_report', 'fr1')"
        )
        conn.execute(
            "INSERT INTO document_index (source_hash, source_file, doc_type, module_record_id) "
            "VALUES ('h-ra1', 'ra1.pdf', 'rating_action', 'ra1')"
        )
        conn.commit()
    finally:
        conn.close()


def test_reconciliation_passes_when_hashes_and_index_match(tmp_path: Path) -> None:
    db_path = tmp_path / "corpus.db"
    extracted_root = tmp_path / "extracted"
    _init_db(db_path)
    _populate_matching_data(db_path, extracted_root)

    result = evaluate_sector(
        sector="test",
        db_path=db_path,
        extracted_root=extracted_root,
        require_extracted=True,
        fail_on_extra_db=False,
        fail_on_index_extras=False,
    )

    assert result.status == "pass"
    assert result.violations == []
    assert result.by_doc_type["official_statement"].missing_in_db == 0
    assert result.by_doc_type["official_statement"].missing_in_index == 0


def test_reconciliation_fails_when_index_missing_db_hash(tmp_path: Path) -> None:
    db_path = tmp_path / "corpus.db"
    extracted_root = tmp_path / "extracted"
    _init_db(db_path)
    _populate_matching_data(db_path, extracted_root)

    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "DELETE FROM document_index WHERE source_hash = 'h-ra1' AND doc_type = 'rating_action'"
        )
        conn.commit()
    finally:
        conn.close()

    result = evaluate_sector(
        sector="test",
        db_path=db_path,
        extracted_root=extracted_root,
        require_extracted=True,
        fail_on_extra_db=False,
        fail_on_index_extras=False,
    )

    assert result.status == "fail"
    assert any("rating_action" in message for message in result.violations)
    assert result.by_doc_type["rating_action"].missing_in_index == 1


def test_reconciliation_can_fail_on_extra_db_hashes(tmp_path: Path) -> None:
    db_path = tmp_path / "corpus.db"
    extracted_root = tmp_path / "extracted"
    _init_db(db_path)
    _populate_matching_data(db_path, extracted_root)

    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT INTO documents (id, source_hash, source_file) VALUES ('doc-extra', 'h-extra', 'extra.pdf')"
        )
        conn.execute(
            "INSERT INTO document_index (source_hash, source_file, doc_type, module_record_id) "
            "VALUES ('h-extra', 'extra.pdf', 'official_statement', 'doc-extra')"
        )
        conn.commit()
    finally:
        conn.close()

    warning_result = evaluate_sector(
        sector="test",
        db_path=db_path,
        extracted_root=extracted_root,
        require_extracted=True,
        fail_on_extra_db=False,
        fail_on_index_extras=False,
    )
    assert warning_result.status == "pass"
    assert any("not found in extracted JSON" in message for message in warning_result.warnings)

    strict_result = evaluate_sector(
        sector="test",
        db_path=db_path,
        extracted_root=extracted_root,
        require_extracted=True,
        fail_on_extra_db=True,
        fail_on_index_extras=False,
    )
    assert strict_result.status == "fail"
    assert any("not found in extracted JSON" in message for message in strict_result.violations)


def test_reconciliation_warns_when_extracted_root_missing_without_strict_mode(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "corpus.db"
    extracted_root = tmp_path / "missing-extracted"
    _init_db(db_path)

    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT INTO documents (id, source_hash, source_file) VALUES ('doc1', 'h-os1', 'os1.pdf')"
        )
        conn.execute(
            "INSERT INTO document_index (source_hash, source_file, doc_type, module_record_id) "
            "VALUES ('h-os1', 'os1.pdf', 'official_statement', 'doc1')"
        )
        conn.commit()
    finally:
        conn.close()

    result = evaluate_sector(
        sector="test",
        db_path=db_path,
        extracted_root=extracted_root,
        require_extracted=False,
        fail_on_extra_db=False,
        fail_on_index_extras=False,
    )

    assert result.status == "pass"
    assert any("Missing extracted root" in warning for warning in result.warnings)


def test_reconciliation_tolerates_backfill_extra_hashes_in_strict_mode(tmp_path: Path) -> None:
    db_path = tmp_path / "corpus.db"
    extracted_root = tmp_path / "extracted"
    _init_db(db_path)
    _populate_matching_data(db_path, extracted_root)

    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT INTO documents (id, source_hash, source_file) VALUES "
            "('doc-backfill', 'h-backfill', "
            "'C:/repo/research/corpus/healthcare/healthcare_credit_drivers.json#hospital_revenue_bonds')"
        )
        conn.execute(
            "INSERT INTO document_index (source_hash, source_file, doc_type, module_record_id, provenance_class) "
            "VALUES ('h-backfill', "
            "'C:/repo/research/corpus/healthcare/healthcare_credit_drivers.json#hospital_revenue_bonds', "
            "'official_statement', 'doc-backfill', 'backfill_research_corpus')"
        )
        conn.commit()
    finally:
        conn.close()

    tolerated_result = evaluate_sector(
        sector="test",
        db_path=db_path,
        extracted_root=extracted_root,
        require_extracted=True,
        fail_on_extra_db=True,
        fail_on_index_extras=True,
        fail_on_type_mismatch=True,
        allow_backfill_extra_db=True,
    )
    assert tolerated_result.status == "pass"
    assert tolerated_result.by_doc_type["official_statement"].tolerated_backfill_extra_in_db == 1
    assert tolerated_result.by_doc_type["official_statement"].actionable_extra_in_db == 0

    strict_result = evaluate_sector(
        sector="test",
        db_path=db_path,
        extracted_root=extracted_root,
        require_extracted=True,
        fail_on_extra_db=True,
        fail_on_index_extras=True,
        fail_on_type_mismatch=True,
        allow_backfill_extra_db=False,
    )
    assert strict_result.status == "fail"
    assert strict_result.by_doc_type["official_statement"].actionable_extra_in_db == 1
