"""FFIEC Call Report data ingestion for Bank Analyzer.

Loads bank financial data from FFIEC CSV exports (BankFind Suite format)
and converts to BankProfile objects for scoring.
"""

from __future__ import annotations

import csv
import logging
from datetime import datetime, timezone
from pathlib import Path

from .models import BankProfile, LoanSegment

logger = logging.getLogger("bank_analyzer.ingest")


# ---------------------------------------------------------------------------
# Column mapping: CSV column name -> (segment_attr, field)
# ---------------------------------------------------------------------------

SEGMENT_MAP: dict[str, tuple[str, dict[str, str]]] = {
    "residential_first": {
        "portfolio": "Residential First Position Portfolio",
        "d30": "Residential First Position 30 89",
        "d90": "Residential First Position 90 Plus",
        "nonaccrual": "Residential First Position Nonaccrual",
        "chargeoffs": "Residential First Position Charge Offs",
        "npl": "Residential First Position Npl Ratio",
        "reo": "Residential Reo",
    },
    "residential_junior": {
        "portfolio": "Residential Junior Position Portfolio",
        "d30": "Residential Junior Position 30 89",
        "d90": "Residential Junior Position 90 Plus",
        "nonaccrual": "Residential Junior Position Nonaccrual",
        "chargeoffs": "Residential Junior Position Charge Offs",
        "npl": "Residential Junior Position Npl Ratio",
        "reo": "",  # Shared with first position REO
    },
    "heloc": {
        "portfolio": "Heloc Portfolio",
        "d30": "Heloc 30 89",
        "d90": "Heloc 90 Plus",
        "nonaccrual": "Heloc Nonaccrual",
        "chargeoffs": "Heloc Charge Offs",
        "npl": "Heloc Npl Ratio",
        "reo": "",
    },
    "commercial_non_owner": {
        "portfolio": "Commercial Non Owner Occupied Portfolio",
        "d30": "Commercial Non Owner Occupied 30 89",
        "d90": "Commercial Non Owner Occupied 90 Plus",
        "nonaccrual": "Commercial Non Owner Occupied Nonaccrual",
        "chargeoffs": "Commercial Non Owner Occupied Charge Offs",
        "npl": "Commercial Non Owner Occupied Npl Ratio",
        "reo": "Commercial Reo",
    },
    "commercial_owner": {
        "portfolio": "Commercial Owner Occupied Portfolio",
        "d30": "Commercial Owner Occupied 30 89",
        "d90": "Commercial Owner Occupied 90 Plus",
        "nonaccrual": "Commercial Owner Occupied Nonaccrual",
        "chargeoffs": "Commercial Owner Occupied Charge Offs",
        "npl": "Commercial Owner Occupied Npl Ratio",
        "reo": "",  # Shared with non-owner REO
    },
    "multifamily": {
        "portfolio": "Multifamily Portfolio",
        "d30": "Multifamily 30 89",
        "d90": "Multifamily 90 Plus",
        "nonaccrual": "Multifamily Nonaccrual",
        "chargeoffs": "Multifamily Charge Offs",
        "npl": "Multifamily Npl Ratio",
        "reo": "Multifamily Reo",
    },
    "construction_residential": {
        "portfolio": "Construction Residential Portfolio",
        "d30": "Construction Residential 30 89",
        "d90": "Construction Residential 90 Plus",
        "nonaccrual": "Construction Residential Nonaccrual",
        "chargeoffs": "Construction Residential Charge Offs",
        "npl": "Construction Residential Npl Ratio",
        "reo": "Construction Reo",
    },
    "construction_commercial": {
        "portfolio": "Construction Commercial Portfolio",
        "d30": "Construction Commercial 30 89",
        "d90": "Construction Commercial 90 Plus",
        "nonaccrual": "Construction Commercial Nonaccrual",
        "chargeoffs": "Construction Commercial Charge Offs",
        "npl": "Construction Commercial Npl Ratio",
        "reo": "",
    },
    "farmland": {
        "portfolio": "Farmland Portfolio",
        "d30": "Farmland 30 89",
        "d90": "Farmland 90 Plus",
        "nonaccrual": "Farmland Nonaccrual",
        "chargeoffs": "Farmland Charge Offs",
        "npl": "Farmland Npl Ratio",
        "reo": "Farmland Reo",
    },
    "ci": {
        "portfolio": "Ci Portfolio",
        "d30": "Ci 30 89",
        "d90": "Ci 90 Plus",
        "nonaccrual": "Ci Nonaccrual",
        "chargeoffs": "Ci Charge Offs",
        "npl": "Ci Npl Ratio",
        "reo": "",
    },
    "credit_cards": {
        "portfolio": "Credit Cards Portfolio",
        "d30": "Credit Cards 30 89",
        "d90": "Credit Cards 90 Plus",
        "nonaccrual": "Credit Cards Nonaccrual",
        "chargeoffs": "Credit Cards Charge Offs",
        "npl": "Credit Cards Npl Ratio",
        "reo": "",
    },
    "auto_loans": {
        "portfolio": "Auto Loans Portfolio",
        "d30": "Auto Loans 30 89",
        "d90": "Auto Loans 90 Plus",
        "nonaccrual": "Auto Loans Nonaccrual",
        "chargeoffs": "Auto Loans Charge Offs",
        "npl": "Auto Loans Npl Ratio",
        "reo": "",
    },
}


def _safe_float(val: str | None) -> float:
    """Parse a float from CSV, handling empty/missing values."""
    if not val or not val.strip():
        return 0.0
    clean = val.strip().replace(",", "").replace('"', "")
    try:
        return float(clean)
    except (ValueError, TypeError):
        return 0.0


def _safe_int(val: str | None) -> int:
    """Parse an int from CSV."""
    if not val or not val.strip():
        return 0
    clean = val.strip().replace(",", "").replace('"', "")
    try:
        return int(float(clean))
    except (ValueError, TypeError):
        return 0


def _build_segment(row: dict[str, str], segment_name: str, col_map: dict[str, str]) -> LoanSegment:
    """Build a LoanSegment from a CSV row using column mapping."""
    return LoanSegment(
        segment_name=segment_name,
        portfolio_balance=_safe_float(row.get(col_map["portfolio"])),
        delinquent_30_89=_safe_float(row.get(col_map["d30"])),
        delinquent_90_plus=_safe_float(row.get(col_map["d90"])),
        nonaccrual=_safe_float(row.get(col_map["nonaccrual"])),
        charge_offs=_safe_float(row.get(col_map["chargeoffs"])),
        npl_ratio=_safe_float(row.get(col_map["npl"])),
        reo=_safe_float(row.get(col_map["reo"])) if col_map.get("reo") else 0.0,
    )


def load_banks_from_csv(csv_path: Path) -> list[BankProfile]:
    """Load bank profiles from an FFIEC BankFind CSV export.

    Args:
        csv_path: Path to the CSV file.

    Returns:
        List of BankProfile objects.
    """
    csv_path = Path(csv_path)
    if not csv_path.exists():
        logger.warning("CSV file not found: %s", csv_path)
        return []

    banks: list[BankProfile] = []
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                # Build loan segments
                segments = {}
                for seg_attr, col_map in SEGMENT_MAP.items():
                    segments[seg_attr] = _build_segment(row, seg_attr, col_map)

                profile = BankProfile(
                    bank_name=row.get("Bank Name", "").strip().strip('"'),
                    id_rssd=_safe_int(row.get("Id Rssd")),
                    fdic_cert=_safe_int(row.get("Fdic Cert Number")) or None,
                    city=row.get("City", "").strip(),
                    state=row.get("State", "").strip(),
                    postal_code=row.get("Postal Code", "").strip(),
                    website=row.get("Website Url", "").strip(),
                    total_assets=_safe_float(row.get("Total Assets")),
                    risk_based_capital_ratio=_safe_float(row.get("Risk Based Capital Ratio")) or None,
                    tier1_leverage_ratio=_safe_float(row.get("Tier1 Leverage Ratio")) or None,
                    tier1_rbc_ratio=_safe_float(row.get("Tier1 Risk Based Capital Ratio")) or None,
                    allowance_loan_losses=_safe_float(row.get("Allowance Loan Losses")),
                    provision_loan_losses=_safe_float(row.get("Provision Loan Losses")),
                    loans_held_for_sale=_safe_float(row.get("Loans Held For Sale")),
                    held_for_sale_nonaccrual=_safe_float(row.get("Held For Sale Nonaccrual")),
                    mortgage_first_liens_hfs=_safe_float(row.get("Mortgage First Liens Held For Sale")),
                    mortgages_sold_quarter=_safe_float(row.get("Mortgages Sold Quarter")),
                    ingestion_timestamp=datetime.now(timezone.utc),
                    **segments,
                )
                banks.append(profile)
            except Exception as exc:
                logger.warning("Failed to parse bank row: %s — %s", row.get("Bank Name", "?"), exc)

    logger.info("Loaded %d bank profiles from %s", len(banks), csv_path.name)
    return banks


def load_all_banks(data_dir: Path) -> list[BankProfile]:
    """Load and deduplicate banks from all CSV files in a directory.

    Banks are deduplicated by RSSD ID, keeping the record with higher
    total assets (assumes more recent/complete data).
    """
    data_dir = Path(data_dir)
    all_banks: dict[int, BankProfile] = {}

    for csv_file in sorted(data_dir.glob("bank_search_*.csv")):
        for bank in load_banks_from_csv(csv_file):
            existing = all_banks.get(bank.id_rssd)
            if existing is None or bank.total_assets > existing.total_assets:
                all_banks[bank.id_rssd] = bank

    result = sorted(all_banks.values(), key=lambda b: -b.total_assets)
    logger.info("Total unique banks after dedup: %d", len(result))
    return result
