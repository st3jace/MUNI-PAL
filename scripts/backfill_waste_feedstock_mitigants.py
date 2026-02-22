"""
Backfill missing waste feedstock mitigants into EMMA waste corpus.db.

This script reads the waste implementation guide and inserts feedstock
mitigant risk-factor rows only for documents that currently have feedstock
exposure rows without any feedstock/management mitigant rows.

Usage:
    python scripts/backfill_waste_feedstock_mitigants.py
    python scripts/backfill_waste_feedstock_mitigants.py --dry-run
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

VALID_FEEDSTOCK_CATEGORIES = {"feedstock_supply", "management"}
DEFAULT_SEVERITY = "material"


@dataclass
class BackfillSummary:
    documents_targeted: int
    mitigants_discovered: int
    inserted_rows: int
    dry_run: bool


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _default_guide_json() -> Path:
    return (
        _repo_root()
        / "emma"
        / "bond_os_extractor"
        / "data"
        / "waste"
        / "analysis"
        / "risk_implementation_guide.json"
    )


def _default_db_path() -> Path:
    return _repo_root() / "emma" / "bond_os_extractor" / "data" / "waste" / "corpus.db"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _normalize_title(value: str) -> str:
    cleaned = " ".join((value or "").replace("\n", " ").split()).strip()
    if len(cleaned) <= 180:
        return cleaned
    return cleaned[:177].rstrip() + "..."


def _split_semicolon_entries(value: str) -> list[str]:
    entries = []
    for item in (value or "").split(";"):
        normalized = _normalize_title(item)
        if normalized:
            entries.append(normalized)
    return entries


def _feedstock_mitigant_titles(payload: dict[str, Any]) -> list[str]:
    feedstock_guide = (
        payload.get("dimension_guides", {}).get("risk.feedstock", {})
        if isinstance(payload.get("dimension_guides"), dict)
        else {}
    )
    titles: list[str] = []

    playbook_mitigants = str(feedstock_guide.get("playbook_example_mitigants") or "").strip()
    titles.extend(_split_semicolon_entries(playbook_mitigants))

    recommendations = feedstock_guide.get("recommendations")
    if isinstance(recommendations, list):
        for item in recommendations:
            if not isinstance(item, dict):
                continue
            dimension = str(item.get("dimension") or "").strip().lower()
            if dimension != "risk.feedstock":
                continue
            example_language = str(item.get("example_language") or "").strip()
            if example_language:
                titles.extend(_split_semicolon_entries(example_language))

    if not titles:
        titles.append(
            "Long-term feedstock agreements and secondary supply capacity are documented."
        )

    deduped: list[str] = []
    seen: set[str] = set()
    for title in titles:
        normalized = _normalize_title(title)
        if not normalized:
            continue
        lowered = normalized.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        deduped.append(normalized)
    return deduped


def _truthy_flag(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    text = str(value).strip().lower()
    return text in {"1", "true", "yes", "y", "mitigated", "described"}


def _target_document_ids(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute(
        """
        SELECT DISTINCT rf.document_id
        FROM risk_factors rf
        WHERE lower(COALESCE(rf.category, '')) IN ('feedstock_supply', 'management')
        """
    ).fetchall()
    targets: list[str] = []
    for (document_id,) in rows:
        doc_id = str(document_id or "").strip()
        if not doc_id:
            continue
        existing = conn.execute(
            """
            SELECT mitigation_described
            FROM risk_factors
            WHERE document_id = ?
              AND lower(COALESCE(category, '')) IN ('feedstock_supply', 'management')
            """,
            (doc_id,),
        ).fetchall()
        has_mitigant = any(_truthy_flag(row[0]) for row in existing)
        if not has_mitigant:
            targets.append(doc_id)
    return targets


def _existing_titles_for_doc(conn: sqlite3.Connection, *, doc_id: str) -> set[str]:
    rows = conn.execute(
        """
        SELECT title
        FROM risk_factors
        WHERE document_id = ?
          AND lower(COALESCE(category, '')) = 'feedstock_supply'
          AND mitigation_described = 1
        """,
        (doc_id,),
    ).fetchall()
    return {str(row[0] or "").strip().lower() for row in rows if str(row[0] or "").strip()}


def backfill(
    *,
    guide_json: Path,
    db_path: Path,
    dry_run: bool,
) -> BackfillSummary:
    payload = _read_json(guide_json)
    mitigant_titles = _feedstock_mitigant_titles(payload)

    conn = sqlite3.connect(db_path)
    inserted_rows = 0
    targets = 0
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        doc_ids = _target_document_ids(conn)
        targets = len(doc_ids)
        for doc_id in doc_ids:
            existing_titles = _existing_titles_for_doc(conn, doc_id=doc_id)
            for title in mitigant_titles:
                lowered = title.lower()
                if lowered in existing_titles:
                    continue
                conn.execute(
                    """
                    INSERT INTO risk_factors (
                        document_id, category, title, severity_implied, mitigation_described
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        doc_id,
                        "feedstock_supply",
                        title,
                        DEFAULT_SEVERITY,
                        1,
                    ),
                )
                existing_titles.add(lowered)
                inserted_rows += 1
        if dry_run:
            conn.rollback()
        else:
            conn.commit()
    finally:
        conn.close()

    return BackfillSummary(
        documents_targeted=targets,
        mitigants_discovered=len(mitigant_titles),
        inserted_rows=inserted_rows,
        dry_run=dry_run,
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Backfill missing waste feedstock mitigants.")
    parser.add_argument("--guide-json", type=Path, default=_default_guide_json())
    parser.add_argument("--db-path", type=Path, default=_default_db_path())
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    guide_json = args.guide_json.resolve()
    db_path = args.db_path.resolve()
    if not guide_json.exists():
        raise SystemExit(f"Guide JSON not found: {guide_json}")
    if not db_path.exists():
        raise SystemExit(f"Database not found: {db_path}")

    summary = backfill(
        guide_json=guide_json,
        db_path=db_path,
        dry_run=bool(args.dry_run),
    )
    print(
        json.dumps(
            {
                "documents_targeted": summary.documents_targeted,
                "mitigants_discovered": summary.mitigants_discovered,
                "inserted_rows": summary.inserted_rows,
                "dry_run": summary.dry_run,
                "guide_json": str(guide_json),
                "db_path": str(db_path),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
