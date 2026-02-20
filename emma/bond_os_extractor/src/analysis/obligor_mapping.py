"""Obligor-to-ticker mapping for the waste sector bond universe.

Bridges two data worlds:
  - Bond side: EMMA CUSIPs, OS extractions, rating actions, financial reports
    with issuer/obligor/borrower names (inconsistent, long-form)
  - Equity side: 19 waste sector tickers with daily price history and
    standardized financials

The mapping enables the dual-methodology integration from Summers' Standard
Model: equity fundamentals provide the dense time series for Hilbert space
analysis (Phase 4), while bond-specific data captures structural features
(covenants, enhancement, pledge type) unavailable in equity data.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

logger = logging.getLogger("bond_os_extractor.analysis.obligor_mapping")


@dataclass
class ObligorProfile:
    """Canonical obligor identity linking bond and equity data."""
    canonical_name: str
    ticker: str | None = None
    aliases: list[str] = field(default_factory=list)
    cusips: list[str] = field(default_factory=list)
    sector: str = "solid_waste"

    def __hash__(self) -> int:
        return hash(self.canonical_name)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ObligorProfile):
            return NotImplemented
        return self.canonical_name == other.canonical_name


# Known obligor-to-ticker mappings for the waste sector universe.
# Aliases are substrings matched case-insensitively against issuer/obligor/borrower names.
KNOWN_OBLIGORS: list[ObligorProfile] = [
    ObligorProfile(
        canonical_name="Waste Management Inc",
        ticker="WM",
        aliases=[
            "waste management",
            "wm holdings",
            "usa waste services",
            "wm renewable energy",
        ],
    ),
    ObligorProfile(
        canonical_name="Republic Services Inc",
        ticker="RSG",
        aliases=[
            "republic services",
            "allied waste",
            "allied waste industries",
        ],
    ),
    ObligorProfile(
        canonical_name="GFL Environmental Inc",
        ticker="GFL",
        aliases=[
            "gfl environmental",
            "gfl env",
        ],
    ),
    ObligorProfile(
        canonical_name="Casella Waste Systems Inc",
        ticker="CWST",
        aliases=[
            "casella waste",
            "casella",
        ],
    ),
    ObligorProfile(
        canonical_name="Clean Harbors Inc",
        ticker="CLH",
        aliases=[
            "clean harbors",
            "clean harbour",
        ],
    ),
    ObligorProfile(
        canonical_name="Waste Connections Inc",
        ticker="WCN",
        aliases=[
            "waste connections",
            "progressive waste",
        ],
    ),
    ObligorProfile(
        canonical_name="Stericycle Inc",
        ticker="NVRI",
        aliases=[
            "stericycle",
            "nvri",
        ],
    ),
    ObligorProfile(
        canonical_name="Veolia Environnement",
        ticker="VLTO",
        aliases=[
            "veolia",
            "vlto",
        ],
    ),
    ObligorProfile(
        canonical_name="Xylem Inc",
        ticker="XYL",
        aliases=[
            "xylem",
        ],
    ),
    ObligorProfile(
        canonical_name="Zurn Elkay Water Solutions",
        ticker="ZWS",
        aliases=[
            "zurn elkay",
            "zurn",
        ],
    ),
    ObligorProfile(
        canonical_name="Select Water Solutions",
        ticker="WTTR",
        aliases=[
            "select water",
            "select energy",
        ],
    ),
    ObligorProfile(
        canonical_name="SCWO Group",
        ticker="SCWO",
        aliases=[
            "scwo",
            "374water",
        ],
    ),
    ObligorProfile(
        canonical_name="Quest Resource Holding",
        ticker="QRHC",
        aliases=[
            "quest resource",
        ],
    ),
    ObligorProfile(
        canonical_name="Montrose Environmental Group",
        ticker="MEG",
        aliases=[
            "montrose environmental",
            "montrose env",
        ],
    ),
    ObligorProfile(
        canonical_name="ESG Clean Energy",
        ticker="ESGL",
        aliases=[
            "esg clean energy",
            "esgl",
        ],
    ),
    ObligorProfile(
        canonical_name="Digimarc Corporation",
        ticker="DXST",
        aliases=[
            "digimarc",
            "dxst",
        ],
    ),
    ObligorProfile(
        canonical_name="China Recycling Energy Corp",
        ticker="CREG",
        aliases=[
            "china recycling",
            "creg",
        ],
    ),
    ObligorProfile(
        canonical_name="YDDL Inc",
        ticker="YDDL",
        aliases=[
            "yddl",
        ],
    ),
]

# Ticker lookup
_TICKER_TO_OBLIGOR: dict[str, ObligorProfile] = {
    o.ticker: o for o in KNOWN_OBLIGORS if o.ticker
}


def get_obligor_by_ticker(ticker: str) -> ObligorProfile | None:
    """Look up obligor profile by equity ticker symbol."""
    return _TICKER_TO_OBLIGOR.get(ticker.upper())


def match_issuer_to_obligor(name: str) -> ObligorProfile | None:
    """Fuzzy-match an issuer/obligor/borrower name to a known obligor.

    Uses case-insensitive substring matching against all known aliases.
    Returns the first match found, or None.
    """
    if not name:
        return None
    name_lower = name.lower()
    for obligor in KNOWN_OBLIGORS:
        for alias in obligor.aliases:
            if alias in name_lower:
                return obligor
    return None


def match_issuer_to_ticker(name: str) -> str | None:
    """Convenience: return ticker symbol for an issuer name, or None."""
    ob = match_issuer_to_obligor(name)
    return ob.ticker if ob else None


def build_cusip_mapping(
    os_records: list[dict],
    financial_reports: list[dict] | None = None,
    rating_actions: list[dict] | None = None,
) -> dict[str, ObligorProfile]:
    """Build CUSIP-to-obligor mapping from extracted bond data.

    Scans issuer_name, obligor_name, and borrower_name fields across
    all record types, matching against known obligor aliases.

    Returns dict mapping CUSIP (or source_hash if no CUSIP) → ObligorProfile.
    """
    mapping: dict[str, ObligorProfile] = {}

    for rec in os_records:
        names_to_try = [
            rec.get("issuer_name"),
            rec.get("borrower_name"),
        ]
        cusip = rec.get("cusip_base") or rec.get("id", "")

        for name in names_to_try:
            if not name:
                continue
            obligor = match_issuer_to_obligor(name)
            if obligor:
                if cusip and cusip not in obligor.cusips:
                    obligor.cusips.append(cusip)
                mapping[cusip] = obligor
                break

    # Also scan module records
    for records in [financial_reports or [], rating_actions or []]:
        for rec in records:
            names_to_try = [
                rec.get("issuer_name"),
                rec.get("obligor_name"),
            ]
            # Use CUSIPs from the record
            rec_cusips = rec.get("cusip_references", [])
            rec_id = rec.get("id", "")

            for name in names_to_try:
                if not name:
                    continue
                obligor = match_issuer_to_obligor(name)
                if obligor:
                    for c in rec_cusips:
                        if c not in obligor.cusips:
                            obligor.cusips.append(c)
                    if rec_id:
                        mapping[rec_id] = obligor
                    break

    matched = len(set(mapping.values()))
    logger.info(
        "Built CUSIP mapping: %d CUSIPs → %d unique obligors",
        len(mapping), matched,
    )
    return mapping


def get_all_tickers() -> list[str]:
    """Return all known ticker symbols."""
    return [o.ticker for o in KNOWN_OBLIGORS if o.ticker]


def get_all_obligors() -> list[ObligorProfile]:
    """Return all known obligor profiles."""
    return list(KNOWN_OBLIGORS)
