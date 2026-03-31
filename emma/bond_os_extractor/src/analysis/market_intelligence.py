"""Sector Market Intelligence Report Generator.

Aggregates EMMA corpus data into a publishable sector benchmark report
designed as a lead magnet for municipal bond borrowers and advisors.

Pulls from all available corpus sources:
  - Official Statement extractions (deal identity, structure, security)
  - Risk factor disclosures (severity, mitigation rates)
  - Rating actions and agency factors (strengths, challenges)
  - Financial reports (DSCR, coverage, revenue metrics)
  - Security packages (pledge types, covenant thresholds)
  - Credit enhancements (LOC, insurance, surety)
  - EMMA crawler data (ratings, secondary market trades)

Handles sparse data gracefully: each section reports its data availability
so sectors with partial extraction (e.g., healthcare) produce useful
partial reports rather than failing.
"""
from __future__ import annotations

import json
import logging
import statistics
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy.engine import Engine

from ..config import get_settings
from .data_loader import (
    get_emma_ratings,
    get_emma_trades,
    load_credit_enhancements,
    load_emma_bond_data,
    load_financial_reports,
    load_os_records,
    load_rating_action_factors,
    load_rating_actions,
    load_risk_factors,
    load_security_packages,
)
from .spread_table import DEFAULT_MUNI_SPREADS

logger = logging.getLogger("bond_os_extractor.analysis.market_intelligence")


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class DataAvailability:
    """Tracks what data is available vs. pending for a section."""
    source: str
    n_records: int
    status: str  # "available", "partial", "pending"
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "source": self.source,
            "n_records": self.n_records,
            "status": self.status,
        }
        if self.note:
            d["note"] = self.note
        return d


@dataclass
class RatingDistribution:
    """Rating counts by agency and grade."""
    by_agency: dict[str, dict[str, int]] = field(default_factory=dict)
    investment_grade_pct: float = 0.0
    modal_rating: str = ""
    total_rated: int = 0
    data: DataAvailability | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "by_agency": self.by_agency,
            "investment_grade_pct": round(self.investment_grade_pct, 1),
            "modal_rating": self.modal_rating,
            "total_rated": self.total_rated,
            "data_availability": self.data.to_dict() if self.data else None,
        }


_DSCR_SMALL_SAMPLE_THRESHOLD = 30

# Sector-specific DSCR plausibility upper bounds.  Values above these
# thresholds almost certainly reflect a total-revenue / debt-service
# calculation error (should be net-revenue / debt-service).
# Source: Moody's Investor Service, S&P Global Ratings sector medians.
_DSCR_PLAUSIBILITY_UPPER: dict[str, float] = {
    "healthcare": 5.0,   # Moody's A-rated hospital median ~3.5x; values above 5x
                         # almost certainly use total revenue instead of net revenue
    "waste":      6.0,   # WTE/solid waste typical range 1.2x–4.0x
}
_DSCR_PLAUSIBILITY_DEFAULT = 20.0  # generous fallback for unknown sectors


@dataclass
class FinancialBenchmarks:
    """Aggregate financial metrics from corpus."""
    dscr_median: float | None = None
    dscr_p25: float | None = None
    dscr_p75: float | None = None
    dscr_values: list[float] = field(default_factory=list)
    dscr_sample_warning: str | None = None
    operating_margin_median: float | None = None
    net_margin_median: float | None = None
    days_cash_median: float | None = None
    leverage_median: float | None = None
    n_reports: int = 0
    data: DataAvailability | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "dscr": {
                "median": self.dscr_median,
                "p25": self.dscr_p25,
                "p75": self.dscr_p75,
                "n_values": len(self.dscr_values),
                "sample_warning": self.dscr_sample_warning,
            },
            "operating_margin_median": self.operating_margin_median,
            "net_margin_median": self.net_margin_median,
            "days_cash_on_hand_median": self.days_cash_median,
            "leverage_median": self.leverage_median,
            "n_reports": self.n_reports,
            "data_availability": self.data.to_dict() if self.data else None,
        }


@dataclass
class DealStructureProfile:
    """Aggregate deal structure characteristics."""
    n_deals: int = 0
    par_amount_total: float = 0.0
    par_amount_median: float | None = None
    par_amount_range: tuple[float, float] = (0.0, 0.0)
    bond_type_distribution: dict[str, int] = field(default_factory=dict)
    tax_status_distribution: dict[str, int] = field(default_factory=dict)
    interest_type_distribution: dict[str, int] = field(default_factory=dict)
    state_distribution: dict[str, int] = field(default_factory=dict)
    enhancement_distribution: dict[str, int] = field(default_factory=dict)
    top_issuers: list[dict[str, Any]] = field(default_factory=list)
    data: DataAvailability | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "n_deals": self.n_deals,
            "par_amount_total_usd": self.par_amount_total,
            "par_amount_median_usd": self.par_amount_median,
            "par_amount_range_usd": list(self.par_amount_range),
            "bond_type_distribution": self.bond_type_distribution,
            "tax_status_distribution": self.tax_status_distribution,
            "interest_type_distribution": self.interest_type_distribution,
            "state_distribution": self.state_distribution,
            "enhancement_distribution": self.enhancement_distribution,
            "top_issuers": self.top_issuers,
            "data_availability": self.data.to_dict() if self.data else None,
        }


@dataclass
class SecurityProfile:
    """Aggregate security/covenant characteristics."""
    pledge_type_distribution: dict[str, int] = field(default_factory=dict)
    lien_position_distribution: dict[str, int] = field(default_factory=dict)
    coverage_ratio_median: float | None = None
    coverage_ratio_values: list[float] = field(default_factory=list)
    abt_median: float | None = None
    dsrf_type_distribution: dict[str, int] = field(default_factory=dict)
    n_packages: int = 0
    data: DataAvailability | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "pledge_type_distribution": self.pledge_type_distribution,
            "lien_position_distribution": self.lien_position_distribution,
            "coverage_ratio": {
                "median": self.coverage_ratio_median,
                "n_values": len(self.coverage_ratio_values),
            },
            "additional_bonds_test_median": self.abt_median,
            "dsrf_type_distribution": self.dsrf_type_distribution,
            "n_packages": self.n_packages,
            "data_availability": self.data.to_dict() if self.data else None,
        }


@dataclass
class RiskProfile:
    """Aggregate risk factor analysis."""
    n_risk_factors: int = 0
    n_issuances_with_risk: int = 0
    category_distribution: dict[str, int] = field(default_factory=dict)
    severity_distribution: dict[str, int] = field(default_factory=dict)
    overall_mitigation_rate: float = 0.0
    mitigation_by_category: dict[str, float] = field(default_factory=dict)
    top_categories: list[dict[str, Any]] = field(default_factory=list)
    data: DataAvailability | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "n_risk_factors": self.n_risk_factors,
            "n_issuances_with_risk_disclosures": self.n_issuances_with_risk,
            "category_distribution": self.category_distribution,
            "severity_distribution": self.severity_distribution,
            "overall_mitigation_rate": round(self.overall_mitigation_rate, 3),
            "mitigation_by_category": {
                k: round(v, 3) for k, v in self.mitigation_by_category.items()
            },
            "top_categories": self.top_categories,
            "data_availability": self.data.to_dict() if self.data else None,
        }


@dataclass
class RatingAgencyPerspective:
    """What rating agencies say about this sector."""
    n_actions: int = 0
    n_factors: int = 0
    upgrade_count: int = 0
    downgrade_count: int = 0
    affirmation_count: int = 0
    top_strengths: list[str] = field(default_factory=list)
    top_challenges: list[str] = field(default_factory=list)
    agency_distribution: dict[str, int] = field(default_factory=dict)
    data: DataAvailability | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "n_rating_actions": self.n_actions,
            "n_rating_factors": self.n_factors,
            "action_distribution": {
                "upgrades": self.upgrade_count,
                "downgrades": self.downgrade_count,
                "affirmations": self.affirmation_count,
            },
            "top_strengths": self.top_strengths[:10],
            "top_challenges": self.top_challenges[:10],
            "agency_distribution": self.agency_distribution,
            "data_availability": self.data.to_dict() if self.data else None,
        }


@dataclass
class SpreadCurve:
    """Rating-to-spread curve for the sector."""
    curve: dict[str, int] = field(default_factory=dict)
    sector_typical_range: str = ""
    investment_grade_range_bps: tuple[int, int] = (0, 0)

    def to_dict(self) -> dict[str, Any]:
        return {
            "rating_to_spread_bps": self.curve,
            "sector_typical_range": self.sector_typical_range,
            "investment_grade_range_bps": list(self.investment_grade_range_bps),
        }


@dataclass
class MarketActivitySummary:
    """Secondary market activity from EMMA crawler."""
    n_cusips: int = 0
    n_trades: int = 0
    avg_trades_per_bond: float = 0.0
    price_range: tuple[float, float] = (0.0, 0.0)
    yield_range: tuple[float, float] = (0.0, 0.0)
    trade_size_median: float | None = None
    data: DataAvailability | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "n_cusips_tracked": self.n_cusips,
            "n_secondary_trades": self.n_trades,
            "avg_trades_per_bond": round(self.avg_trades_per_bond, 1),
            "price_range": list(self.price_range),
            "yield_range": list(self.yield_range),
            "trade_size_median_usd": self.trade_size_median,
            "data_availability": self.data.to_dict() if self.data else None,
        }


@dataclass
class SectorMarketIntelligence:
    """Complete sector market intelligence report."""
    sector: str
    generated_at: str
    report_version: str = "1.0"
    executive_summary: dict[str, Any] = field(default_factory=dict)
    deal_structure: DealStructureProfile = field(
        default_factory=DealStructureProfile
    )
    rating_distribution: RatingDistribution = field(
        default_factory=RatingDistribution
    )
    financial_benchmarks: FinancialBenchmarks = field(
        default_factory=FinancialBenchmarks
    )
    security_profile: SecurityProfile = field(default_factory=SecurityProfile)
    risk_profile: RiskProfile = field(default_factory=RiskProfile)
    rating_agency_perspective: RatingAgencyPerspective = field(
        default_factory=RatingAgencyPerspective
    )
    spread_curve: SpreadCurve = field(default_factory=SpreadCurve)
    market_activity: MarketActivitySummary = field(
        default_factory=MarketActivitySummary
    )
    methodology: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "analysis": "Sector Market Intelligence Report",
            "sector": self.sector,
            "generated_at": self.generated_at,
            "report_version": self.report_version,
            "executive_summary": self.executive_summary,
            "deal_structure": self.deal_structure.to_dict(),
            "rating_distribution": self.rating_distribution.to_dict(),
            "financial_benchmarks": self.financial_benchmarks.to_dict(),
            "security_profile": self.security_profile.to_dict(),
            "risk_profile": self.risk_profile.to_dict(),
            "rating_agency_perspective": (
                self.rating_agency_perspective.to_dict()
            ),
            "spread_curve": self.spread_curve.to_dict(),
            "market_activity": self.market_activity.to_dict(),
            "methodology": self.methodology,
        }


# ---------------------------------------------------------------------------
# RATING HELPERS
# ---------------------------------------------------------------------------

# Investment grade floor (BBB- / Baa3 and above)
_IG_RATINGS = {
    "AAA", "AA+", "AA", "AA-", "A+", "A", "A-",
    "BBB+", "BBB", "BBB-",
    "Aaa", "Aa1", "Aa2", "Aa3", "A1", "A2", "A3",
    "Baa1", "Baa2", "Baa3",
}


def _is_investment_grade(rating: str) -> bool:
    return rating.strip() in _IG_RATINGS


def _normalize_rating(rating: str) -> str:
    """Normalize Moody's ratings to S&P equivalent for display."""
    moody_to_sp = {
        "Aaa": "AAA", "Aa1": "AA+", "Aa2": "AA", "Aa3": "AA-",
        "A1": "A+", "A2": "A", "A3": "A-",
        "Baa1": "BBB+", "Baa2": "BBB", "Baa3": "BBB-",
        "Ba1": "BB+", "Ba2": "BB", "Ba3": "BB-",
        "B1": "B+", "B2": "B", "B3": "B-",
        "Caa1": "CCC+", "Caa2": "CCC", "Caa3": "CCC-",
        "Ca": "CC",
    }
    clean = rating.strip()
    return moody_to_sp.get(clean, clean)


def _safe_median(values: list[float]) -> float | None:
    if not values:
        return None
    return round(statistics.median(values), 4)


def _safe_percentile(values: list[float], pct: float) -> float | None:
    if not values:
        return None
    s = sorted(values)
    idx = int(len(s) * pct)
    idx = min(idx, len(s) - 1)
    return round(s[idx], 4)


# ---------------------------------------------------------------------------
# Aggregation Functions
# ---------------------------------------------------------------------------

def _build_deal_structure(
    os_records: list[dict[str, Any]],
) -> DealStructureProfile:
    """Aggregate deal structure from OS records."""
    profile = DealStructureProfile()
    profile.n_deals = len(os_records)

    if not os_records:
        profile.data = DataAvailability(
            "official_statements", 0, "pending",
            "No OS extractions available. Run batch ingest to populate.",
        )
        return profile

    par_amounts: list[float] = []
    bond_types: Counter[str] = Counter()
    tax_statuses: Counter[str] = Counter()
    interest_types: Counter[str] = Counter()
    states: Counter[str] = Counter()
    enhancements: Counter[str] = Counter()
    issuer_counts: Counter[str] = Counter()

    for r in os_records:
        par = r.get("par_amount")
        # Cap at $50B to filter extraction artifacts
        if par and isinstance(par, (int, float)) and 0 < par < 5e10:
            par_amounts.append(float(par))

        bt = r.get("bond_type")
        if bt:
            bond_types[bt.lower()] += 1

        ts = r.get("tax_status")
        if ts:
            tax_statuses[ts.lower()] += 1

        it = r.get("interest_type")
        if it:
            interest_types[it.lower()] += 1

        st = r.get("issuer_state")
        if st:
            states[st.upper()] += 1

        ce = r.get("credit_enhancement_type")
        if ce and ce.lower() != "none":
            enhancements[ce.lower()] += 1

        issuer = r.get("issuer_name") or r.get("borrower_name") or "Unknown"
        issuer_counts[issuer] += 1

    if par_amounts:
        profile.par_amount_total = sum(par_amounts)
        profile.par_amount_median = _safe_median(par_amounts)
        profile.par_amount_range = (min(par_amounts), max(par_amounts))

    profile.bond_type_distribution = dict(bond_types.most_common())
    profile.tax_status_distribution = dict(tax_statuses.most_common())
    profile.interest_type_distribution = dict(interest_types.most_common())
    profile.state_distribution = dict(states.most_common(15))
    profile.enhancement_distribution = dict(enhancements.most_common())

    profile.top_issuers = [
        {"name": name, "deal_count": count}
        for name, count in issuer_counts.most_common(10)
    ]

    profile.data = DataAvailability(
        "official_statements", len(os_records), "available",
    )
    return profile


def _build_rating_distribution(
    os_records: list[dict[str, Any]],
    rating_actions: list[dict[str, Any]],
    emma_data: list[dict[str, Any]],
) -> RatingDistribution:
    """Aggregate rating distribution from all sources."""
    dist = RatingDistribution()
    all_ratings: list[str] = []
    by_agency: dict[str, Counter[str]] = {}

    # Valid rating strings (S&P + Moody's + short-term)
    _valid_ratings = set(DEFAULT_MUNI_SPREADS.keys()) | {
        "WR", "NR", "A-1", "A-1+", "A-2", "A-3", "P-1", "P-2", "P-3",
        "F1", "F1+", "F2", "F3", "VMIG1", "VMIG2", "VMIG3",
    }

    def _is_valid_rating(s: str) -> bool:
        return s.strip() in _valid_ratings

    # Source 1: EMMA crawler ratings (richest source)
    for bond in emma_data:
        for r in bond.get("ratings", []):
            agency = r.get("agency", "")
            rating = r.get("rating", "")
            if not rating or not _is_valid_rating(rating):
                continue
            all_ratings.append(rating)
            if agency not in by_agency:
                by_agency[agency] = Counter()
            by_agency[agency][rating] += 1

    # Source 2: Rating actions (latest rating)
    for ra in rating_actions:
        new_rating = ra.get("new_rating", "")
        agency = ra.get("agency", "")
        if not new_rating or not _is_valid_rating(new_rating):
            continue
        all_ratings.append(new_rating)
        if agency not in by_agency:
            by_agency[agency] = Counter()
        by_agency[agency][new_rating] += 1

    total_sources = len(emma_data) + len(rating_actions)
    if not all_ratings:
        dist.data = DataAvailability(
            "ratings", total_sources, "pending" if total_sources == 0 else "partial",
            "No rating data extracted yet." if total_sources == 0
            else "Ratings present but could not be parsed.",
        )
        return dist

    dist.total_rated = len(all_ratings)
    dist.by_agency = {
        agency: dict(counts.most_common())
        for agency, counts in by_agency.items()
    }

    # Investment grade percentage
    ig_count = sum(1 for r in all_ratings if _is_investment_grade(r))
    dist.investment_grade_pct = (ig_count / len(all_ratings)) * 100

    # Modal rating (normalize to S&P)
    normalized = [_normalize_rating(r) for r in all_ratings]
    rating_counter = Counter(normalized)
    dist.modal_rating = rating_counter.most_common(1)[0][0]

    dist.data = DataAvailability(
        "ratings", len(all_ratings), "available",
    )
    return dist


def _build_financial_benchmarks(
    financial_reports: list[dict[str, Any]],
    *,
    sector: str = "",
) -> FinancialBenchmarks:
    """Aggregate financial metrics from extracted reports."""
    fb = FinancialBenchmarks()
    fb.n_reports = len(financial_reports)

    if not financial_reports:
        fb.data = DataAvailability(
            "financial_reports", 0, "pending",
            "No financial reports extracted. Run batch_ingest --all-types to populate.",
        )
        return fb

    dscr_vals: list[float] = []
    op_margins: list[float] = []
    net_margins: list[float] = []
    days_cash: list[float] = []
    leverage: list[float] = []

    for r in financial_reports:
        dscr = r.get("debt_service_coverage_ratio")
        dscr_upper = _DSCR_PLAUSIBILITY_UPPER.get(sector, _DSCR_PLAUSIBILITY_DEFAULT)
        if dscr and isinstance(dscr, (int, float)) and 0 < dscr < dscr_upper:
            dscr_vals.append(float(dscr))

        rev = r.get("total_revenue")
        op_inc = r.get("operating_income")
        net_inc = r.get("net_income")
        assets = r.get("total_assets")
        liabilities = r.get("total_liabilities")

        if rev and op_inc and rev > 0:
            op_margins.append(op_inc / rev)
        if rev and net_inc and rev > 0:
            net_margins.append(net_inc / rev)

        dcoh = r.get("days_cash_on_hand")
        if dcoh and isinstance(dcoh, (int, float)) and dcoh > 0:
            days_cash.append(float(dcoh))

        if assets and liabilities and assets > 0:
            leverage.append(liabilities / assets)

    fb.dscr_values = dscr_vals
    fb.dscr_median = _safe_median(dscr_vals)
    fb.dscr_p25 = _safe_percentile(dscr_vals, 0.25)
    fb.dscr_p75 = _safe_percentile(dscr_vals, 0.75)

    # Flag small DSCR sample sizes — a median from < 30 values is not
    # statistically representative and should not be presented as a benchmark.
    if dscr_vals and len(dscr_vals) < _DSCR_SMALL_SAMPLE_THRESHOLD:
        fb.dscr_sample_warning = (
            f"Based on {len(dscr_vals)} extracted values "
            f"(out of {len(financial_reports)} reports). "
            f"Sample is too small (< {_DSCR_SMALL_SAMPLE_THRESHOLD}) "
            f"to be a reliable sector benchmark. "
            f"Treat as indicative only."
        )

    fb.operating_margin_median = _safe_median(op_margins)
    fb.net_margin_median = _safe_median(net_margins)
    fb.days_cash_median = _safe_median(days_cash)
    fb.leverage_median = _safe_median(leverage)

    status = "available" if dscr_vals else "partial"
    fb.data = DataAvailability(
        "financial_reports", len(financial_reports), status,
        "" if dscr_vals else "Reports found but DSCR not extracted.",
    )
    return fb


def _build_security_profile(
    security_packages: list[dict[str, Any]],
) -> SecurityProfile:
    """Aggregate security/covenant characteristics."""
    sp = SecurityProfile()
    sp.n_packages = len(security_packages)

    if not security_packages:
        sp.data = DataAvailability(
            "security_packages", 0, "pending",
            "No security package data available.",
        )
        return sp

    pledge_types: Counter[str] = Counter()
    lien_positions: Counter[str] = Counter()
    coverage_vals: list[float] = []
    abt_vals: list[float] = []
    dsrf_types: Counter[str] = Counter()

    for pkg in security_packages:
        pt = pkg.get("pledge_type")
        if pt:
            pledge_types[pt.lower()] += 1

        lp = pkg.get("lien_position")
        if lp:
            lien_positions[lp.lower()] += 1

        cov = pkg.get("min_coverage_ratio")
        if cov and isinstance(cov, (int, float)) and 0 < cov < 100:
            coverage_vals.append(float(cov))

        abt = pkg.get("additional_bonds_hist_coverage")
        if abt and isinstance(abt, (int, float)) and 0 < abt < 100:
            abt_vals.append(float(abt))

        dsrf = pkg.get("dsrf_type")
        if dsrf:
            dsrf_types[dsrf.lower()] += 1

    sp.pledge_type_distribution = dict(pledge_types.most_common())
    sp.lien_position_distribution = dict(lien_positions.most_common())
    sp.coverage_ratio_values = coverage_vals
    sp.coverage_ratio_median = _safe_median(coverage_vals)
    sp.abt_median = _safe_median(abt_vals)
    sp.dsrf_type_distribution = dict(dsrf_types.most_common())

    sp.data = DataAvailability(
        "security_packages", len(security_packages), "available",
    )
    return sp


# Risk categories that are sector-specific and should be excluded from
# other sectors to avoid cross-sector contamination in the MIR.
_SECTOR_EXCLUDED_RISK_CATEGORIES: dict[str, set[str]] = {
    "healthcare": {
        "feedstock_supply",    # WTE-specific
        "waste_volume",        # WTE-specific
        "tipping_fee",         # WTE-specific
        "landfill_capacity",   # WTE-specific
    },
    "waste": {
        "payer_mix",                   # Healthcare-specific
        "reimbursement_rate",          # Healthcare-specific
        "certificate_of_need",         # Healthcare-specific
        "patient_volume",              # Healthcare-specific
    },
}


def _build_risk_profile(
    risk_factors: list[dict[str, Any]],
    sector: str | None = None,
) -> RiskProfile:
    """Aggregate risk factor analysis.

    When *sector* is provided, filters out risk categories that belong to
    other sectors (e.g. feedstock_supply in a healthcare report).
    """
    excluded = _SECTOR_EXCLUDED_RISK_CATEGORIES.get(
        (sector or "").lower(), set()
    )
    if excluded:
        risk_factors = [
            rf for rf in risk_factors
            if rf.get("category", "unknown") not in excluded
        ]

    rp = RiskProfile()
    rp.n_risk_factors = len(risk_factors)

    if not risk_factors:
        rp.data = DataAvailability(
            "risk_factors", 0, "pending",
            "No risk factor data extracted. Run batch ingest to populate.",
        )
        return rp

    doc_ids = set()
    categories: Counter[str] = Counter()
    severities: Counter[str] = Counter()
    mitigated_count = 0
    cat_mitigated: dict[str, int] = {}
    cat_total: dict[str, int] = {}

    for rf in risk_factors:
        doc_ids.add(rf.get("document_id"))
        cat = rf.get("category", "unknown")
        categories[cat] += 1
        cat_total[cat] = cat_total.get(cat, 0) + 1

        sev = rf.get("severity_implied", "boilerplate")
        severities[sev] += 1

        if rf.get("mitigation_described"):
            mitigated_count += 1
            cat_mitigated[cat] = cat_mitigated.get(cat, 0) + 1

    rp.n_issuances_with_risk = len(doc_ids)
    rp.category_distribution = dict(categories.most_common())
    rp.severity_distribution = dict(severities.most_common())
    rp.overall_mitigation_rate = (
        mitigated_count / len(risk_factors) if risk_factors else 0
    )

    rp.mitigation_by_category = {
        cat: (cat_mitigated.get(cat, 0) / total) if total > 0 else 0
        for cat, total in cat_total.items()
    }

    # Top categories with detail
    rp.top_categories = [
        {
            "category": cat,
            "count": count,
            "pct_of_total": round(count / len(risk_factors) * 100, 1),
            "mitigation_rate": round(
                rp.mitigation_by_category.get(cat, 0) * 100, 1
            ),
        }
        for cat, count in categories.most_common(10)
    ]

    rp.data = DataAvailability(
        "risk_factors", len(risk_factors), "available",
    )
    return rp


def _build_rating_agency_perspective(
    rating_actions: list[dict[str, Any]],
    rating_factors: list[dict[str, Any]],
) -> RatingAgencyPerspective:
    """Aggregate rating agency strengths/challenges."""
    rap = RatingAgencyPerspective()
    rap.n_actions = len(rating_actions)
    rap.n_factors = len(rating_factors)

    if not rating_actions and not rating_factors:
        rap.data = DataAvailability(
            "rating_actions", 0, "pending",
            "No rating action data. Run batch_ingest --all-types to populate.",
        )
        return rap

    agencies: Counter[str] = Counter()
    for ra in rating_actions:
        agency = ra.get("agency", "Unknown")
        agencies[agency] += 1

        action = (ra.get("action_type") or "").lower()
        if "upgrade" in action:
            rap.upgrade_count += 1
        elif "downgrade" in action:
            rap.downgrade_count += 1
        elif "affirm" in action:
            rap.affirmation_count += 1

    rap.agency_distribution = dict(agencies.most_common())

    strengths: list[str] = []
    challenges: list[str] = []
    for rf in rating_factors:
        factor_type = (rf.get("factor_type") or "").lower()
        text = rf.get("text", "")
        if not text:
            continue
        # Truncate to first sentence for readability
        short = text.split(".")[0].strip() + "." if "." in text else text[:120]
        if factor_type == "strength":
            strengths.append(short)
        elif factor_type == "challenge":
            challenges.append(short)

    # Deduplicate by taking unique first 80 chars
    seen_s: set[str] = set()
    for s in strengths:
        key = s[:80].lower()
        if key not in seen_s:
            seen_s.add(key)
            rap.top_strengths.append(s)

    seen_c: set[str] = set()
    for c in challenges:
        key = c[:80].lower()
        if key not in seen_c:
            seen_c.add(key)
            rap.top_challenges.append(c)

    status = "available" if rating_factors else "partial"
    rap.data = DataAvailability(
        "rating_actions", len(rating_actions) + len(rating_factors), status,
    )
    return rap


def _build_spread_curve() -> SpreadCurve:
    """Build the rating-to-spread reference curve."""
    # Filter to S&P scale only (avoid Moody's duplicates)
    sp_ratings = [
        "AAA", "AA+", "AA", "AA-",
        "A+", "A", "A-",
        "BBB+", "BBB", "BBB-",
        "BB+", "BB", "BB-",
        "B+", "B", "B-",
    ]
    curve = {r: DEFAULT_MUNI_SPREADS[r] for r in sp_ratings}
    return SpreadCurve(
        curve=curve,
        sector_typical_range="A- to BBB+ (62-110 bps over AAA MMD)",
        investment_grade_range_bps=(0, 190),
    )


def _build_market_activity(
    emma_data: list[dict[str, Any]],
) -> MarketActivitySummary:
    """Aggregate secondary market activity from EMMA crawler."""
    mas = MarketActivitySummary()
    mas.n_cusips = len(emma_data)

    if not emma_data:
        mas.data = DataAvailability(
            "emma_crawler", 0, "pending",
            "No EMMA crawler data available.",
        )
        return mas

    all_prices: list[float] = []
    all_yields: list[float] = []
    all_sizes: list[float] = []
    total_trades = 0

    for bond in emma_data:
        trades = get_emma_trades(bond)
        total_trades += len(trades)
        for t in trades:
            price = t.get("price")
            if price and isinstance(price, (int, float)) and 0 < price < 200:
                all_prices.append(price)
            yld = t.get("yield")
            if yld:
                try:
                    y = float(str(yld).rstrip("%"))
                    if 0 < y < 30:
                        all_yields.append(y)
                except (ValueError, TypeError):
                    pass
            amt = t.get("trade_amount")
            if amt and isinstance(amt, (int, float)) and amt > 0:
                all_sizes.append(amt)

    mas.n_trades = total_trades
    mas.avg_trades_per_bond = (
        total_trades / len(emma_data) if emma_data else 0
    )
    if all_prices:
        mas.price_range = (round(min(all_prices), 2), round(max(all_prices), 2))
    if all_yields:
        mas.yield_range = (round(min(all_yields), 3), round(max(all_yields), 3))
    mas.trade_size_median = _safe_median(all_sizes)

    mas.data = DataAvailability(
        "emma_crawler", len(emma_data), "available",
    )
    return mas


def _build_executive_summary(
    sector: str,
    deal_structure: DealStructureProfile,
    rating_dist: RatingDistribution,
    fin_bench: FinancialBenchmarks,
    risk_prof: RiskProfile,
    market_act: MarketActivitySummary,
) -> dict[str, Any]:
    """Generate executive summary from aggregated sections.

    The executive summary is designed to be the first thing a Healthcare
    Operator or Finance Director reads. It frames the report in terms of
    what they will learn, why it matters to their capital planning, and
    what actionable benchmarks they can expect.
    """
    # Count available vs. pending sections
    sections = [
        deal_structure.data,
        rating_dist.data,
        fin_bench.data,
        risk_prof.data,
        market_act.data,
    ]
    available = sum(1 for s in sections if s and s.status == "available")
    pending = sum(1 for s in sections if s and s.status == "pending")
    partial = sum(1 for s in sections if s and s.status == "partial")

    # --- Sector-aware narrative pieces ---
    sector_lower = sector.lower().replace("_", " ")
    sector_title = sector.replace("_", " ").title()

    # Build the par value string
    par_str = ""
    if deal_structure.par_amount_total > 0:
        par_b = deal_structure.par_amount_total / 1e9
        if par_b >= 1:
            par_str = f"${par_b:.1f}B"
        else:
            par_m = deal_structure.par_amount_total / 1e6
            par_str = f"${par_m:.0f}M"

    # Audience-facing introduction
    if sector_lower == "healthcare":
        audience_intro = (
            "Whether you are a hospital CFO evaluating a capital expansion, "
            "a health system Finance Director weighing refinancing options, or "
            "an administrator planning your next facility project — this report "
            "gives you the market context you need before engaging advisors or "
            "entering the bond market."
        )
    elif sector_lower == "waste":
        audience_intro = (
            "Whether you are a solid waste authority evaluating a new facility, "
            "a county finance director considering revenue bond capacity, or an "
            "operator planning a waste-to-energy project — this report gives you "
            "the market context you need before engaging advisors or entering "
            "the bond market."
        )
    else:
        audience_intro = (
            f"Whether you are a {sector_lower} operator planning a capital "
            f"project or a finance director evaluating bond capacity — this "
            f"report gives you the market context you need before engaging "
            f"advisors or entering the bond market."
        )

    # What's inside
    report_guide_items: list[str] = []
    if deal_structure.n_deals > 0:
        report_guide_items.append(
            f"**Deal structure benchmarks** drawn from "
            f"{deal_structure.n_deals} comparable transactions"
            f" ({par_str} in par value)" if par_str else
            f"**Deal structure benchmarks** drawn from "
            f"{deal_structure.n_deals} comparable transactions"
        )
    if rating_dist.total_rated > 0:
        report_guide_items.append(
            f"**Credit rating distribution** showing where your peers land "
            f"({rating_dist.investment_grade_pct:.0f}% investment grade, "
            f"modal rating {rating_dist.modal_rating})"
        )
    if fin_bench.dscr_median is not None:
        dscr_n = len(fin_bench.dscr_values)
        dscr_caveat = (
            f" (based on {dscr_n} extracted values — treat as indicative)"
            if dscr_n < _DSCR_SMALL_SAMPLE_THRESHOLD else ""
        )
        report_guide_items.append(
            f"**Financial benchmarks** including median debt service coverage "
            f"of {fin_bench.dscr_median:.2f}x{dscr_caveat} — the number "
            f"rating agencies and underwriters will compare you against"
        )
    if risk_prof.n_risk_factors > 0:
        top_cat = risk_prof.top_categories[0] if risk_prof.top_categories else {}
        cat_name = top_cat.get("category", "financial")
        report_guide_items.append(
            f"**Risk factor analysis** cataloging {risk_prof.n_risk_factors} "
            f"disclosed risks across {risk_prof.n_issuances_with_risk} "
            f"issuances — so you know what rating agencies are flagging "
            f"(top category: {cat_name})"
        )
    if market_act.n_trades > 0:
        report_guide_items.append(
            f"**Secondary market activity** across "
            f"{market_act.n_cusips} tracked bonds and "
            f"{market_act.n_trades:,} trades — showing real investor demand "
            f"and pricing for {sector_lower} credits"
        )

    # Why it matters
    why_it_matters = (
        f"Bond issuance is one of the largest financial decisions a "
        f"{sector_lower} organization will make. The difference between "
        f"entering the market informed versus uninformed can mean millions "
        f"of dollars in total debt service cost over the life of a bond. "
        f"This report gives you the same market intelligence that "
        f"institutional investors and rating agencies use — so you enter "
        f"conversations with advisors and underwriters on equal footing."
    )

    # What you'll walk away with
    takeaways = [
        "A clear picture of how your sector's bond market is structured",
        "Concrete financial benchmarks to measure your readiness against",
        "Awareness of the risk factors that rating agencies care about most",
        "Market pricing context so you understand what your credit profile "
        "means in basis points and dollars",
    ]

    # Legacy key_findings (kept for JSON consumers)
    key_findings: list[str] = []
    if deal_structure.n_deals > 0:
        key_findings.append(
            f"{deal_structure.n_deals} deals analyzed"
            f" totaling {par_str} in par value" if par_str else
            f"{deal_structure.n_deals} deals analyzed"
        )
    if rating_dist.total_rated > 0:
        key_findings.append(
            f"{rating_dist.investment_grade_pct:.0f}% investment grade; "
            f"modal rating {rating_dist.modal_rating}"
        )
    if fin_bench.dscr_median is not None:
        dscr_n = len(fin_bench.dscr_values)
        dscr_note = f", n={dscr_n}" if dscr_n < _DSCR_SMALL_SAMPLE_THRESHOLD else ""
        key_findings.append(
            f"Median DSCR {fin_bench.dscr_median:.2f}x "
            f"(IQR: {fin_bench.dscr_p25 or 0:.2f}x - "
            f"{fin_bench.dscr_p75 or 0:.2f}x{dscr_note})"
        )
    if risk_prof.n_risk_factors > 0:
        top_cat = risk_prof.top_categories[0] if risk_prof.top_categories else {}
        key_findings.append(
            f"{risk_prof.n_risk_factors} risk factors across "
            f"{risk_prof.n_issuances_with_risk} issuances; "
            f"top category: {top_cat.get('category', 'N/A')} "
            f"({top_cat.get('pct_of_total', 0):.0f}%)"
        )
    if market_act.n_trades > 0:
        key_findings.append(
            f"{market_act.n_cusips} CUSIPs tracked with "
            f"{market_act.n_trades} secondary market trades"
        )

    return {
        "sector": sector,
        "sector_title": sector_title,
        "report_completeness": {
            "available_sections": available,
            "partial_sections": partial,
            "pending_sections": pending,
            "total_sections": len(sections),
        },
        "audience_intro": audience_intro,
        "report_guide": report_guide_items,
        "why_it_matters": why_it_matters,
        "takeaways": takeaways,
        "key_findings": key_findings,
        "data_freshness": datetime.utcnow().strftime("%Y-%m-%d"),
    }


# ---------------------------------------------------------------------------
# Main Generator
# ---------------------------------------------------------------------------

def generate_market_intelligence(
    engine: Engine,
    emma_data: list[dict[str, Any]] | None = None,
) -> SectorMarketIntelligence:
    """Generate a complete Sector Market Intelligence Report.

    Aggregates all available corpus data for the active sector into
    a structured report. Handles missing/sparse data gracefully.

    Args:
        engine: SQLAlchemy engine for the sector's corpus.db.
        emma_data: Pre-loaded EMMA crawler data. If None, loads from disk.

    Returns:
        SectorMarketIntelligence with all sections populated.
    """
    settings = get_settings()
    sector = settings.sector
    logger.info("Generating market intelligence for sector: %s", sector)

    # Load all data sources (each loader handles missing tables gracefully)
    os_records = load_os_records(engine)
    financial_reports = load_financial_reports(engine)
    rating_actions = load_rating_actions(engine)
    risk_factors = load_risk_factors(engine)
    security_packages = load_security_packages(engine)
    rating_factors = load_rating_action_factors(engine)

    if emma_data is None:
        emma_data = load_emma_bond_data()

    logger.info(
        "Data loaded — OS: %d, Financial: %d, Ratings: %d, "
        "Risk: %d, Security: %d, EMMA: %d",
        len(os_records), len(financial_reports), len(rating_actions),
        len(risk_factors), len(security_packages), len(emma_data),
    )

    # Build each section
    deal_structure = _build_deal_structure(os_records)
    rating_dist = _build_rating_distribution(
        os_records, rating_actions, emma_data,
    )
    fin_bench = _build_financial_benchmarks(financial_reports, sector=sector)
    security_prof = _build_security_profile(security_packages)
    risk_prof = _build_risk_profile(risk_factors, sector=sector)
    rating_perspective = _build_rating_agency_perspective(
        rating_actions, rating_factors,
    )
    spread_curve = _build_spread_curve()
    market_activity = _build_market_activity(emma_data)

    exec_summary = _build_executive_summary(
        sector, deal_structure, rating_dist, fin_bench,
        risk_prof, market_activity,
    )

    methodology = {
        "data_sources": [
            {
                "name": "Official Statement Extractions",
                "description": "PDF extraction pipeline (pdfplumber + Claude AI)",
                "n_records": len(os_records),
            },
            {
                "name": "EMMA Secondary Market Data",
                "description": "MSRB EMMA crawler (Playwright-based)",
                "n_records": len(emma_data),
            },
            {
                "name": "Financial Reports",
                "description": "10-K/CAFR extraction (table + AI)",
                "n_records": len(financial_reports),
            },
            {
                "name": "Rating Actions",
                "description": "Rating agency action extraction",
                "n_records": len(rating_actions),
            },
            {
                "name": "Risk Factor Disclosures",
                "description": "OS risk factor extraction with severity/mitigation",
                "n_records": len(risk_factors),
            },
        ],
        "spread_curve_source": (
            "Bloomberg Municipal Curve Analytics / ICE MMD curves. "
            "Spreads in basis points over AAA MMD."
        ),
        "limitations": [
            "Corpus limited to bonds indexed on MSRB EMMA.",
            "Financial metrics from extracted documents; may have extraction gaps.",
            "Rating data reflects most recent extracted action, not real-time.",
            "Spread curve is sector-generic; individual deals vary.",
        ],
    }

    report = SectorMarketIntelligence(
        sector=sector,
        generated_at=datetime.utcnow().isoformat() + "Z",
        executive_summary=exec_summary,
        deal_structure=deal_structure,
        rating_distribution=rating_dist,
        financial_benchmarks=fin_bench,
        security_profile=security_prof,
        risk_profile=risk_prof,
        rating_agency_perspective=rating_perspective,
        spread_curve=spread_curve,
        market_activity=market_activity,
        methodology=methodology,
    )

    logger.info("Market intelligence report generated for %s", sector)
    return report


# ---------------------------------------------------------------------------
# Export Functions
# ---------------------------------------------------------------------------

def export_json(
    report: SectorMarketIntelligence,
    output_path: Path | None = None,
) -> Path:
    """Export the report as JSON."""
    if output_path is None:
        output_path = (
            get_settings().analysis_dir / "market_intelligence_report.json"
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report.to_dict(), f, indent=2, default=str)

    logger.info("Exported JSON to %s", output_path)
    return output_path


def export_markdown(
    report: SectorMarketIntelligence,
    output_path: Path | None = None,
) -> Path:
    """Export the report as Markdown."""
    if output_path is None:
        output_path = (
            get_settings().analysis_dir / "market_intelligence_report.md"
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []
    _a = lines.append

    sector_title = report.sector.replace("_", " ").title()
    _a(f"# Sector Market Intelligence Report: {sector_title}")
    _a("")
    _a(f"**Generated:** {report.generated_at[:10]}")
    _a(f"**Report Version:** {report.report_version}")
    _a("")

    # Executive Summary
    es = report.executive_summary
    comp = es.get("report_completeness", {})
    _a("## Executive Summary")
    _a("")
    _a(
        f"This is a data-driven market intelligence report for the "
        f"**{sector_title}** municipal bond sector, built from analysis of "
        f"real EMMA filings, rating agency actions, and secondary market "
        f"trading data."
    )
    _a("")

    # Audience introduction — who this is for
    audience_intro = es.get("audience_intro", "")
    if audience_intro:
        _a(audience_intro)
        _a("")

    # What's inside this report
    guide_items = es.get("report_guide", [])
    if guide_items:
        _a("### What You'll Find in This Report")
        _a("")
        for item in guide_items:
            _a(f"- {item}")
        _a("")

    # Why it matters
    why_it_matters = es.get("why_it_matters", "")
    if why_it_matters:
        _a("### Why This Matters")
        _a("")
        _a(why_it_matters)
        _a("")

    # What you'll walk away with
    takeaways = es.get("takeaways", [])
    if takeaways:
        _a("### What You Should Take Away")
        _a("")
        for t in takeaways:
            _a(f"- {t}")
        _a("")

    # Key metrics at a glance (the original key_findings, relabeled)
    findings = es.get("key_findings", [])
    if findings:
        _a("### Data at a Glance")
        _a("")
        for f_text in findings:
            _a(f"- {f_text}")
        _a("")

    if comp.get("pending_sections", 0) > 0:
        _a(
            f"> **Note:** {comp['pending_sections']} section(s) are pending "
            f"additional data extraction. Run `batch_ingest --all-types` to "
            f"populate remaining sections."
        )
        _a("")

    # Deal Structure
    _a("---")
    _a("## Deal Structure Profile")
    _a("")
    ds = report.deal_structure
    if ds.n_deals > 0:
        _a(f"**Deals analyzed:** {ds.n_deals}")
        if ds.par_amount_median:
            _a(f"**Median par amount:** ${ds.par_amount_median / 1e6:.1f}M")
        if ds.par_amount_total > 0:
            _a(f"**Total par value:** ${ds.par_amount_total / 1e6:.0f}M")
        _a("")

        if ds.bond_type_distribution:
            _a("### Bond Types")
            _a("")
            _a("| Type | Count |")
            _a("|------|-------|")
            for bt, count in ds.bond_type_distribution.items():
                _a(f"| {bt} | {count} |")
            _a("")

        if ds.state_distribution:
            _a("### Geographic Distribution (Top 15)")
            _a("")
            _a("| State | Count |")
            _a("|-------|-------|")
            for state, count in ds.state_distribution.items():
                _a(f"| {state} | {count} |")
            _a("")

        if ds.top_issuers:
            _a("### Top Issuers")
            _a("")
            _a("| Issuer | Deals |")
            _a("|--------|-------|")
            for iss in ds.top_issuers[:10]:
                _a(f"| {iss['name'][:60]} | {iss['deal_count']} |")
            _a("")
    else:
        _a("*Data pending — no OS extractions available.*")
        _a("")

    # Rating Distribution
    _a("---")
    _a("## Rating Distribution")
    _a("")
    rd = report.rating_distribution
    if rd.total_rated > 0:
        _a(f"**Total rated bonds:** {rd.total_rated}")
        _a(f"**Investment grade:** {rd.investment_grade_pct:.0f}%")
        _a(f"**Modal rating:** {rd.modal_rating}")
        _a("")

        for agency, ratings in rd.by_agency.items():
            if not agency:
                continue
            _a(f"### {agency}")
            _a("")
            _a("| Rating | Count |")
            _a("|--------|-------|")
            for rating, count in sorted(ratings.items()):
                _a(f"| {rating} | {count} |")
            _a("")
    else:
        _a("*Data pending — no rating data extracted.*")
        _a("")

    # Financial Benchmarks
    _a("---")
    _a("## Financial Benchmarks")
    _a("")
    fb = report.financial_benchmarks
    if fb.n_reports > 0:
        _a(f"**Reports analyzed:** {fb.n_reports}")
        if fb.dscr_sample_warning:
            _a("")
            _a(f"> **⚠ Small sample size:** {fb.dscr_sample_warning}")
        _a("")
        _a("| Metric | Value |")
        _a("|--------|-------|")
        if fb.dscr_median is not None:
            n_dscr = len(fb.dscr_values)
            _a(f"| DSCR (median, n={n_dscr}) | {fb.dscr_median:.2f}x |")
        if fb.dscr_p25 is not None:
            _a(f"| DSCR (25th pct) | {fb.dscr_p25:.2f}x |")
        if fb.dscr_p75 is not None:
            _a(f"| DSCR (75th pct) | {fb.dscr_p75:.2f}x |")
        if fb.operating_margin_median is not None:
            _a(
                f"| Operating margin (median) "
                f"| {fb.operating_margin_median * 100:.1f}% |"
            )
        if fb.net_margin_median is not None:
            _a(
                f"| Net margin (median) "
                f"| {fb.net_margin_median * 100:.1f}% |"
            )
        if fb.days_cash_median is not None:
            _a(f"| Days cash on hand (median) | {fb.days_cash_median:.0f} |")
        if fb.leverage_median is not None:
            _a(
                f"| Leverage ratio (median) "
                f"| {fb.leverage_median:.2f}x |"
            )
        _a("")
    else:
        _a(
            "*Data pending — run `batch_ingest --all-types` to extract "
            "financial reports.*"
        )
        _a("")

    # Security Profile
    _a("---")
    _a("## Security & Covenant Profile")
    _a("")
    sp = report.security_profile
    if sp.n_packages > 0:
        _a(f"**Security packages analyzed:** {sp.n_packages}")
        _a("")

        if sp.pledge_type_distribution:
            _a("### Pledge Types")
            _a("")
            _a("| Pledge Type | Count |")
            _a("|-------------|-------|")
            for pt, count in sp.pledge_type_distribution.items():
                _a(f"| {pt} | {count} |")
            _a("")

        _a("### Covenant Thresholds")
        _a("")
        _a("| Metric | Median |")
        _a("|--------|--------|")
        if sp.coverage_ratio_median is not None:
            _a(f"| Min coverage ratio | {sp.coverage_ratio_median:.2f}x |")
        if sp.abt_median is not None:
            _a(f"| Additional bonds test | {sp.abt_median:.2f}x |")
        _a("")
    else:
        _a("*Data pending — no security package data available.*")
        _a("")

    # Risk Profile
    _a("---")
    _a("## Risk Factor Analysis")
    _a("")
    rp = report.risk_profile
    if rp.n_risk_factors > 0:
        _a(f"**Risk factors analyzed:** {rp.n_risk_factors}")
        _a(
            f"**Issuances with risk disclosures:** "
            f"{rp.n_issuances_with_risk}"
        )
        _a(
            f"**Overall mitigation rate:** "
            f"{rp.overall_mitigation_rate * 100:.0f}%"
        )
        _a("")

        if rp.top_categories:
            _a("### Risk Categories")
            _a("")
            _a("| Category | Count | % of Total | Mitigation Rate |")
            _a("|----------|-------|-----------|-----------------|")
            for tc in rp.top_categories:
                _a(
                    f"| {tc['category']} | {tc['count']} "
                    f"| {tc['pct_of_total']:.0f}% "
                    f"| {tc['mitigation_rate']:.0f}% |"
                )
            _a("")

        if rp.severity_distribution:
            _a("### Severity Distribution")
            _a("")
            _a("| Severity | Count |")
            _a("|----------|-------|")
            for sev, count in rp.severity_distribution.items():
                _a(f"| {sev} | {count} |")
            _a("")
    else:
        _a(
            "*Data pending — run `batch_ingest` to extract risk factor "
            "disclosures from Official Statements.*"
        )
        _a("")

    # Rating Agency Perspective
    _a("---")
    _a("## Rating Agency Perspective")
    _a("")
    rap = report.rating_agency_perspective
    if rap.n_actions > 0 or rap.n_factors > 0:
        _a(f"**Rating actions analyzed:** {rap.n_actions}")
        _a(f"**Rating factors extracted:** {rap.n_factors}")
        _a(
            f"**Actions:** {rap.upgrade_count} upgrades, "
            f"{rap.downgrade_count} downgrades, "
            f"{rap.affirmation_count} affirmations"
        )
        _a("")

        if rap.top_strengths:
            _a("### Cited Strengths")
            _a("")
            for s in rap.top_strengths[:10]:
                _a(f"- {s}")
            _a("")

        if rap.top_challenges:
            _a("### Cited Challenges")
            _a("")
            for c in rap.top_challenges[:10]:
                _a(f"- {c}")
            _a("")
    else:
        _a(
            "*Data pending — run `batch_ingest --all-types` to extract "
            "rating actions.*"
        )
        _a("")

    # Spread Curve
    _a("---")
    _a("## Credit Spread Reference Curve")
    _a("")
    sc = report.spread_curve
    _a(f"**Typical sector range:** {sc.sector_typical_range}")
    _a(
        f"**Investment grade range:** "
        f"{sc.investment_grade_range_bps[0]}-"
        f"{sc.investment_grade_range_bps[1]} bps"
    )
    _a("")
    _a("| Rating | Spread (bps over AAA MMD) |")
    _a("|--------|---------------------------|")
    for rating, bps in sc.curve.items():
        _a(f"| {rating} | {bps} |")
    _a("")
    _a(
        "*Spreads represent typical revenue bond pricing. "
        "Individual deals vary by structure, enhancement, and market conditions.*"
    )
    _a("")

    # Market Activity
    _a("---")
    _a("## Secondary Market Activity")
    _a("")
    ma = report.market_activity
    if ma.n_cusips > 0:
        _a(f"**CUSIPs tracked:** {ma.n_cusips}")
        _a(f"**Total secondary trades:** {ma.n_trades}")
        _a(f"**Avg trades per bond:** {ma.avg_trades_per_bond:.1f}")
        if ma.price_range != (0.0, 0.0):
            _a(
                f"**Price range:** ${ma.price_range[0]:.2f} - "
                f"${ma.price_range[1]:.2f}"
            )
        if ma.yield_range != (0.0, 0.0):
            _a(
                f"**Yield range:** {ma.yield_range[0]:.2f}% - "
                f"{ma.yield_range[1]:.2f}%"
            )
        if ma.trade_size_median is not None:
            _a(
                f"**Median trade size:** "
                f"${ma.trade_size_median / 1000:.0f}K"
            )
        _a("")
    else:
        _a("*Data pending — no EMMA crawler data available.*")
        _a("")

    # Methodology
    _a("---")
    _a("## Methodology & Data Sources")
    _a("")
    for src in report.methodology.get("data_sources", []):
        _a(f"- **{src['name']}**: {src['description']} ({src['n_records']} records)")
    _a("")
    _a("### Limitations")
    _a("")
    for lim in report.methodology.get("limitations", []):
        _a(f"- {lim}")
    _a("")
    _a("---")
    _a(f"*Report generated by Muni-Pal Bond Intelligence Engine*")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    logger.info("Exported Markdown to %s", output_path)
    return output_path
