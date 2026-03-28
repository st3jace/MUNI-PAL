"""Obligor-to-ticker mapping for the multi-sector bond universe.

Bridges two data worlds:
  - Bond side: EMMA CUSIPs, OS extractions, rating actions, financial reports
    with issuer/obligor/borrower names (inconsistent, long-form)
  - Equity side: sector tickers with daily price history and
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


# ---------------------------------------------------------------------------
# Waste sector obligors
# ---------------------------------------------------------------------------
WASTE_OBLIGORS: list[ObligorProfile] = [
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

# ---------------------------------------------------------------------------
# Healthcare sector obligors
# ---------------------------------------------------------------------------
HEALTHCARE_OBLIGORS: list[ObligorProfile] = [
    ObligorProfile(
        canonical_name="Chiricahua Community Health Centers Inc",
        ticker=None,  # Nonprofit FQHC — no equity ticker
        aliases=[
            "chiricahua community health center",
            "chiricahua comm health center",
            "chiricahua comm heath center",  # Typo variant in parcel records
            "cchci",
            "chiricahua health",
        ],
        cusips=[],  # Pre-issuance — no CUSIP yet
        sector="healthcare",
    ),
]


# ---------------------------------------------------------------------------
# WTE (Waste-to-Energy) sector obligors — crawled from EMMA Mar 2026
# Two tiers:
#   1. Corporate borrowers with equity tickers (behind conduit IDA bonds)
#   2. Municipal/IDA conduit issuers (bond-only, use Phase 6 synthetic returns)
# ---------------------------------------------------------------------------
WTE_OBLIGORS: list[ObligorProfile] = [
    # --- Tier 1: Corporate borrowers with equity tickers ---
    ObligorProfile(
        canonical_name="Dominion Energy Inc",
        ticker="D",
        aliases=[
            "dominion energy",
            "virginia electric and power",
            "va electric and power",
            "virginia power fuel securitization",
        ],
        sector="wte",
    ),
    ObligorProfile(
        canonical_name="The Southern Company",
        ticker="SO",
        aliases=[
            "southern company",
            "the southern company",
            "development authority of burke county",
        ],
        sector="wte",
    ),
    ObligorProfile(
        canonical_name="Nucor Corporation",
        ticker="NUE",
        aliases=[
            "nucor",
            "nucor corporation",
            "development authority of bartow county",
        ],
        sector="wte",
    ),
    ObligorProfile(
        canonical_name="ArcelorMittal",
        ticker="MT",
        aliases=[
            "arcelormittal",
            "arcelor mittal",
        ],
        sector="wte",
    ),
    ObligorProfile(
        canonical_name="United States Steel Corporation",
        ticker=None,  # Delisted (Nippon Steel acquisition)
        aliases=[
            "united states steel",
            "u.s. steel",
            "u s steel",
            "us steel",
        ],
        sector="wte",
    ),
    ObligorProfile(
        canonical_name="BP plc",
        ticker="BP",
        aliases=[
            "bp p.l.c",
            "bp plc",
            "city of whiting",
            "whiting indiana",
        ],
        sector="wte",
    ),
    ObligorProfile(
        canonical_name="Waste Management Inc",
        ticker="WM",
        aliases=[
            "waste management",
            "wm holdings",
        ],
        sector="wte",
    ),
    ObligorProfile(
        canonical_name="Republic Services Inc",
        ticker="RSG",
        aliases=[
            "republic services",
        ],
        sector="wte",
    ),
    ObligorProfile(
        canonical_name="GFL Environmental Inc",
        ticker="GFL",
        aliases=[
            "gfl environmental",
        ],
        sector="wte",
    ),
    ObligorProfile(
        canonical_name="Reworld Holding Corporation",
        ticker=None,  # Private since 2021 (EQT acquisition of Covanta)
        aliases=[
            "reworld",
            "covanta holding",
            "covanta",
        ],
        sector="wte",
    ),
    ObligorProfile(
        canonical_name="Core Natural Resources Inc",
        ticker="CNR",  # Formerly CEIX (CONSOL Energy)
        aliases=[
            "core natural resources",
            "consol energy",
        ],
        sector="wte",
    ),
    ObligorProfile(
        canonical_name="Novelis Inc",
        ticker=None,  # Private (owned by Hindalco/Aditya Birla)
        aliases=[
            "novelis",
            "novelis inc",
            "novelis corporation",
        ],
        sector="wte",
    ),
    # --- Tier 2: Municipal/IDA conduit issuers (bond-only) ---
    ObligorProfile(
        canonical_name="Cumberland County (NJ)",
        ticker=None,
        aliases=["cumberland county", "cumberland county industrial"],
        sector="wte",
    ),
    ObligorProfile(
        canonical_name="FL Development Finance Corp",
        ticker=None,
        aliases=["florida development finance", "fl dev finance"],
        sector="wte",
    ),
    ObligorProfile(
        canonical_name="CA Municipal Finance Authority",
        ticker=None,
        aliases=["california municipal finance", "ca municipal finance"],
        sector="wte",
    ),
    ObligorProfile(
        canonical_name="PA EDFA",
        ticker=None,
        aliases=["pennsylvania economic development financing", "pa edfa", "pa economic dev"],
        sector="wte",
    ),
    ObligorProfile(
        canonical_name="Northern CA Sanitation Agencies",
        ticker=None,
        aliases=["northern california sanitation", "northern ca sanitation"],
        sector="wte",
    ),
    ObligorProfile(
        canonical_name="Iowa Finance Authority",
        ticker=None,
        aliases=["iowa finance authority"],
        sector="wte",
    ),
    ObligorProfile(
        canonical_name="NJ Infrastructure Bank",
        ticker=None,
        aliases=["new jersey infrastructure", "nj infrastructure"],
        sector="wte",
    ),
    ObligorProfile(
        canonical_name="Brazoria County IDC (TX)",
        ticker=None,
        aliases=["brazoria county", "brazoria county industrial"],
        sector="wte",
    ),
    ObligorProfile(
        canonical_name="Mission Economic Development Corp",
        ticker=None,
        aliases=["mission economic development", "mission economic dev"],
        sector="wte",
    ),
    ObligorProfile(
        canonical_name="City of Osceola (AR)",
        ticker=None,
        aliases=["city of osceola", "osceola, arkansas"],
        sector="wte",
    ),
    ObligorProfile(
        canonical_name="Jersey City MUA",
        ticker=None,
        aliases=["jersey city municipal utilities", "jersey city mua"],
        sector="wte",
    ),
    ObligorProfile(
        canonical_name="Sacramento Sanitation District",
        ticker=None,
        aliases=["sacramento area sewer", "sacramento regional county sanitation"],
        sector="wte",
    ),
]


# ---------------------------------------------------------------------------
# Sector registry
# ---------------------------------------------------------------------------
SECTOR_OBLIGORS: dict[str, list[ObligorProfile]] = {
    "waste": WASTE_OBLIGORS,
    "healthcare": HEALTHCARE_OBLIGORS,
    "wte": WTE_OBLIGORS,
}

# Backward-compatible alias
KNOWN_OBLIGORS = WASTE_OBLIGORS


def _get_current_sector() -> str:
    """Get the active sector from settings (lazy import to avoid circular)."""
    from ..config import get_settings
    return get_settings().sector


def get_obligors_for_sector(sector: str | None = None) -> list[ObligorProfile]:
    """Get obligor profiles for a specific sector."""
    s = sector or _get_current_sector()
    return SECTOR_OBLIGORS.get(s, [])


# Ticker lookup (built lazily from all sectors)
_TICKER_TO_OBLIGOR: dict[str, ObligorProfile] | None = None


def _get_ticker_map() -> dict[str, ObligorProfile]:
    global _TICKER_TO_OBLIGOR
    if _TICKER_TO_OBLIGOR is None:
        _TICKER_TO_OBLIGOR = {
            o.ticker: o
            for obligors in SECTOR_OBLIGORS.values()
            for o in obligors
            if o.ticker
        }
    return _TICKER_TO_OBLIGOR


def get_obligor_by_ticker(ticker: str) -> ObligorProfile | None:
    """Look up obligor profile by equity ticker symbol."""
    return _get_ticker_map().get(ticker.upper())


def match_issuer_to_obligor(name: str, sector: str | None = None) -> ObligorProfile | None:
    """Fuzzy-match an issuer/obligor/borrower name to a known obligor.

    Uses case-insensitive substring matching against all known aliases.
    Returns the first match found, or None. Defaults to the active sector.
    """
    if not name:
        return None
    name_lower = name.lower()
    for obligor in get_obligors_for_sector(sector):
        for alias in obligor.aliases:
            if alias in name_lower:
                return obligor
    return None


def match_issuer_to_ticker(name: str, sector: str | None = None) -> str | None:
    """Convenience: return ticker symbol for an issuer name, or None."""
    ob = match_issuer_to_obligor(name, sector)
    return ob.ticker if ob else None


def build_cusip_mapping(
    os_records: list[dict],
    financial_reports: list[dict] | None = None,
    rating_actions: list[dict] | None = None,
) -> dict[str, ObligorProfile]:
    """Build CUSIP-to-obligor mapping from extracted bond data.

    Scans issuer_name, obligor_name, and borrower_name fields across
    all record types, matching against known obligor aliases.

    Returns dict mapping CUSIP (or source_hash if no CUSIP) -> ObligorProfile.
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
        "Built CUSIP mapping: %d CUSIPs -> %d unique obligors",
        len(mapping), matched,
    )
    return mapping


def get_all_tickers(sector: str | None = None) -> list[str]:
    """Return all known ticker symbols for the given sector (default: active)."""
    return [o.ticker for o in get_obligors_for_sector(sector) if o.ticker]


def get_all_obligors(sector: str | None = None) -> list[ObligorProfile]:
    """Return all known obligor profiles for the given sector (default: active)."""
    return list(get_obligors_for_sector(sector))
