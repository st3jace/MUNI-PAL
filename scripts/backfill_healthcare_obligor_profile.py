"""
Backfill healthcare obligor profile data into EMMA healthcare corpus.db.

This script ingests a profile JSON (default: CCHCI) and upserts:
- documents
- deal_identities
- deal_structures
- classifications
- risk_factors
- security_packages

Usage:
    python scripts/backfill_healthcare_obligor_profile.py
    python scripts/backfill_healthcare_obligor_profile.py --dry-run
    python scripts/backfill_healthcare_obligor_profile.py --profile-json <path> --db-path <path>
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
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

VALID_LIEN_POSITIONS = {"first", "second", "pari_passu", "subordinate"}
VALID_PLEDGE_TYPES = {"gross_revenue", "net_revenue", "specific_revenue", "none"}
DEFAULT_EXTRACTION_VERSION = "healthcare-profile-backfill-v1"


@dataclass
class BackfillSummary:
    document_id: str
    inserted_risk_factors: int
    inserted_security_packages: int
    dry_run: bool


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _default_profile_json() -> Path:
    return (
        _repo_root()
        / "emma"
        / "bond_os_extractor"
        / "data"
        / "healthcare"
        / "analysis"
        / "cchci_obligor_profile.json"
    )


def _default_db_path() -> Path:
    return _repo_root() / "emma" / "bond_os_extractor" / "data" / "healthcare" / "corpus.db"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _source_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _safe_str(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _normalized_title(text: str) -> str:
    cleaned = " ".join(text.replace("\n", " ").split())
    if not cleaned:
        return "Risk factor"
    if len(cleaned) <= 180:
        return cleaned
    return cleaned[:177].rstrip() + "..."


def _risk_category_from_text(text: str) -> str:
    lowered = text.lower()
    mapping: list[tuple[str, str]] = [
        ("material weakness", "management"),
        ("audit", "management"),
        ("allowance", "management"),
        ("accounts receivable", "management"),
        ("medicaid", "regulatory"),
        ("reimbursement", "regulatory"),
        ("grant", "financial"),
        ("loss", "financial"),
        ("cash", "financial"),
        ("balloon", "financial"),
        ("debt", "financial"),
        ("unrated", "financial"),
        ("interest", "interest_rate"),
    ]
    for needle, category in mapping:
        if needle in lowered:
            return category
    return "financial"


def _severity_from_text(text: str) -> str:
    lowered = text.lower()
    if any(token in lowered for token in ("material weakness", "operating loss", "cash declined", "balloon")):
        return "significant"
    if any(token in lowered for token in ("risk", "declining", "unrated", "weakness")):
        return "material"
    return "material"


def _risk_rows(profile: dict[str, Any]) -> list[dict[str, Any]]:
    bond_readiness = profile.get("bond_readiness")
    financials = profile.get("financials")
    ida_loan = profile.get("ida_loan")

    challenges = (
        bond_readiness.get("challenges", [])
        if isinstance(bond_readiness, dict)
        else []
    )
    covenants = ida_loan.get("covenants", []) if isinstance(ida_loan, dict) else []

    refinancing_covenant_present = any(
        "refinanc" in _safe_str(item).lower()
        for item in covenants
    )

    rows: list[dict[str, Any]] = []
    dedupe_keys: set[tuple[str, str]] = set()

    for challenge in challenges:
        challenge_text = _safe_str(challenge)
        if not challenge_text:
            continue
        category = _risk_category_from_text(challenge_text)
        if category not in VALID_RISK_CATEGORIES:
            category = "financial"
        mitigation = False
        lowered = challenge_text.lower()
        if "material weakness" in lowered:
            mitigation = True
        if "balloon" in lowered and refinancing_covenant_present:
            mitigation = True

        row = {
            "category": category,
            "title": _normalized_title(challenge_text),
            "severity_implied": _severity_from_text(challenge_text),
            "mitigation_described": int(mitigation),
        }
        key = (row["category"], row["title"].lower())
        if key not in dedupe_keys:
            dedupe_keys.add(key)
            rows.append(row)

    weaknesses = (
        financials.get("material_weaknesses", [])
        if isinstance(financials, dict)
        else []
    )
    for weakness in weaknesses:
        if not isinstance(weakness, dict):
            continue
        finding_id = _safe_str(weakness.get("finding_id"))
        description = _safe_str(weakness.get("description"))
        detail = _safe_str(weakness.get("detail"))
        status = _safe_str(weakness.get("status")).lower()

        title_parts = [part for part in [finding_id, description] if part]
        title = " - ".join(title_parts) if title_parts else "Audit finding"
        if detail:
            title = f"{title}: {detail}"

        row = {
            "category": "management",
            "title": _normalized_title(title),
            "severity_implied": "significant",
            "mitigation_described": int("corrective_action" in status or "in_progress" in status),
        }
        key = (row["category"], row["title"].lower())
        if key not in dedupe_keys:
            dedupe_keys.add(key)
            rows.append(row)

    return rows


def _parse_first_ratio(texts: list[str]) -> float | None:
    ratio_pattern = re.compile(r"(\d+(?:\.\d+)?)\s*x", re.IGNORECASE)
    for text in texts:
        match = ratio_pattern.search(text)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None
    return None


def _security_row(profile: dict[str, Any]) -> dict[str, Any]:
    ida_loan = profile.get("ida_loan") if isinstance(profile.get("ida_loan"), dict) else {}
    security = ida_loan.get("security") if isinstance(ida_loan.get("security"), dict) else {}
    bond_readiness = (
        profile.get("bond_readiness")
        if isinstance(profile.get("bond_readiness"), dict)
        else {}
    )
    options = [
        _safe_str(item)
        for item in bond_readiness.get("security_package_options", [])
        if _safe_str(item)
    ]

    options_lower = [item.lower() for item in options]
    pledge_type: str | None = None
    if any("gross revenue pledge" in item for item in options_lower):
        pledge_type = "gross_revenue"
    elif any("net revenue pledge" in item for item in options_lower):
        pledge_type = "net_revenue"
    elif any("grant assignment" in item or "intercept" in item for item in options_lower):
        pledge_type = "specific_revenue"
    if pledge_type not in VALID_PLEDGE_TYPES:
        pledge_type = None

    lien_position = _safe_str(security.get("lien_position")).lower()
    if lien_position not in VALID_LIEN_POSITIONS:
        lien_position = None

    real_property_mortgage = (
        "deed" in _safe_str(security.get("type")).lower()
        or any("real property" in item for item in options_lower)
        or any("collateral" in item for item in options_lower)
    )
    equipment_security_interest = any("equipment" in item for item in options_lower)

    pledged_revenue_segments = [
        item for item in options
        if "revenue" in item.lower() or "grant" in item.lower() or "intercept" in item.lower()
    ]
    property_text = _safe_str(security.get("property"))
    if property_text:
        pledged_revenue_segments.append(f"Collateral property: {property_text}")
    pledged_revenues_description = (
        "; ".join(dict.fromkeys(pledged_revenue_segments))
        if pledged_revenue_segments
        else None
    )

    min_coverage_ratio = _parse_first_ratio(options)
    additional_bonds_hist_coverage = _parse_first_ratio(
        [item for item in options if "additional bonds" in item.lower() or "dscr" in item.lower()]
    )

    dsrf_type = None
    if any("debt service reserve fund" in item for item in options_lower):
        dsrf_type = "fixed_amount"

    return {
        "pledge_type": pledge_type,
        "pledged_revenues_description": pledged_revenues_description,
        "lien_position": lien_position,
        "real_property_mortgage": int(real_property_mortgage),
        "equipment_security_interest": int(equipment_security_interest),
        "min_coverage_ratio": min_coverage_ratio,
        "additional_bonds_hist_coverage": additional_bonds_hist_coverage,
        "dsrf_type": dsrf_type,
        "dsrf_amount": None,
    }


def _size_band_for_amount(amount: float | None) -> str:
    if amount is None:
        return "UNKNOWN"
    if amount < 10_000_000:
        return "MICRO"
    if amount < 50_000_000:
        return "SMALL"
    if amount < 250_000_000:
        return "MEDIUM"
    if amount < 1_000_000_000:
        return "LARGE"
    return "JUMBO"


def _coerce_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _upsert_document(
    conn: sqlite3.Connection,
    *,
    profile_path: Path,
    source_hash: str,
) -> str:
    existing = conn.execute(
        "SELECT id FROM documents WHERE source_hash = ?",
        (source_hash,),
    ).fetchone()

    now = datetime.now(UTC).replace(tzinfo=None).isoformat(sep=" ")
    source_file = profile_path.as_posix()
    doc_id = (
        str(existing[0])
        if existing
        else str(uuid.uuid5(uuid.NAMESPACE_URL, f"munipal-healthcare-profile:{source_hash}"))
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
                "profile_backfill",
                now,
                DEFAULT_EXTRACTION_VERSION,
                0.9,
                "CONDUIT_501C3",
                "NEW_MONEY",
                "NON_RATED",
                "MICRO",
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
            "profile_backfill",
            now,
            DEFAULT_EXTRACTION_VERSION,
            0.9,
            "CONDUIT_501C3",
            "NEW_MONEY",
            "NON_RATED",
            "MICRO",
        ),
    )
    return doc_id


def _upsert_identity_structure_and_classification(
    conn: sqlite3.Connection,
    *,
    doc_id: str,
    profile: dict[str, Any],
    bond_type: str,
) -> None:
    obligor = profile.get("obligor") if isinstance(profile.get("obligor"), dict) else {}
    ida_loan = profile.get("ida_loan") if isinstance(profile.get("ida_loan"), dict) else {}

    issuer_name = _safe_str(ida_loan.get("lender")) or _safe_str(obligor.get("canonical_name"))
    issuer_type = "ida" if "development authority" in issuer_name.lower() else "authority"
    borrower_name = _safe_str(ida_loan.get("borrower")) or _safe_str(obligor.get("legal_name"))

    conn.execute(
        """
        INSERT INTO deal_identities (
            document_id, cusip_base, document_type, dated_date, sale_date, delivery_date,
            issuer_name, issuer_type, issuer_state, issuer_county, borrower_name,
            trustee_name, bond_counsel, municipal_advisor, series_name, official_title
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(document_id) DO UPDATE SET
            document_type = excluded.document_type,
            dated_date = excluded.dated_date,
            issuer_name = excluded.issuer_name,
            issuer_type = excluded.issuer_type,
            issuer_state = excluded.issuer_state,
            issuer_county = excluded.issuer_county,
            borrower_name = excluded.borrower_name,
            series_name = excluded.series_name,
            official_title = excluded.official_title
        """,
        (
            doc_id,
            None,
            "profile_backfill",
            _safe_str(ida_loan.get("origination_date")) or None,
            None,
            None,
            issuer_name or None,
            issuer_type,
            _safe_str(obligor.get("state")) or None,
            _safe_str(obligor.get("county")) or None,
            borrower_name or None,
            None,
            None,
            None,
            "CCHCI_IDA_2024",
            _safe_str(ida_loan.get("description")) or None,
        ),
    )

    principal = _coerce_float(ida_loan.get("principal"))
    maturity_date = _safe_str(ida_loan.get("maturity_date")) or None
    interest_type = "fixed_rate" if _coerce_float(ida_loan.get("interest_rate")) is not None else None
    maturity_type = "bullet" if "balloon" in _safe_str(ida_loan.get("payment_structure")).lower() else None

    conn.execute(
        """
        INSERT INTO deal_structures (
            document_id, par_amount, denomination, bond_type, tax_status, interest_type,
            cab_enabled, slb_enabled, green_bond, maturity_type, final_maturity_date,
            optional_redemption_date, optional_redemption_price, credit_enhancement_type, credit_enhancer_name
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(document_id) DO UPDATE SET
            par_amount = excluded.par_amount,
            bond_type = excluded.bond_type,
            interest_type = excluded.interest_type,
            maturity_type = excluded.maturity_type,
            final_maturity_date = excluded.final_maturity_date
        """,
        (
            doc_id,
            principal,
            None,
            bond_type,
            None,
            interest_type,
            0,
            0,
            0,
            maturity_type,
            maturity_date,
            None,
            None,
            None,
            None,
        ),
    )

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
            "CONDUIT_501C3",
            "NEW_MONEY",
            "NON_RATED",
            _size_band_for_amount(principal),
        ),
    )


def _replace_risk_factors(
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


def _replace_security_package(
    conn: sqlite3.Connection,
    *,
    doc_id: str,
    row: dict[str, Any],
) -> int:
    conn.execute("DELETE FROM security_packages WHERE document_id = ?", (doc_id,))
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
            row.get("pledge_type"),
            row.get("pledged_revenues_description"),
            row.get("lien_position"),
            int(bool(row.get("real_property_mortgage"))),
            int(bool(row.get("equipment_security_interest"))),
            row.get("min_coverage_ratio"),
            row.get("additional_bonds_hist_coverage"),
            row.get("dsrf_type"),
            row.get("dsrf_amount"),
        ),
    )
    return 1


def backfill(
    *,
    profile_json: Path,
    db_path: Path,
    bond_type: str,
    dry_run: bool,
) -> BackfillSummary:
    profile = _read_json(profile_json)
    db_source_hash = _source_hash(profile_json)
    risk_rows = _risk_rows(profile)
    security_row = _security_row(profile)

    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        doc_id = _upsert_document(conn, profile_path=profile_json, source_hash=db_source_hash)
        _upsert_identity_structure_and_classification(
            conn,
            doc_id=doc_id,
            profile=profile,
            bond_type=bond_type,
        )
        inserted_risk_factors = _replace_risk_factors(conn, doc_id=doc_id, rows=risk_rows)
        inserted_security_packages = _replace_security_package(conn, doc_id=doc_id, row=security_row)

        if dry_run:
            conn.rollback()
        else:
            conn.commit()
    finally:
        conn.close()

    return BackfillSummary(
        document_id=doc_id,
        inserted_risk_factors=inserted_risk_factors,
        inserted_security_packages=inserted_security_packages,
        dry_run=dry_run,
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Backfill healthcare obligor profile risk/security rows into corpus.db.",
    )
    parser.add_argument(
        "--profile-json",
        type=Path,
        default=_default_profile_json(),
        help="Path to obligor profile JSON.",
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=_default_db_path(),
        help="Path to healthcare corpus SQLite database.",
    )
    parser.add_argument(
        "--bond-type",
        default="conduit_revenue",
        help="deal_structures.bond_type value for the backfilled profile document.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Execute transformations without committing database changes.",
    )
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    profile_json = args.profile_json.resolve()
    db_path = args.db_path.resolve()
    if not profile_json.exists():
        parser.error(f"Profile JSON not found: {profile_json}")
    if not db_path.exists():
        parser.error(f"Database not found: {db_path}")

    summary = backfill(
        profile_json=profile_json,
        db_path=db_path,
        bond_type=str(args.bond_type).strip() or "conduit_revenue",
        dry_run=bool(args.dry_run),
    )
    print(
        json.dumps(
            {
                "document_id": summary.document_id,
                "inserted_risk_factors": summary.inserted_risk_factors,
                "inserted_security_packages": summary.inserted_security_packages,
                "dry_run": summary.dry_run,
                "profile_json": str(profile_json),
                "db_path": str(db_path),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
