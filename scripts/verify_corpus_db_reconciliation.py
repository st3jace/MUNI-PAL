"""
Verify corpus DB reconciliation against extracted JSON inputs and document_index.

Usage:
    python scripts/verify_corpus_db_reconciliation.py
    python scripts/verify_corpus_db_reconciliation.py --sector waste
    python scripts/verify_corpus_db_reconciliation.py --fail-on-extra-db
    python scripts/verify_corpus_db_reconciliation.py --fail-on-extra-db --fail-on-index-extras --fail-on-type-mismatch
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path

DOC_TYPES = (
    "official_statement",
    "event_filing",
    "financial_report",
    "rating_action",
)

TABLE_BY_DOC_TYPE = {
    "official_statement": "documents",
    "event_filing": "event_filings",
    "financial_report": "financial_reports",
    "rating_action": "rating_actions",
}

BACKFILL_PROVENANCE_BY_MARKER = {
    "analysis/cchci_obligor_profile.json": "backfill_obligor_profile",
    "research/corpus/healthcare/healthcare_credit_drivers.json": "backfill_research_corpus",
    "risk_implementation_guide.json": "backfill_waste_feedstock",
}



_ALLOWED_SQL_IDENTIFIERS = {
    "document_index",
    "documents",
    "event_filings",
    "financial_reports",
    "rating_actions",
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
class TypeReconciliation:
    extracted_unique_hashes: int
    db_unique_hashes: int
    index_unique_hashes: int
    missing_in_db: int
    extra_in_db: int
    tolerated_backfill_extra_in_db: int
    actionable_extra_in_db: int
    missing_in_index: int
    extra_in_index: int
    type_mismatch_in_index: int


@dataclass
class SectorReconciliation:
    sector: str
    db_path: Path
    extracted_root: Path
    by_doc_type: dict[str, TypeReconciliation]
    duplicate_source_hash_rows: dict[str, int]
    orphan_rows: dict[str, int]
    parse_errors: int
    status: str
    violations: list[str]
    warnings: list[str]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _default_paths() -> dict[str, tuple[Path, Path]]:
    root = _repo_root() / "emma" / "bond_os_extractor" / "data"
    return {
        "waste": (root / "waste" / "corpus.db", root / "waste" / "extracted"),
        "healthcare": (root / "healthcare" / "corpus.db", root / "healthcare" / "extracted"),
    }


def _json_files_for_type(extracted_root: Path, *, doc_type: str) -> list[Path]:
    if doc_type == "official_statement":
        return sorted(extracted_root.glob("*.json"))
    subdir = extracted_root / doc_type
    if not subdir.exists():
        return []
    return sorted(subdir.rglob("*.json"))


def _load_extracted_hashes(extracted_root: Path) -> tuple[dict[str, set[str]], int]:
    hashes: dict[str, set[str]] = {doc_type: set() for doc_type in DOC_TYPES}
    parse_errors = 0
    for doc_type in DOC_TYPES:
        for path in _json_files_for_type(extracted_root, doc_type=doc_type):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001
                parse_errors += 1
                continue
            source_hash = str(payload.get("source_hash") or "").strip()
            if source_hash:
                hashes[doc_type].add(source_hash)
    return hashes, parse_errors


def _load_db_hashes(conn: sqlite3.Connection) -> dict[str, set[str]]:
    output: dict[str, set[str]] = {}
    for doc_type, table in TABLE_BY_DOC_TYPE.items():
        rows = conn.execute(
            f"SELECT source_hash FROM {_quote_allowed_identifier(table)} WHERE source_hash IS NOT NULL"
        ).fetchall()
        output[doc_type] = {str(row[0]).strip() for row in rows if str(row[0]).strip()}
    return output


def _load_db_rows(conn: sqlite3.Connection) -> dict[str, dict[str, str]]:
    output: dict[str, dict[str, str]] = {}
    for doc_type, table in TABLE_BY_DOC_TYPE.items():
        rows = conn.execute(
            f"SELECT source_hash, source_file FROM {_quote_allowed_identifier(table)} WHERE source_hash IS NOT NULL"
        ).fetchall()
        output[doc_type] = {
            str(row[0]).strip(): str(row[1] or "")
            for row in rows
            if str(row[0]).strip()
        }
    return output


def _table_has_column(conn: sqlite3.Connection, table_name: str, column: str) -> bool:
    rows = conn.execute(f"PRAGMA table_info({_quote_allowed_identifier(table_name)})").fetchall()
    return any(str(row[1] or "").strip() == column for row in rows)


def _has_composite_unique_index(conn: sqlite3.Connection) -> bool:
    rows = conn.execute("PRAGMA index_list(document_index)").fetchall()
    for row in rows:
        index_name = str(row[1] or "")
        is_unique = int(row[2] or 0) == 1
        if not index_name or not is_unique:
            continue
        columns = [
            str(col_row[2] or "")
            for col_row in conn.execute(f"PRAGMA index_info({_quote_allowed_identifier(index_name)})").fetchall()
        ]
        if columns == ["source_hash", "doc_type"]:
            return True
    return False


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


def _load_index_hashes_and_provenance(
    conn: sqlite3.Connection,
) -> tuple[dict[str, set[str]], dict[str, dict[str, str]]]:
    output_hashes: dict[str, set[str]] = {doc_type: set() for doc_type in DOC_TYPES}
    output_provenance: dict[str, dict[str, str]] = {doc_type: {} for doc_type in DOC_TYPES}
    has_provenance = _table_has_column(conn, "document_index", "provenance_class")
    select_sql = (
        "SELECT doc_type, source_hash, source_file, provenance_class "
        "FROM document_index WHERE source_hash IS NOT NULL"
        if has_provenance
        else "SELECT doc_type, source_hash, source_file, NULL "
        "FROM document_index WHERE source_hash IS NOT NULL"
    )
    rows = conn.execute(select_sql).fetchall()
    for row in rows:
        doc_type = str(row[0] or "").strip()
        source_hash = str(row[1] or "").strip()
        source_file = str(row[2] or "")
        if doc_type in output_hashes and source_hash:
            output_hashes[doc_type].add(source_hash)
            provenance_class = str(row[3] or "").strip() or _infer_provenance_class(source_file)
            output_provenance[doc_type][source_hash] = provenance_class
    return output_hashes, output_provenance


def _duplicate_counts(conn: sqlite3.Connection) -> dict[str, int]:
    output: dict[str, int] = {}
    for doc_type, table in TABLE_BY_DOC_TYPE.items():
        dup_count = conn.execute(
            f"""
            SELECT COUNT(*) FROM (
                SELECT source_hash
                FROM {_quote_allowed_identifier(table)}
                WHERE source_hash IS NOT NULL
                GROUP BY source_hash
                HAVING COUNT(*) > 1
            )
            """
        ).fetchone()[0]
        output[doc_type] = int(dup_count)
    return output


def _orphan_counts(conn: sqlite3.Connection) -> dict[str, int]:
    return {
        "deal_identities_without_documents": int(
            conn.execute(
                """
                SELECT COUNT(*)
                FROM deal_identities di
                LEFT JOIN documents d ON d.id = di.document_id
                WHERE d.id IS NULL
                """
            ).fetchone()[0]
        ),
        "deal_structures_without_documents": int(
            conn.execute(
                """
                SELECT COUNT(*)
                FROM deal_structures ds
                LEFT JOIN documents d ON d.id = ds.document_id
                WHERE d.id IS NULL
                """
            ).fetchone()[0]
        ),
        "risk_factors_without_documents": int(
            conn.execute(
                """
                SELECT COUNT(*)
                FROM risk_factors rf
                LEFT JOIN documents d ON d.id = rf.document_id
                WHERE d.id IS NULL
                """
            ).fetchone()[0]
        ),
        "security_packages_without_documents": int(
            conn.execute(
                """
                SELECT COUNT(*)
                FROM security_packages sp
                LEFT JOIN documents d ON d.id = sp.document_id
                WHERE d.id IS NULL
                """
            ).fetchone()[0]
        ),
    }


def evaluate_sector(
    *,
    sector: str,
    db_path: Path,
    extracted_root: Path,
    require_extracted: bool,
    fail_on_extra_db: bool,
    fail_on_index_extras: bool,
    fail_on_type_mismatch: bool = False,
    allow_backfill_extra_db: bool = True,
) -> SectorReconciliation:
    violations: list[str] = []
    warnings: list[str] = []
    extracted_available = extracted_root.exists()

    if not db_path.exists():
        return SectorReconciliation(
            sector=sector,
        db_path=db_path,
        extracted_root=extracted_root,
        by_doc_type={},
            duplicate_source_hash_rows={},
            orphan_rows={},
            parse_errors=0,
            status="fail",
            violations=[f"Missing DB: {db_path.as_posix()}"],
            warnings=[],
        )
    if extracted_available:
        extracted_hashes, parse_errors = _load_extracted_hashes(extracted_root)
    else:
        extracted_hashes = {doc_type: set() for doc_type in DOC_TYPES}
        parse_errors = 0
        message = f"Missing extracted root: {extracted_root.as_posix()}"
        if require_extracted:
            violations.append(message)
        else:
            warnings.append(message)
            warnings.append(
                "Skipping extracted-vs-DB delta checks because extracted root is unavailable."
            )

    conn = sqlite3.connect(db_path)
    try:
        db_rows = _load_db_rows(conn)
        db_hashes = _load_db_hashes(conn)
        index_hashes, index_provenance = _load_index_hashes_and_provenance(conn)
        has_provenance_column = _table_has_column(conn, "document_index", "provenance_class")
        has_composite_key = _has_composite_unique_index(conn)
        duplicate_counts = _duplicate_counts(conn)
        orphan_counts = _orphan_counts(conn)
    finally:
        conn.close()

    if not has_composite_key:
        violations.append(
            "document_index schema missing UNIQUE(source_hash, doc_type) normalization key."
        )
    if not has_provenance_column:
        violations.append(
            "document_index schema missing provenance_class column for backfill provenance tagging."
        )

    if parse_errors:
        warnings.append(f"{parse_errors} extracted JSON files could not be parsed.")

    by_doc_type: dict[str, TypeReconciliation] = {}

    for doc_type in DOC_TYPES:
        extracted_set = extracted_hashes.get(doc_type, set()) if extracted_available else set()
        db_set = db_hashes.get(doc_type, set())
        index_set = index_hashes.get(doc_type, set())

        missing_in_db = (extracted_set - db_set) if extracted_available else set()
        extra_in_db = (db_set - extracted_set) if extracted_available else set()
        missing_in_index = db_set - index_set
        extra_in_index = index_set - db_set

        type_mismatch_in_index_set: set[str] = set()
        for source_hash in missing_in_index:
            for other_doc_type in DOC_TYPES:
                if other_doc_type == doc_type:
                    continue
                if source_hash in index_hashes.get(other_doc_type, set()):
                    type_mismatch_in_index_set.add(source_hash)
                    break
        missing_in_index_exact = missing_in_index - type_mismatch_in_index_set

        tolerated_backfill_extra_in_db = 0
        actionable_extra_in_db = 0
        for source_hash in extra_in_db:
            source_file = db_rows.get(doc_type, {}).get(source_hash, "")
            provenance_class = index_provenance.get(doc_type, {}).get(source_hash) or _infer_provenance_class(
                source_file
            )
            if allow_backfill_extra_db and provenance_class.startswith("backfill_"):
                tolerated_backfill_extra_in_db += 1
            else:
                actionable_extra_in_db += 1

        by_doc_type[doc_type] = TypeReconciliation(
            extracted_unique_hashes=len(extracted_set),
            db_unique_hashes=len(db_set),
            index_unique_hashes=len(index_set),
            missing_in_db=len(missing_in_db),
            extra_in_db=len(extra_in_db),
            tolerated_backfill_extra_in_db=tolerated_backfill_extra_in_db,
            actionable_extra_in_db=actionable_extra_in_db,
            missing_in_index=len(missing_in_index),
            extra_in_index=len(extra_in_index),
            type_mismatch_in_index=len(type_mismatch_in_index_set),
        )

        if missing_in_db:
            violations.append(
                f"{doc_type}: {len(missing_in_db)} extracted hashes missing in DB."
            )
        if missing_in_index_exact:
            violations.append(
                f"{doc_type}: {len(missing_in_index_exact)} DB hashes missing in document_index."
            )
        if actionable_extra_in_db:
            message = (
                f"{doc_type}: {actionable_extra_in_db} DB hashes not found in extracted JSON "
                "(actionable)."
            )
            if fail_on_extra_db:
                violations.append(message)
            else:
                warnings.append(message)
        if extra_in_index:
            message = f"{doc_type}: {len(extra_in_index)} index hashes not found in source table."
            if fail_on_index_extras:
                violations.append(message)
            else:
                warnings.append(message)
        if type_mismatch_in_index_set:
            message = (
                f"{doc_type}: {len(type_mismatch_in_index_set)} DB hashes are indexed under a "
                "different doc_type."
            )
            if fail_on_type_mismatch:
                violations.append(message)
            else:
                warnings.append(message)

    for doc_type, dup_count in duplicate_counts.items():
        if dup_count > 0:
            violations.append(f"{doc_type}: duplicate source_hash groups={dup_count}.")

    for orphan_name, orphan_count in orphan_counts.items():
        if orphan_count > 0:
            violations.append(f"{orphan_name}: orphan rows={orphan_count}.")

    status = "pass" if not violations else "fail"
    return SectorReconciliation(
        sector=sector,
        db_path=db_path,
        extracted_root=extracted_root,
        by_doc_type=by_doc_type,
        duplicate_source_hash_rows=duplicate_counts,
        orphan_rows=orphan_counts,
        parse_errors=parse_errors,
        status=status,
        violations=violations,
        warnings=warnings,
    )


def evaluate_all(
    *,
    sectors: list[str] | None,
    require_extracted: bool,
    fail_on_extra_db: bool,
    fail_on_index_extras: bool,
    fail_on_type_mismatch: bool,
    allow_backfill_extra_db: bool,
) -> list[SectorReconciliation]:
    paths = _default_paths()
    selected = sectors or list(paths.keys())
    results: list[SectorReconciliation] = []
    for sector in selected:
        if sector not in paths:
            raise ValueError(f"Unsupported sector `{sector}`. Available: {sorted(paths)}")
        db_path, extracted_root = paths[sector]
        results.append(
            evaluate_sector(
                sector=sector,
                db_path=db_path,
                extracted_root=extracted_root,
                require_extracted=require_extracted,
                fail_on_extra_db=fail_on_extra_db,
                fail_on_index_extras=fail_on_index_extras,
                fail_on_type_mismatch=fail_on_type_mismatch,
                allow_backfill_extra_db=allow_backfill_extra_db,
            )
        )
    return results


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Verify corpus DB source-hash reconciliation and document_index coverage.",
    )
    parser.add_argument(
        "--sector",
        action="append",
        default=None,
        help="Sector to verify (repeatable). Defaults to all sectors.",
    )
    parser.add_argument(
        "--require-extracted",
        action="store_true",
        help="Fail when extracted JSON roots are missing. Without this flag, extracted-vs-DB deltas are skipped when roots are absent.",
    )
    parser.add_argument(
        "--fail-on-extra-db",
        action="store_true",
        help="Fail when DB contains hashes not found in extracted JSON.",
    )
    parser.add_argument(
        "--fail-on-index-extras",
        action="store_true",
        help="Fail when document_index contains hashes not found in source tables.",
    )
    parser.add_argument(
        "--fail-on-type-mismatch",
        action="store_true",
        help="Fail when a DB hash is indexed only under a different doc_type.",
    )
    parser.add_argument(
        "--no-allow-backfill-extra-db",
        action="store_true",
        help="Treat backfill-only DB hashes missing from extracted JSON as actionable.",
    )
    return parser


def _print_result(result: SectorReconciliation) -> None:
    print(
        "[corpus-reconciliation] "
        f"sector={result.sector} status={result.status} "
        f"parse_errors={result.parse_errors}"
    )
    for doc_type in DOC_TYPES:
        row = result.by_doc_type.get(doc_type)
        if row is None:
            continue
        print(
            "[corpus-reconciliation] "
            f"sector={result.sector} doc_type={doc_type} "
            f"extracted={row.extracted_unique_hashes} db={row.db_unique_hashes} "
            f"index={row.index_unique_hashes} "
            f"missing_in_db={row.missing_in_db} extra_in_db={row.extra_in_db} "
            f"backfill_extra_in_db={row.tolerated_backfill_extra_in_db} "
            f"actionable_extra_in_db={row.actionable_extra_in_db} "
            f"missing_in_index={row.missing_in_index} extra_in_index={row.extra_in_index} "
            f"type_mismatch_in_index={row.type_mismatch_in_index}"
        )
    if result.violations:
        print(f"[corpus-reconciliation] sector={result.sector} violations:")
        for violation in result.violations:
            print(f"- {violation}")
    if result.warnings:
        print(f"[corpus-reconciliation] sector={result.sector} warnings:")
        for warning in result.warnings:
            print(f"- {warning}")


def main() -> int:
    args = _build_parser().parse_args()
    results = evaluate_all(
        sectors=args.sector,
        require_extracted=bool(args.require_extracted),
        fail_on_extra_db=bool(args.fail_on_extra_db),
        fail_on_index_extras=bool(args.fail_on_index_extras),
        fail_on_type_mismatch=bool(args.fail_on_type_mismatch),
        allow_backfill_extra_db=not bool(args.no_allow_backfill_extra_db),
    )
    for result in results:
        _print_result(result)
    return 0 if all(result.status == "pass" for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
