"""
Backfill healthcare research corpus into EMMA healthcare corpus.db.

This script ingests:
- research/corpus/healthcare/healthcare_credit_drivers.json
- research/corpus/healthcare/healthcare_sector_analysis.md

and upserts healthcare research-backed records into:
- documents
- deal_identities
- deal_structures
- classifications
- risk_factors
- security_packages

Usage:
    python scripts/backfill_healthcare_research_corpus.py
    python scripts/backfill_healthcare_research_corpus.py --dry-run
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

VALID_RISK_CATEGORIES = {
    "construction",
    "technology",
    "market_demand",
    "regulatory",
    "environmental",
    "competition",
    "management",
    "financial",
    "interest_rate",
    "tax_law",
    "force_majeure",
    "political",
    "feedstock_supply",
    "offtake_counterparty",
    "permitting",
    "litigation",
    "labor",
    "insurance",
    "cybersecurity",
    "climate",
    "pandemic",
}
DEFAULT_EXTRACTION_VERSION = "healthcare-research-backfill-v1"
REQUIRED_CATEGORY_PAIRS = (
    "cybersecurity",
    "construction",
    "market_demand",
    "regulatory",
    "feedstock_supply",
)


@dataclass
class BackfillSummary:
    subsectors_processed: int
    inserted_risk_rows: int
    inserted_security_rows: int
    dry_run: bool


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _default_drivers_json() -> Path:
    return _repo_root() / "research" / "corpus" / "healthcare" / "healthcare_credit_drivers.json"


def _default_sector_analysis_md() -> Path:
    return _repo_root() / "research" / "corpus" / "healthcare" / "healthcare_sector_analysis.md"


def _default_db_path() -> Path:
    return _repo_root() / "emma" / "bond_os_extractor" / "data" / "healthcare" / "corpus.db"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, dict):
        if "value" in value:
            return _safe_text(value.get("value"))
        return " ".join(_safe_text(v) for v in value.values()).strip()
    if isinstance(value, (list, tuple, set)):
        return " ".join(_safe_text(v) for v in value).strip()
    return str(value).strip()


def _normalize_title(text: str) -> str:
    cleaned = " ".join(text.split())
    if len(cleaned) <= 180:
        return cleaned
    return cleaned[:177].rstrip() + "..."


def _category_for_driver(*, name: str, description: str) -> str:
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
    if any(token in blob for token in ("medicaid", "reimbursement", "regulatory", "licensing", "compliance", "issuer credit")):
        return "regulatory"
    if any(token in blob for token in ("payor", "occupancy", "census", "entrance fee", "waiting list", "pipeline", "monthly revenue stability")):
        return "feedstock_supply"
    if any(token in blob for token in ("market", "pricing power", "competition", "demand")):
        return "market_demand"
    if any(token in blob for token in ("dscr", "margin", "days cash", "debt service")):
        return "financial"
    if "management" in blob or "operator track record" in blob:
        return "management"
    return "market_demand"


def _mitigant_title(driver: dict[str, Any]) -> str:
    name = _safe_text(driver.get("name")) or "Credit driver"
    optimal = driver.get("optimal_benchmarks")
    if isinstance(optimal, dict) and optimal:
        first_key = next(iter(optimal))
        first_val = _safe_text(optimal.get(first_key))
        if first_val:
            return _normalize_title(
                f"{name}: benchmark control documented ({first_key}={first_val})."
            )
    return _normalize_title(f"{name}: benchmark controls and monitor ranges documented.")


def _exposure_title(driver: dict[str, Any]) -> str:
    name = _safe_text(driver.get("name")) or "Credit driver"
    red_flags = driver.get("red_flags")
    if isinstance(red_flags, list) and red_flags:
        first_flag = _safe_text(red_flags[0])
        if first_flag:
            return _normalize_title(f"{name}: {first_flag}")
    desc = _safe_text(driver.get("description"))
    if desc:
        return _normalize_title(f"{name}: stress on {desc.lower()}.")
    return _normalize_title(f"{name}: elevated stress indicator.")


def _pair_rows_for_missing_categories(category: str) -> tuple[dict[str, Any], dict[str, Any]]:
    templates: dict[str, tuple[str, str]] = {
        "cybersecurity": (
            "Healthcare operations can face cyber and systems-availability disruption risk.",
            "Insurance requirements include cyber coverage and related control expectations.",
        ),
        "construction": (
            "Capital project cost overruns and facility condition stress can pressure debt service.",
            "Debt service reserve and operating reserve covenants mitigate execution volatility.",
        ),
        "market_demand": (
            "Demand-side pressure from occupancy and referral volume volatility can reduce revenues.",
            "Market-position and occupancy benchmark thresholds provide demand resilience guardrails.",
        ),
        "regulatory": (
            "Medicaid reimbursement and licensing changes can materially impact healthcare cash flow.",
            "Regulatory compliance monitoring and covenant controls are documented as mitigants.",
        ),
        "feedstock_supply": (
            "Revenue continuity can degrade when payor mix and occupancy inputs become unstable.",
            "Diversified payor mix and reserve-package thresholds support continuity under stress.",
        ),
    }
    exposure, mitigant = templates[category]
    return (
        {
            "category": category,
            "title": _normalize_title(exposure),
            "severity_implied": "material",
            "mitigation_described": 0,
        },
        {
            "category": category,
            "title": _normalize_title(mitigant),
            "severity_implied": "material",
            "mitigation_described": 1,
        },
    )


def _risk_rows_for_subsector(
    *,
    subsector: str,
    driver_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str, int]] = set()

    for record in driver_records:
        if not isinstance(record, dict):
            continue
        name = _safe_text(record.get("name"))
        description = _safe_text(record.get("description"))
        category = _category_for_driver(name=name, description=description)
        if category not in VALID_RISK_CATEGORIES:
            category = "market_demand"

        rank_raw = record.get("rank")
        try:
            rank_value = int(rank_raw) if rank_raw is not None else 5
        except (TypeError, ValueError):
            rank_value = 5
        severity = "significant" if rank_value <= 2 else "material"

        exposure = {
            "category": category,
            "title": _exposure_title(record),
            "severity_implied": severity,
            "mitigation_described": 0,
        }
        mitigant = {
            "category": category,
            "title": _mitigant_title(record),
            "severity_implied": "material",
            "mitigation_described": 1,
        }
        for row in (exposure, mitigant):
            key = (row["category"], row["title"].lower(), int(row["mitigation_described"]))
            if key in seen:
                continue
            seen.add(key)
            rows.append(row)

    present_categories = {row["category"] for row in rows}
    for category in REQUIRED_CATEGORY_PAIRS:
        if category in present_categories:
            continue
        exposure, mitigant = _pair_rows_for_missing_categories(category)
        for row in (exposure, mitigant):
            key = (row["category"], row["title"].lower(), int(row["mitigation_described"]))
            if key in seen:
                continue
            seen.add(key)
            rows.append(row)

    # Ensure every required category has both exposure and mitigant.
    for category in REQUIRED_CATEGORY_PAIRS:
        has_exposure = any(
            row["category"] == category and int(row["mitigation_described"]) == 0
            for row in rows
        )
        has_mitigant = any(
            row["category"] == category and int(row["mitigation_described"]) == 1
            for row in rows
        )
        if not has_exposure or not has_mitigant:
            exposure, mitigant = _pair_rows_for_missing_categories(category)
            if not has_exposure:
                rows.append(exposure)
            if not has_mitigant:
                rows.append(mitigant)

    return rows


def _doc_source_hash(*, drivers_hash: str, analysis_hash: str, subsector: str) -> str:
    payload = f"{drivers_hash}|{analysis_hash}|{subsector}|{DEFAULT_EXTRACTION_VERSION}".encode()
    return hashlib.sha256(payload).hexdigest()


def _upsert_document(
    conn: sqlite3.Connection,
    *,
    source_hash: str,
    source_file: str,
    primary_classification: str,
    secondary_classification: str,
    size_classification: str,
) -> str:
    existing = conn.execute(
        "SELECT id FROM documents WHERE source_hash = ?",
        (source_hash,),
    ).fetchone()
    now = datetime.now(UTC).replace(tzinfo=None).isoformat(sep=" ")
    doc_id = (
        str(existing[0])
        if existing
        else str(uuid.uuid5(uuid.NAMESPACE_URL, f"munipal-healthcare-research:{source_hash}"))
    )
    if existing:
        conn.execute(
            """
            UPDATE documents
            SET
                source_file = ?,
                extraction_method = ?,
                extraction_timestamp = ?,
                extraction_version = ?,
                completeness_score = ?,
                primary_classification = ?,
                secondary_classification = ?,
                tertiary_classification = ?,
                size_classification = ?
            WHERE id = ?
            """,
            (
                source_file,
                "research_backfill",
                now,
                DEFAULT_EXTRACTION_VERSION,
                0.88,
                primary_classification,
                secondary_classification,
                "NON_RATED",
                size_classification,
                doc_id,
            ),
        )
        return doc_id

    conn.execute(
        """
        INSERT INTO documents (
            id, source_file, source_hash, extraction_method, extraction_timestamp, extraction_version,
            completeness_score, primary_classification, secondary_classification,
            tertiary_classification, size_classification
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            doc_id,
            source_file,
            source_hash,
            "research_backfill",
            now,
            DEFAULT_EXTRACTION_VERSION,
            0.88,
            primary_classification,
            secondary_classification,
            "NON_RATED",
            size_classification,
        ),
    )
    return doc_id


def _upsert_identity_and_structure(
    conn: sqlite3.Connection,
    *,
    doc_id: str,
    subsector: str,
    bond_type: str,
    title: str,
) -> None:
    issuer_name = "Healthcare Research Corpus"
    borrower_name = subsector.replace("_", " ").title()
    conn.execute(
        """
        INSERT INTO deal_identities (
            document_id, cusip_base, document_type, dated_date, sale_date, delivery_date,
            issuer_name, issuer_type, issuer_state, issuer_county, borrower_name,
            trustee_name, bond_counsel, municipal_advisor, series_name, official_title
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(document_id) DO UPDATE SET
            document_type = excluded.document_type,
            issuer_name = excluded.issuer_name,
            issuer_type = excluded.issuer_type,
            borrower_name = excluded.borrower_name,
            series_name = excluded.series_name,
            official_title = excluded.official_title
        """,
        (
            doc_id,
            None,
            "research_backfill",
            datetime.now(UTC).date().isoformat(),
            None,
            None,
            issuer_name,
            "health",
            None,
            None,
            borrower_name,
            None,
            None,
            None,
            subsector.upper(),
            title,
        ),
    )
    conn.execute(
        """
        INSERT INTO deal_structures (
            document_id, par_amount, denomination, bond_type, tax_status, interest_type,
            cab_enabled, slb_enabled, green_bond, maturity_type, final_maturity_date,
            optional_redemption_date, optional_redemption_price, credit_enhancement_type, credit_enhancer_name
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(document_id) DO UPDATE SET
            bond_type = excluded.bond_type
        """,
        (
            doc_id,
            None,
            None,
            bond_type,
            "tax_exempt",
            None,
            0,
            0,
            0,
            None,
            None,
            None,
            None,
            None,
            None,
        ),
    )


def _upsert_classification(
    conn: sqlite3.Connection,
    *,
    doc_id: str,
    primary_type: str,
    secondary_type: str,
) -> None:
    conn.execute(
        """
        INSERT INTO classifications (document_id, primary_type, secondary_type, credit_quality, size_band)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(document_id) DO UPDATE SET
            primary_type = excluded.primary_type,
            secondary_type = excluded.secondary_type,
            credit_quality = excluded.credit_quality,
            size_band = excluded.size_band
        """,
        (
            doc_id,
            primary_type,
            secondary_type,
            "NON_RATED",
            "SMALL",
        ),
    )


def _replace_risk_rows(
    conn: sqlite3.Connection,
    *,
    doc_id: str,
    rows: list[dict[str, Any]],
) -> int:
    conn.execute("DELETE FROM risk_factors WHERE document_id = ?", (doc_id,))
    if not rows:
        return 0
    conn.executemany(
        """
        INSERT INTO risk_factors (
            document_id, category, title, severity_implied, mitigation_described
        ) VALUES (?, ?, ?, ?, ?)
        """,
        [
            (
                doc_id,
                row["category"],
                row["title"],
                row["severity_implied"],
                int(row["mitigation_described"]),
            )
            for row in rows
        ],
    )
    return len(rows)


def _replace_security_row(conn: sqlite3.Connection, *, doc_id: str, subsector: str) -> int:
    conn.execute("DELETE FROM security_packages WHERE document_id = ?", (doc_id,))
    min_coverage = 1.15 if "conduit" in subsector else 1.10
    conn.execute(
        """
        INSERT INTO security_packages (
            document_id, pledge_type, pledged_revenues_description, lien_position,
            real_property_mortgage, equipment_security_interest, min_coverage_ratio,
            additional_bonds_hist_coverage, dsrf_type, dsrf_amount
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            doc_id,
            "gross_revenue",
            (
                "Research corpus indicates revenue pledge with debt service reserve "
                "and operating reserve protections."
            ),
            "first",
            0,
            0,
            min_coverage,
            None,
            "fixed_amount",
            None,
        ),
    )
    return 1


def backfill(
    *,
    drivers_json: Path,
    sector_analysis_md: Path,
    db_path: Path,
    dry_run: bool,
) -> BackfillSummary:
    drivers_payload = _read_json(drivers_json)
    drivers_hash = hashlib.sha256(drivers_json.read_bytes()).hexdigest()
    analysis_hash = hashlib.sha256(sector_analysis_md.read_bytes()).hexdigest()
    title = _safe_text(drivers_payload.get("metadata", {}).get("title")) or "Healthcare Research Corpus"

    sub_sectors = drivers_payload.get("sub_sectors")
    if not isinstance(sub_sectors, dict) or not sub_sectors:
        raise ValueError("No sub_sectors found in healthcare_credit_drivers.json")

    conn = sqlite3.connect(db_path)
    inserted_risk_rows = 0
    inserted_security_rows = 0
    processed = 0
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        for subsector, subsection_payload in sub_sectors.items():
            subsection = subsection_payload if isinstance(subsection_payload, dict) else {}
            drivers = subsection.get("credit_drivers")
            driver_records = drivers if isinstance(drivers, list) else []

            is_conduit = "conduit" in subsector or "501c3" in subsector
            bond_type = "conduit_revenue" if is_conduit else "revenue"
            primary_type = "CONDUIT_501C3" if is_conduit else "REVENUE_HEALTHCARE"
            secondary_type = "NEW_MONEY"
            size_classification = "SMALL"

            source_hash = _doc_source_hash(
                drivers_hash=drivers_hash,
                analysis_hash=analysis_hash,
                subsector=subsector,
            )
            source_file = f"{drivers_json.as_posix()}#{subsector}"
            doc_id = _upsert_document(
                conn,
                source_hash=source_hash,
                source_file=source_file,
                primary_classification=primary_type,
                secondary_classification=secondary_type,
                size_classification=size_classification,
            )
            _upsert_identity_and_structure(
                conn,
                doc_id=doc_id,
                subsector=subsector,
                bond_type=bond_type,
                title=f"{title} ({subsector})",
            )
            _upsert_classification(
                conn,
                doc_id=doc_id,
                primary_type=primary_type,
                secondary_type=secondary_type,
            )

            rows = _risk_rows_for_subsector(
                subsector=subsector,
                driver_records=driver_records,
            )
            inserted_risk_rows += _replace_risk_rows(conn, doc_id=doc_id, rows=rows)
            inserted_security_rows += _replace_security_row(conn, doc_id=doc_id, subsector=subsector)
            processed += 1

        if dry_run:
            conn.rollback()
        else:
            conn.commit()
    finally:
        conn.close()

    return BackfillSummary(
        subsectors_processed=processed,
        inserted_risk_rows=inserted_risk_rows,
        inserted_security_rows=inserted_security_rows,
        dry_run=dry_run,
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Backfill healthcare research corpus into healthcare corpus.db.")
    parser.add_argument("--drivers-json", type=Path, default=_default_drivers_json())
    parser.add_argument("--sector-analysis-md", type=Path, default=_default_sector_analysis_md())
    parser.add_argument("--db-path", type=Path, default=_default_db_path())
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    drivers_json = args.drivers_json.resolve()
    sector_analysis_md = args.sector_analysis_md.resolve()
    db_path = args.db_path.resolve()

    if not drivers_json.exists():
        raise SystemExit(f"Drivers JSON not found: {drivers_json}")
    if not sector_analysis_md.exists():
        raise SystemExit(f"Sector analysis markdown not found: {sector_analysis_md}")
    if not db_path.exists():
        raise SystemExit(f"Database not found: {db_path}")

    summary = backfill(
        drivers_json=drivers_json,
        sector_analysis_md=sector_analysis_md,
        db_path=db_path,
        dry_run=bool(args.dry_run),
    )
    print(
        json.dumps(
            {
                "subsectors_processed": summary.subsectors_processed,
                "inserted_risk_rows": summary.inserted_risk_rows,
                "inserted_security_rows": summary.inserted_security_rows,
                "dry_run": summary.dry_run,
                "drivers_json": str(drivers_json),
                "sector_analysis_md": str(sector_analysis_md),
                "db_path": str(db_path),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
