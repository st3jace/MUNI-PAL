"""
Verify corpus DB reconciliation against extracted JSON inputs and document_index.

Usage:
    python scripts/verify_corpus_db_reconciliation.py
    python scripts/verify_corpus_db_reconciliation.py --sector waste
    python scripts/verify_corpus_db_reconciliation.py --fail-on-extra-db
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


@dataclass
class TypeReconciliation:
    extracted_unique_hashes: int
    db_unique_hashes: int
    index_unique_hashes: int
    missing_in_db: int
    extra_in_db: int
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
            f"SELECT source_hash FROM {table} WHERE source_hash IS NOT NULL"
        ).fetchall()
        output[doc_type] = {str(row[0]).strip() for row in rows if str(row[0]).strip()}
    return output


def _load_index_hashes(conn: sqlite3.Connection) -> dict[str, set[str]]:
    output: dict[str, set[str]] = {doc_type: set() for doc_type in DOC_TYPES}
    rows = conn.execute(
        "SELECT doc_type, source_hash FROM document_index WHERE source_hash IS NOT NULL"
    ).fetchall()
    for row in rows:
        doc_type = str(row[0] or "").strip()
        source_hash = str(row[1] or "").strip()
        if doc_type in output and source_hash:
            output[doc_type].add(source_hash)
    return output


def _duplicate_counts(conn: sqlite3.Connection) -> dict[str, int]:
    output: dict[str, int] = {}
    for doc_type, table in TABLE_BY_DOC_TYPE.items():
        dup_count = conn.execute(
            f"""
            SELECT COUNT(*) FROM (
                SELECT source_hash
                FROM {table}
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
) -> SectorReconciliation:
    violations: list[str] = []
    warnings: list[str] = []

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
    if extracted_root.exists():
        extracted_hashes, parse_errors = _load_extracted_hashes(extracted_root)
    else:
        extracted_hashes = {doc_type: set() for doc_type in DOC_TYPES}
        parse_errors = 0
        message = f"Missing extracted root: {extracted_root.as_posix()}"
        if require_extracted:
            violations.append(message)
        else:
            warnings.append(message)

    conn = sqlite3.connect(db_path)
    try:
        db_hashes = _load_db_hashes(conn)
        index_hashes = _load_index_hashes(conn)
        duplicate_counts = _duplicate_counts(conn)
        orphan_counts = _orphan_counts(conn)
    finally:
        conn.close()

    if parse_errors:
        warnings.append(f"{parse_errors} extracted JSON files could not be parsed.")

    by_doc_type: dict[str, TypeReconciliation] = {}
    db_union: set[str] = set()
    index_union: set[str] = set()
    for doc_type in DOC_TYPES:
        db_union |= db_hashes.get(doc_type, set())
        index_union |= index_hashes.get(doc_type, set())

    for doc_type in DOC_TYPES:
        extracted_set = extracted_hashes.get(doc_type, set())
        db_set = db_hashes.get(doc_type, set())
        index_set = index_hashes.get(doc_type, set())

        missing_in_db = extracted_set - db_set
        extra_in_db = db_set - extracted_set
        # Index schema is unique on source_hash (not source_hash+doc_type), so
        # coverage must be evaluated against global index hashes.
        missing_in_index = db_set - index_union
        extra_in_index = index_set - db_union
        type_mismatch_in_index = (db_set & index_union) - index_set

        by_doc_type[doc_type] = TypeReconciliation(
            extracted_unique_hashes=len(extracted_set),
            db_unique_hashes=len(db_set),
            index_unique_hashes=len(index_set),
            missing_in_db=len(missing_in_db),
            extra_in_db=len(extra_in_db),
            missing_in_index=len(missing_in_index),
            extra_in_index=len(extra_in_index),
            type_mismatch_in_index=len(type_mismatch_in_index),
        )

        if missing_in_db:
            violations.append(
                f"{doc_type}: {len(missing_in_db)} extracted hashes missing in DB."
            )
        if missing_in_index:
            violations.append(
                f"{doc_type}: {len(missing_in_index)} DB hashes missing in document_index."
            )
        if extra_in_db:
            message = f"{doc_type}: {len(extra_in_db)} DB hashes not found in extracted JSON."
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
        if type_mismatch_in_index:
            warnings.append(
                f"{doc_type}: {len(type_mismatch_in_index)} DB hashes are indexed under a different doc_type."
            )

    if len(db_union) != sum(len(db_hashes.get(doc_type, set())) for doc_type in DOC_TYPES):
        warnings.append("Cross-table source_hash collisions detected across corpus doc types.")

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
        help="Fail when extracted JSON roots are missing.",
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
    )
    for result in results:
        _print_result(result)
    return 0 if all(result.status == "pass" for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
