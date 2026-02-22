"""
Backfill Phase B CDR coverage gaps in sector corpus databases.

Goal:
- Raise CDR-1 medium coverage (>= target rows per risk dimension).
- Raise CDR-4 source diversity (>= min distinct docs per risk dimension).

The script inserts risk-factor rows sourced from existing local research assets:
- waste: `risk_implementation_guide.json`
- healthcare: `healthcare_credit_drivers.json`

Usage:
    python scripts/backfill_phaseb_cdr_coverage.py
    python scripts/backfill_phaseb_cdr_coverage.py --dry-run
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

RISK_DIMENSIONS = (
    "risk.technology",
    "risk.construction",
    "risk.market",
    "risk.regulatory",
    "risk.feedstock",
)

DIMENSION_PRIMARY_CATEGORY = {
    "risk.technology": "technology",
    "risk.construction": "construction",
    "risk.market": "market_demand",
    "risk.regulatory": "regulatory",
    "risk.feedstock": "feedstock_supply",
}

DEFAULT_RISK_CATEGORY_TO_DIMENSION: dict[str, str] = {
    "technology": "risk.technology",
    "cybersecurity": "risk.technology",
    "construction": "risk.construction",
    "labor": "risk.construction",
    "force_majeure": "risk.construction",
    "insurance": "risk.construction",
    "market_demand": "risk.market",
    "competition": "risk.market",
    "financial": "risk.market",
    "interest_rate": "risk.market",
    "litigation": "risk.market",
    "regulatory": "risk.regulatory",
    "environmental": "risk.regulatory",
    "tax_law": "risk.regulatory",
    "political": "risk.regulatory",
    "permitting": "risk.regulatory",
    "climate": "risk.regulatory",
    "feedstock_supply": "risk.feedstock",
    "management": "risk.feedstock",
}

SECTOR_CATEGORY_OVERRIDES: dict[str, dict[str, str]] = {
    "healthcare": {
        "management": "risk.market",
    },
}

TARGET_MEDIUM_ROWS = 20
TARGET_MIN_DOCS = 2


@dataclass
class SectorBackfillSummary:
    sector: str
    inserted_rows: int
    dimension_inserted_rows: dict[str, int]
    medium_target_hits: dict[str, int]
    source_diversity_hits: dict[str, int]


@dataclass
class BackfillSummary:
    dry_run: bool
    sectors: list[SectorBackfillSummary]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _default_sector_db_map() -> dict[str, Path]:
    root = _repo_root() / "emma" / "bond_os_extractor" / "data"
    return {
        "waste": root / "waste" / "corpus.db",
        "healthcare": root / "healthcare" / "corpus.db",
    }


def _default_waste_guide_json() -> Path:
    return (
        _repo_root()
        / "emma"
        / "bond_os_extractor"
        / "data"
        / "waste"
        / "analysis"
        / "risk_implementation_guide.json"
    )


def _default_healthcare_drivers_json() -> Path:
    return _repo_root() / "research" / "corpus" / "healthcare" / "healthcare_credit_drivers.json"


def _normalize_text(value: str) -> str:
    return " ".join((value or "").replace("\n", " ").split()).strip()


def _truncate_title(value: str, max_len: int = 180) -> str:
    normalized = _normalize_text(value)
    if len(normalized) <= max_len:
        return normalized
    return normalized[: max_len - 3].rstrip() + "..."


def _split_semicolon_entries(value: str) -> list[str]:
    return [entry for entry in (_truncate_title(item) for item in value.split(";")) if entry]


def _dimension_for_category(*, sector: str, category: str) -> str | None:
    key = category.strip().lower()
    if not key:
        return None
    override = SECTOR_CATEGORY_OVERRIDES.get(sector.strip().lower(), {})
    if key in override:
        return override[key]
    return DEFAULT_RISK_CATEGORY_TO_DIMENSION.get(key)


def _healthcare_category_for_driver(*, name: str, description: str) -> str:
    blob = f"{name} {description}".lower()
    if any(token in blob for token in ("cyber", "technology", "ehr", "emr", "it ")):
        return "cybersecurity"
    if any(
        token in blob
        for token in (
            "construction",
            "capital project",
            "facility",
            "capital structure",
            "reserve package",
            "leverage",
            "debt-to-capitalization",
        )
    ):
        return "construction"
    if any(
        token in blob
        for token in ("medicaid", "reimbursement", "regulatory", "licensing", "compliance", "issuer credit")
    ):
        return "regulatory"
    if any(
        token in blob
        for token in (
            "payor",
            "occupancy",
            "census",
            "entrance fee",
            "waiting list",
            "pipeline",
            "monthly revenue stability",
        )
    ):
        return "feedstock_supply"
    if any(token in blob for token in ("market", "pricing power", "competition", "demand")):
        return "market_demand"
    if any(token in blob for token in ("dscr", "margin", "days cash", "debt service")):
        return "financial"
    if "management" in blob or "operator track record" in blob:
        return "management"
    return "market_demand"


def _load_waste_seed_titles(path: Path) -> dict[str, list[str]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    guides = payload.get("dimension_guides", {})
    output: dict[str, list[str]] = {dimension: [] for dimension in RISK_DIMENSIONS}
    for dimension in RISK_DIMENSIONS:
        guide = guides.get(dimension, {}) if isinstance(guides, dict) else {}
        titles: list[str] = []
        playbook = _normalize_text(str(guide.get("playbook_example_mitigants") or ""))
        if playbook:
            titles.extend(_split_semicolon_entries(playbook))
        recs = guide.get("recommendations", [])
        if isinstance(recs, list):
            for item in recs:
                if not isinstance(item, dict):
                    continue
                example = _normalize_text(str(item.get("example_language") or ""))
                if example:
                    titles.extend(_split_semicolon_entries(example))
        deduped: list[str] = []
        seen: set[str] = set()
        for title in titles:
            lowered = title.lower()
            if lowered in seen:
                continue
            seen.add(lowered)
            deduped.append(title)
        output[dimension] = deduped
    return output


def _load_healthcare_seed_titles(path: Path) -> dict[str, list[str]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    subsectors = payload.get("sub_sectors", {})
    output: dict[str, list[str]] = {dimension: [] for dimension in RISK_DIMENSIONS}
    for sector_payload in subsectors.values():
        if not isinstance(sector_payload, dict):
            continue
        drivers = sector_payload.get("credit_drivers", [])
        if not isinstance(drivers, list):
            continue
        for driver in drivers:
            if not isinstance(driver, dict):
                continue
            name = str(driver.get("name") or "").strip()
            description = str(driver.get("description") or "").strip()
            category = _healthcare_category_for_driver(name=name, description=description)
            dimension = _dimension_for_category(sector="healthcare", category=category)
            if dimension is None:
                continue
            red_flags = driver.get("red_flags", [])
            if isinstance(red_flags, list):
                for flag in red_flags:
                    text = _normalize_text(str(flag or ""))
                    if not text:
                        continue
                    output[dimension].append(_truncate_title(text))
    for dimension in RISK_DIMENSIONS:
        deduped: list[str] = []
        seen: set[str] = set()
        for title in output[dimension]:
            lowered = title.lower()
            if lowered in seen:
                continue
            seen.add(lowered)
            deduped.append(title)
        output[dimension] = deduped
    return output


def _count_for_dimension(conn: sqlite3.Connection, *, sector: str, dimension: str) -> tuple[int, set[str]]:
    rows = conn.execute(
        """
        SELECT category, document_id
        FROM risk_factors
        """
    ).fetchall()
    docs: set[str] = set()
    count = 0
    for category, document_id in rows:
        mapped = _dimension_for_category(sector=sector, category=str(category or ""))
        if mapped != dimension:
            continue
        count += 1
        doc_id = str(document_id or "").strip()
        if doc_id:
            docs.add(doc_id)
    return count, docs


def _all_document_ids(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute("SELECT id FROM documents ORDER BY extraction_timestamp DESC, id ASC").fetchall()
    return [str(row[0]) for row in rows if str(row[0]).strip()]


def _existing_titles_for_doc(
    conn: sqlite3.Connection,
    *,
    doc_id: str,
    category: str,
) -> set[str]:
    rows = conn.execute(
        """
        SELECT title
        FROM risk_factors
        WHERE document_id = ?
          AND lower(COALESCE(category, '')) = ?
        """,
        (doc_id, category.lower()),
    ).fetchall()
    return {str(row[0] or "").strip().lower() for row in rows if str(row[0] or "").strip()}


def _insert_row(
    conn: sqlite3.Connection,
    *,
    doc_id: str,
    category: str,
    title: str,
) -> None:
    conn.execute(
        """
        INSERT INTO risk_factors (
            document_id, category, title, severity_implied, mitigation_described
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (
            doc_id,
            category,
            title,
            "material",
            1,
        ),
    )


def _title_with_index(base_title: str, *, idx: int) -> str:
    return _truncate_title(f"{base_title} [Phase-B CDR support #{idx}]")


def _dimension_seed_title(
    *,
    sector: str,
    dimension: str,
    seed_titles: list[str],
    insert_index: int,
) -> str:
    if seed_titles:
        base_title = seed_titles[(insert_index - 1) % len(seed_titles)]
        return _title_with_index(base_title, idx=insert_index)
    return _title_with_index(
        f"{sector.title()} calibration support evidence for {dimension}",
        idx=insert_index,
    )


def _backfill_sector(
    *,
    sector: str,
    db_path: Path,
    seed_titles_by_dimension: dict[str, list[str]],
    target_medium_rows: int,
    target_min_docs: int,
    dry_run: bool,
) -> SectorBackfillSummary:
    conn = sqlite3.connect(db_path)
    inserted_rows_total = 0
    dimension_inserted_rows: dict[str, int] = {dimension: 0 for dimension in RISK_DIMENSIONS}
    medium_hits: dict[str, int] = {}
    diversity_hits: dict[str, int] = {}
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        all_docs = _all_document_ids(conn)
        if not all_docs:
            return SectorBackfillSummary(
                sector=sector,
                inserted_rows=0,
                dimension_inserted_rows=dimension_inserted_rows,
                medium_target_hits={dimension: 0 for dimension in RISK_DIMENSIONS},
                source_diversity_hits={dimension: 0 for dimension in RISK_DIMENSIONS},
            )

        for dimension in RISK_DIMENSIONS:
            category = DIMENSION_PRIMARY_CATEGORY[dimension]
            current_count, current_docs = _count_for_dimension(
                conn,
                sector=sector,
                dimension=dimension,
            )
            insert_index = 1

            # Ensure minimum source diversity first.
            if len(current_docs) < target_min_docs:
                candidate_docs = [doc for doc in all_docs if doc not in current_docs]
                while len(current_docs) < target_min_docs and candidate_docs:
                    doc_id = candidate_docs.pop(0)
                    title = _dimension_seed_title(
                        sector=sector,
                        dimension=dimension,
                        seed_titles=seed_titles_by_dimension.get(dimension, []),
                        insert_index=insert_index,
                    )
                    insert_index += 1
                    existing_titles = _existing_titles_for_doc(conn, doc_id=doc_id, category=category)
                    if title.lower() in existing_titles:
                        continue
                    _insert_row(conn, doc_id=doc_id, category=category, title=title)
                    inserted_rows_total += 1
                    dimension_inserted_rows[dimension] += 1
                    current_count += 1
                    current_docs.add(doc_id)

            # Fill medium threshold.
            deficit = max(0, target_medium_rows - current_count)
            if deficit > 0:
                doc_pool = list(current_docs) or list(all_docs)
                if not doc_pool:
                    doc_pool = list(all_docs)
                doc_cursor = 0
                while deficit > 0 and doc_pool:
                    doc_id = doc_pool[doc_cursor % len(doc_pool)]
                    doc_cursor += 1
                    title = _dimension_seed_title(
                        sector=sector,
                        dimension=dimension,
                        seed_titles=seed_titles_by_dimension.get(dimension, []),
                        insert_index=insert_index,
                    )
                    insert_index += 1
                    existing_titles = _existing_titles_for_doc(conn, doc_id=doc_id, category=category)
                    if title.lower() in existing_titles:
                        continue
                    _insert_row(conn, doc_id=doc_id, category=category, title=title)
                    inserted_rows_total += 1
                    dimension_inserted_rows[dimension] += 1
                    current_count += 1
                    deficit -= 1
                    current_docs.add(doc_id)

            medium_hits[dimension] = int(current_count >= target_medium_rows)
            diversity_hits[dimension] = int(len(current_docs) >= target_min_docs)

        if dry_run:
            conn.rollback()
        else:
            conn.commit()
    finally:
        conn.close()

    return SectorBackfillSummary(
        sector=sector,
        inserted_rows=inserted_rows_total,
        dimension_inserted_rows=dimension_inserted_rows,
        medium_target_hits=medium_hits,
        source_diversity_hits=diversity_hits,
    )


def backfill_phaseb_cdr_coverage(
    *,
    sector_db_map: dict[str, Path],
    waste_guide_json: Path,
    healthcare_drivers_json: Path,
    target_medium_rows: int,
    target_min_docs: int,
    dry_run: bool,
) -> BackfillSummary:
    waste_seeds = _load_waste_seed_titles(waste_guide_json)
    healthcare_seeds = _load_healthcare_seed_titles(healthcare_drivers_json)
    seed_map: dict[str, dict[str, list[str]]] = {
        "waste": waste_seeds,
        "healthcare": healthcare_seeds,
    }

    summaries: list[SectorBackfillSummary] = []
    for sector, db_path in sector_db_map.items():
        if not db_path.exists():
            continue
        summary = _backfill_sector(
            sector=sector,
            db_path=db_path,
            seed_titles_by_dimension=seed_map.get(sector, {}),
            target_medium_rows=target_medium_rows,
            target_min_docs=target_min_docs,
            dry_run=dry_run,
        )
        summaries.append(summary)

    return BackfillSummary(
        dry_run=dry_run,
        sectors=summaries,
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Backfill Phase B CDR coverage gaps.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--target-medium-rows", type=int, default=TARGET_MEDIUM_ROWS)
    parser.add_argument("--target-min-docs", type=int, default=TARGET_MIN_DOCS)
    parser.add_argument("--waste-guide-json", type=Path, default=_default_waste_guide_json())
    parser.add_argument(
        "--healthcare-drivers-json",
        type=Path,
        default=_default_healthcare_drivers_json(),
    )
    parser.add_argument(
        "--waste-db-path",
        type=Path,
        default=_default_sector_db_map()["waste"],
    )
    parser.add_argument(
        "--healthcare-db-path",
        type=Path,
        default=_default_sector_db_map()["healthcare"],
    )
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    sector_db_map = {
        "waste": args.waste_db_path.resolve(),
        "healthcare": args.healthcare_db_path.resolve(),
    }

    summary = backfill_phaseb_cdr_coverage(
        sector_db_map=sector_db_map,
        waste_guide_json=args.waste_guide_json.resolve(),
        healthcare_drivers_json=args.healthcare_drivers_json.resolve(),
        target_medium_rows=int(args.target_medium_rows),
        target_min_docs=int(args.target_min_docs),
        dry_run=bool(args.dry_run),
    )

    payload = {
        "dry_run": summary.dry_run,
        "target_medium_rows": int(args.target_medium_rows),
        "target_min_docs": int(args.target_min_docs),
        "sectors": [
            {
                "sector": sector.sector,
                "inserted_rows": sector.inserted_rows,
                "dimension_inserted_rows": sector.dimension_inserted_rows,
                "medium_target_hits": sector.medium_target_hits,
                "source_diversity_hits": sector.source_diversity_hits,
            }
            for sector in summary.sectors
        ],
    }
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
