"""Issuance Benchmarking Calculator — Phase B of the Sensing Component.

Takes prospect inputs (deal size, state, expected rating, maturity) and
returns corpus-derived benchmarks: spread estimate, peer deal comparison,
structural norms, risk profile, and PFA comparison angle.

Designed as a conversion engine: prospects who downloaded the Phase A
sector report engage deeper by benchmarking their specific issuance
against the EMMA corpus.
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
    load_emma_bond_data,
    load_financial_reports,
    load_os_ratings,
    load_os_records,
    load_rating_action_factors,
    load_rating_actions,
    load_risk_factors,
    load_security_packages,
)
from .spread_table import DEFAULT_MUNI_SPREADS, get_spread_bps

logger = logging.getLogger("bond_os_extractor.analysis.benchmarking_calculator")


# ---------------------------------------------------------------------------
# Rating utilities
# ---------------------------------------------------------------------------

# Ordered S&P scale for notch-distance calculations
_SP_SCALE = [
    "AAA", "AA+", "AA", "AA-",
    "A+", "A", "A-",
    "BBB+", "BBB", "BBB-",
    "BB+", "BB", "BB-",
    "B+", "B", "B-",
    "CCC+", "CCC", "CCC-",
    "CC", "C", "D",
]
_SP_INDEX = {r: i for i, r in enumerate(_SP_SCALE)}

# Moody's to S&P equivalence
_MOODYS_TO_SP = {
    "Aaa": "AAA", "Aa1": "AA+", "Aa2": "AA", "Aa3": "AA-",
    "A1": "A+", "A2": "A", "A3": "A-",
    "Baa1": "BBB+", "Baa2": "BBB", "Baa3": "BBB-",
    "Ba1": "BB+", "Ba2": "BB", "Ba3": "BB-",
    "B1": "B+", "B2": "B", "B3": "B-",
    "Caa1": "CCC+", "Caa2": "CCC", "Caa3": "CCC-",
    "Ca": "CC",
}

_IG_RATINGS = {
    "AAA", "AA+", "AA", "AA-", "A+", "A", "A-",
    "BBB+", "BBB", "BBB-",
    "Aaa", "Aa1", "Aa2", "Aa3", "A1", "A2", "A3",
    "Baa1", "Baa2", "Baa3",
}


def _normalize_rating(rating: str) -> str | None:
    """Convert any rating to S&P scale. Returns None if unrecognized."""
    r = rating.strip()
    if r in _SP_INDEX:
        return r
    if r in _MOODYS_TO_SP:
        return _MOODYS_TO_SP[r]
    return None


def _notch_distance(r1: str, r2: str) -> int | None:
    """Absolute notch distance between two S&P-normalized ratings."""
    n1 = _normalize_rating(r1)
    n2 = _normalize_rating(r2)
    if n1 is None or n2 is None:
        return None
    return abs(_SP_INDEX[n1] - _SP_INDEX[n2])


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class ProspectInputs:
    """What the prospect tells us about their planned issuance."""
    sector: str
    deal_size: float  # USD
    state: str  # 2-letter abbreviation
    expected_rating: str  # S&P or Moody's
    maturity_years: float  # years to final maturity


@dataclass
class SpreadEstimate:
    """Estimated credit spread for the prospect's issuance."""
    expected_spread_bps: int | None
    rating_normalized: str
    sector_median_spread_bps: int | None
    spread_vs_sector: str  # "tighter", "wider", "at_median"
    sector_spread_range: tuple[int, int] = (0, 0)
    n_rated_peers: int = 0
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "expected_spread_bps": self.expected_spread_bps,
            "rating_normalized": self.rating_normalized,
            "sector_median_spread_bps": self.sector_median_spread_bps,
            "spread_vs_sector": self.spread_vs_sector,
            "sector_spread_range_bps": list(self.sector_spread_range),
            "n_rated_peers": self.n_rated_peers,
            "note": self.note,
        }


@dataclass
class PeerDeal:
    """A single peer deal from the corpus."""
    issuer_name: str
    state: str
    par_amount: float
    rating: str
    bond_type: str
    maturity: str
    similarity_score: float  # 0-1, higher = more similar

    def to_dict(self) -> dict[str, Any]:
        return {
            "issuer_name": self.issuer_name,
            "state": self.state,
            "par_amount_usd": self.par_amount,
            "rating": self.rating,
            "bond_type": self.bond_type,
            "maturity": self.maturity,
            "similarity_score": round(self.similarity_score, 3),
        }


@dataclass
class PeerComparison:
    """Summary of peer deal matching results."""
    n_peers_found: int = 0
    peer_deals: list[PeerDeal] = field(default_factory=list)
    size_percentile: float | None = None  # prospect's deal size percentile
    peer_par_median: float | None = None
    peer_par_range: tuple[float, float] = (0.0, 0.0)

    def to_dict(self) -> dict[str, Any]:
        return {
            "n_peers_found": self.n_peers_found,
            "peer_deals": [p.to_dict() for p in self.peer_deals],
            "size_percentile": round(self.size_percentile, 1) if self.size_percentile is not None else None,
            "peer_par_median_usd": self.peer_par_median,
            "peer_par_range_usd": list(self.peer_par_range),
        }


@dataclass
class StructuralNorms:
    """Typical structural features for the peer group."""
    pledge_type_distribution: dict[str, int] = field(default_factory=dict)
    typical_coverage_ratio: float | None = None
    coverage_ratio_range: tuple[float, float] = (0.0, 0.0)
    abt_coverage_median: float | None = None
    dsrf_prevalence: float = 0.0  # % of peers with DSRF
    dsrf_types: dict[str, int] = field(default_factory=dict)
    enhancement_types: dict[str, int] = field(default_factory=dict)
    lien_position_distribution: dict[str, int] = field(default_factory=dict)
    n_packages: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "pledge_type_distribution": self.pledge_type_distribution,
            "typical_coverage_ratio": self.typical_coverage_ratio,
            "coverage_ratio_range": list(self.coverage_ratio_range),
            "abt_coverage_median": self.abt_coverage_median,
            "dsrf_prevalence_pct": round(self.dsrf_prevalence * 100, 1),
            "dsrf_types": self.dsrf_types,
            "enhancement_types": self.enhancement_types,
            "lien_position_distribution": self.lien_position_distribution,
            "n_packages": self.n_packages,
        }


@dataclass
class RiskProfile:
    """Risk landscape for the sector relevant to the prospect."""
    top_risk_categories: list[dict[str, Any]] = field(default_factory=list)
    overall_mitigation_rate: float = 0.0
    n_risk_factors: int = 0
    rating_agency_strengths: list[str] = field(default_factory=list)
    rating_agency_challenges: list[str] = field(default_factory=list)
    prospect_risk_flags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "top_risk_categories": self.top_risk_categories,
            "overall_mitigation_rate_pct": round(self.overall_mitigation_rate * 100, 1),
            "n_risk_factors": self.n_risk_factors,
            "rating_agency_strengths": self.rating_agency_strengths,
            "rating_agency_challenges": self.rating_agency_challenges,
            "prospect_risk_flags": self.prospect_risk_flags,
        }


@dataclass
class FinancialBenchmarks:
    """Financial metric benchmarks from peer group."""
    dscr_median: float | None = None
    dscr_iqr: tuple[float, float] = (0.0, 0.0)
    operating_margin_median: float | None = None
    leverage_median: float | None = None
    days_cash_median: float | None = None
    n_reports: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "dscr": {
                "median": self.dscr_median,
                "iqr": list(self.dscr_iqr),
            },
            "operating_margin_median": self.operating_margin_median,
            "leverage_median": self.leverage_median,
            "days_cash_on_hand_median": self.days_cash_median,
            "n_reports": self.n_reports,
        }


@dataclass
class PFAComparison:
    """Comparison angle vs. Public Finance Authority / conduit issuers.

    Addresses advisor insight: "Compare financing to Public Finance Authority"
    — issuers want to know how their deal stacks up against conduit alternatives.
    """
    conduit_deals_in_corpus: int = 0
    conduit_median_par: float | None = None
    conduit_rating_profile: str = ""
    conduit_states: list[str] = field(default_factory=list)
    prospect_advantages: list[str] = field(default_factory=list)
    prospect_considerations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "conduit_deals_in_corpus": self.conduit_deals_in_corpus,
            "conduit_median_par_usd": self.conduit_median_par,
            "conduit_rating_profile": self.conduit_rating_profile,
            "conduit_states": self.conduit_states,
            "prospect_advantages": self.prospect_advantages,
            "prospect_considerations": self.prospect_considerations,
        }


@dataclass
class MarketContext:
    """Secondary market context for the prospect's rating tier."""
    n_trades: int = 0
    median_yield: float | None = None
    yield_range: tuple[float, float] = (0.0, 0.0)
    median_price: float | None = None
    n_bonds_trading: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "n_trades": self.n_trades,
            "median_yield_pct": self.median_yield,
            "yield_range_pct": list(self.yield_range),
            "median_price": self.median_price,
            "n_bonds_trading": self.n_bonds_trading,
        }


@dataclass
class IssuanceBenchmark:
    """Complete benchmarking result for a prospect issuance."""
    inputs: ProspectInputs
    spread_estimate: SpreadEstimate
    peer_comparison: PeerComparison
    structural_norms: StructuralNorms
    risk_profile: RiskProfile
    financial_benchmarks: FinancialBenchmarks
    pfa_comparison: PFAComparison
    market_context: MarketContext
    generated_at: str = ""
    sector: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "meta": {
                "generated_at": self.generated_at,
                "sector": self.sector,
                "generator": "benchmarking_calculator_v1",
            },
            "inputs": {
                "deal_size_usd": self.inputs.deal_size,
                "state": self.inputs.state,
                "expected_rating": self.inputs.expected_rating,
                "maturity_years": self.inputs.maturity_years,
            },
            "spread_estimate": self.spread_estimate.to_dict(),
            "peer_comparison": self.peer_comparison.to_dict(),
            "structural_norms": self.structural_norms.to_dict(),
            "risk_profile": self.risk_profile.to_dict(),
            "financial_benchmarks": self.financial_benchmarks.to_dict(),
            "pfa_comparison": self.pfa_comparison.to_dict(),
            "market_context": self.market_context.to_dict(),
        }


# ---------------------------------------------------------------------------
# Peer matching engine
# ---------------------------------------------------------------------------

def _compute_similarity(
    record: dict[str, Any],
    inputs: ProspectInputs,
    emma_ratings: dict[str, str],
) -> float:
    """Score 0-1 similarity between a corpus deal and prospect inputs.

    Weights:
      - Rating proximity:  0.35 (most important for spread)
      - Size proximity:    0.30 (deal size affects execution)
      - State match:       0.20 (regional market dynamics)
      - Sector match:      0.15 (already filtered by sector config)
    """
    score = 0.0

    # Rating proximity (0.35 weight)
    deal_rating = None
    cusip = record.get("cusip_base", "")
    if cusip and cusip in emma_ratings:
        deal_rating = emma_ratings[cusip]
    if not deal_rating:
        # Try from OS extraction
        for field_name in ("new_rating", "rating"):
            r = record.get(field_name)
            if r:
                deal_rating = r
                break

    if deal_rating:
        dist = _notch_distance(inputs.expected_rating, deal_rating)
        if dist is not None:
            # 0 notches = 1.0, 6+ notches = 0.0
            score += 0.35 * max(0.0, 1.0 - dist / 6.0)
    else:
        score += 0.35 * 0.3  # partial credit for unrated

    # Size proximity (0.30 weight)
    par = record.get("par_amount")
    if par and isinstance(par, (int, float)) and par > 0:
        ratio = min(par, inputs.deal_size) / max(par, inputs.deal_size)
        score += 0.30 * ratio
    else:
        score += 0.30 * 0.2  # partial credit

    # State match (0.20 weight)
    state = (record.get("issuer_state") or "").strip().upper()
    if state == inputs.state.upper():
        score += 0.20
    elif state:
        score += 0.20 * 0.3  # partial credit for being a real state

    # Sector (0.15 weight) — already filtered by sector config
    score += 0.15

    return score


def _find_peer_deals(
    os_records: list[dict[str, Any]],
    inputs: ProspectInputs,
    emma_ratings: dict[str, str],
    max_peers: int = 10,
    min_similarity: float = 0.4,
) -> PeerComparison:
    """Find and rank peer deals from the corpus."""
    scored = []
    par_amounts = []

    for r in os_records:
        par = r.get("par_amount")
        if par and isinstance(par, (int, float)) and 0 < par < 5e10:
            par_amounts.append(par)

        sim = _compute_similarity(r, inputs, emma_ratings)
        if sim >= min_similarity:
            scored.append((sim, r))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:max_peers]

    peers = []
    for sim, r in top:
        peers.append(PeerDeal(
            issuer_name=r.get("issuer_name") or r.get("borrower_name") or "Unknown",
            state=(r.get("issuer_state") or "").upper(),
            par_amount=float(r.get("par_amount") or 0),
            rating="",  # filled below
            bond_type=r.get("bond_type") or "",
            maturity=r.get("final_maturity_date") or "",
            similarity_score=sim,
        ))

    # Size percentile
    size_pctl = None
    if par_amounts:
        below = sum(1 for p in par_amounts if p <= inputs.deal_size)
        size_pctl = (below / len(par_amounts)) * 100.0

    peer_pars = [p.par_amount for p in peers if p.par_amount > 0]

    return PeerComparison(
        n_peers_found=len(peers),
        peer_deals=peers,
        size_percentile=size_pctl,
        peer_par_median=statistics.median(peer_pars) if peer_pars else None,
        peer_par_range=(min(peer_pars), max(peer_pars)) if peer_pars else (0.0, 0.0),
    )


# ---------------------------------------------------------------------------
# Spread estimation
# ---------------------------------------------------------------------------

def _estimate_spread(
    inputs: ProspectInputs,
    emma_data: list[dict[str, Any]],
    rating_actions: list[dict[str, Any]] | None = None,
    os_ratings: list[dict[str, Any]] | None = None,
) -> SpreadEstimate:
    """Estimate credit spread from rating + corpus data.

    Collects sector rating distribution from multiple sources:
    EMMA crawler ratings, rating actions, and OS extraction ratings.
    """
    norm = _normalize_rating(inputs.expected_rating)
    if not norm:
        return SpreadEstimate(
            expected_spread_bps=None,
            rating_normalized=inputs.expected_rating,
            sector_median_spread_bps=None,
            spread_vs_sector="unknown",
            note=f"Unrecognized rating: {inputs.expected_rating}",
        )

    expected_bps = get_spread_bps(norm)

    # Collect sector spreads from all rating sources
    sector_spreads = []

    # Source 1: EMMA crawler ratings
    for bond in emma_data:
        for r in bond.get("ratings", []):
            rating = r.get("rating", "")
            bps = get_spread_bps(rating)
            if bps is not None:
                sector_spreads.append(bps)

    # Source 2: Rating actions (new_rating)
    for ra in (rating_actions or []):
        rating = ra.get("new_rating", "")
        bps = get_spread_bps(rating)
        if bps is not None:
            sector_spreads.append(bps)

    # Source 3: OS-embedded ratings (from the ratings table)
    for r in (os_ratings or []):
        rating = r.get("rating", "")
        bps = get_spread_bps(rating)
        if bps is not None:
            sector_spreads.append(bps)

    sector_median = None
    spread_range = (0, 0)
    vs = "unknown"
    if sector_spreads:
        sector_median = int(statistics.median(sector_spreads))
        spread_range = (min(sector_spreads), max(sector_spreads))
        if expected_bps is not None:
            if expected_bps < sector_median - 5:
                vs = "tighter"
            elif expected_bps > sector_median + 5:
                vs = "wider"
            else:
                vs = "at_median"

    return SpreadEstimate(
        expected_spread_bps=expected_bps,
        rating_normalized=norm,
        sector_median_spread_bps=sector_median,
        spread_vs_sector=vs,
        sector_spread_range=spread_range,
        n_rated_peers=len(sector_spreads),
        note=f"Spread based on {norm} over AAA MMD",
    )


# ---------------------------------------------------------------------------
# Structural norms
# ---------------------------------------------------------------------------

def _build_structural_norms(
    security_packages: list[dict[str, Any]],
    os_records: list[dict[str, Any]],
) -> StructuralNorms:
    """Aggregate structural features from corpus as norms."""
    norms = StructuralNorms()

    pledge_types: Counter[str] = Counter()
    lien_positions: Counter[str] = Counter()
    dsrf_types: Counter[str] = Counter()
    enhancement_types: Counter[str] = Counter()
    coverages: list[float] = []
    abt_coverages: list[float] = []
    has_dsrf = 0

    for sp in security_packages:
        norms.n_packages += 1
        pt = sp.get("pledge_type")
        if pt:
            pledge_types[pt] += 1

        lp = sp.get("lien_position")
        if lp:
            lien_positions[lp] += 1

        cov = sp.get("min_coverage_ratio")
        if cov and isinstance(cov, (int, float)) and 0 < cov < 100:
            coverages.append(float(cov))

        abt = sp.get("additional_bonds_hist_coverage")
        if abt and isinstance(abt, (int, float)) and 0 < abt < 100:
            abt_coverages.append(float(abt))

        dsrf = sp.get("dsrf_type")
        if dsrf:
            dsrf_types[dsrf] += 1
            has_dsrf += 1

    # Enhancement types from OS records
    for r in os_records:
        et = r.get("credit_enhancement_type")
        if et and et.lower() != "none":
            enhancement_types[et] += 1

    norms.pledge_type_distribution = dict(pledge_types.most_common(10))
    norms.lien_position_distribution = dict(lien_positions.most_common(5))
    norms.dsrf_types = dict(dsrf_types.most_common(5))
    norms.enhancement_types = dict(enhancement_types.most_common(10))

    if coverages:
        norms.typical_coverage_ratio = statistics.median(coverages)
        norms.coverage_ratio_range = (min(coverages), max(coverages))

    if abt_coverages:
        norms.abt_coverage_median = statistics.median(abt_coverages)

    if norms.n_packages > 0:
        norms.dsrf_prevalence = has_dsrf / norms.n_packages

    return norms


# ---------------------------------------------------------------------------
# Risk profile
# ---------------------------------------------------------------------------

def _build_risk_profile(
    risk_factors: list[dict[str, Any]],
    rating_action_factors: list[dict[str, Any]],
    inputs: ProspectInputs,
) -> RiskProfile:
    """Build risk landscape relevant to the prospect."""
    profile = RiskProfile()
    profile.n_risk_factors = len(risk_factors)

    # Category distribution
    cat_counts: Counter[str] = Counter()
    cat_mitigated: Counter[str] = Counter()
    for rf in risk_factors:
        cat = rf.get("category", "Other")
        cat_counts[cat] += 1
        if rf.get("mitigation_described"):
            cat_mitigated[cat] += 1

    total_mitigated = sum(cat_mitigated.values())
    if risk_factors:
        profile.overall_mitigation_rate = total_mitigated / len(risk_factors)

    top_cats = []
    for cat, count in cat_counts.most_common(8):
        mit_rate = cat_mitigated[cat] / count if count > 0 else 0
        top_cats.append({
            "category": cat,
            "count": count,
            "pct_of_total": (count / len(risk_factors) * 100) if risk_factors else 0,
            "mitigation_rate_pct": round(mit_rate * 100, 0),
        })
    profile.top_risk_categories = top_cats

    # Rating agency strengths/challenges
    strengths: Counter[str] = Counter()
    challenges: Counter[str] = Counter()
    for raf in rating_action_factors:
        ft = (raf.get("factor_type") or "").lower()
        text = raf.get("text", "")
        if not text:
            continue
        if ft in ("strength", "key_factor"):
            strengths[text] += 1
        elif ft == "challenge":
            challenges[text] += 1

    profile.rating_agency_strengths = [s for s, _ in strengths.most_common(5)]
    profile.rating_agency_challenges = [c for c, _ in challenges.most_common(5)]

    # Prospect-specific risk flags based on inputs
    norm = _normalize_rating(inputs.expected_rating)
    if norm and norm not in _IG_RATINGS:
        profile.prospect_risk_flags.append(
            f"Sub-investment-grade rating ({norm}) — expect higher disclosure requirements"
        )

    if inputs.deal_size < 10_000_000:
        profile.prospect_risk_flags.append(
            "Small deal size (<$10M) — limited market liquidity, higher relative issuance costs"
        )
    elif inputs.deal_size > 500_000_000:
        profile.prospect_risk_flags.append(
            "Large deal size (>$500M) — may require multiple tranches or institutional placement"
        )

    return profile


# ---------------------------------------------------------------------------
# Financial benchmarks
# ---------------------------------------------------------------------------

def _build_financial_benchmarks(
    financial_reports: list[dict[str, Any]],
) -> FinancialBenchmarks:
    """Aggregate financial benchmarks from corpus."""
    fb = FinancialBenchmarks()
    fb.n_reports = len(financial_reports)

    dscr_vals = []
    op_margins = []
    leverage_vals = []
    days_cash_vals = []

    for fr in financial_reports:
        dscr = fr.get("debt_service_coverage_ratio")
        if dscr and isinstance(dscr, (int, float)) and 0 < dscr < 100:
            dscr_vals.append(float(dscr))

        rev = fr.get("total_revenue")
        oi = fr.get("operating_income")
        if rev and oi and isinstance(rev, (int, float)) and isinstance(oi, (int, float)) and rev > 0:
            op_margins.append(oi / rev)

        assets = fr.get("total_assets")
        liab = fr.get("total_liabilities")
        if assets and liab and isinstance(assets, (int, float)) and isinstance(liab, (int, float)) and assets > 0:
            leverage_vals.append(liab / assets)

        dcoh = fr.get("days_cash_on_hand")
        if dcoh and isinstance(dcoh, (int, float)) and dcoh > 0:
            days_cash_vals.append(float(dcoh))

    if dscr_vals:
        dscr_vals.sort()
        fb.dscr_median = statistics.median(dscr_vals)
        n = len(dscr_vals)
        fb.dscr_iqr = (
            dscr_vals[n // 4] if n >= 4 else dscr_vals[0],
            dscr_vals[3 * n // 4] if n >= 4 else dscr_vals[-1],
        )
    if op_margins:
        fb.operating_margin_median = statistics.median(op_margins)
    if leverage_vals:
        fb.leverage_median = statistics.median(leverage_vals)
    if days_cash_vals:
        fb.days_cash_median = statistics.median(days_cash_vals)

    return fb


# ---------------------------------------------------------------------------
# PFA comparison
# ---------------------------------------------------------------------------

# Keywords that identify conduit/PFA-style issuances
_CONDUIT_KEYWORDS = [
    "public finance authority", "pfa",
    "conduit", "industrial development",
    "economic development", "development authority",
    "housing authority", "health facilities",
    "educational facilities", "cultural facilities",
]


def _build_pfa_comparison(
    os_records: list[dict[str, Any]],
    inputs: ProspectInputs,
) -> PFAComparison:
    """Compare prospect issuance against conduit/PFA deals in corpus."""
    pfa = PFAComparison()

    conduit_deals = []
    for r in os_records:
        issuer = (r.get("issuer_name") or "").lower()
        borrower = (r.get("borrower_name") or "").lower()
        series = (r.get("series_name") or "").lower()
        combined = f"{issuer} {borrower} {series}"

        if any(kw in combined for kw in _CONDUIT_KEYWORDS):
            conduit_deals.append(r)

    pfa.conduit_deals_in_corpus = len(conduit_deals)

    if not conduit_deals:
        pfa.prospect_considerations.append(
            "No conduit/PFA deals found in corpus for direct comparison"
        )
        return pfa

    # Conduit par amounts
    conduit_pars = []
    for d in conduit_deals:
        par = d.get("par_amount")
        if par and isinstance(par, (int, float)) and 0 < par < 5e10:
            conduit_pars.append(par)
    if conduit_pars:
        pfa.conduit_median_par = statistics.median(conduit_pars)

    # Conduit states
    states: Counter[str] = Counter()
    for d in conduit_deals:
        st = (d.get("issuer_state") or "").strip().upper()
        if st:
            states[st] += 1
    pfa.conduit_states = [s for s, _ in states.most_common(5)]

    # Conduit rating profile
    conduit_ig = 0
    conduit_rated = 0
    for d in conduit_deals:
        for field_name in ("new_rating", "rating"):
            r = d.get(field_name)
            if r:
                conduit_rated += 1
                if r in _IG_RATINGS:
                    conduit_ig += 1
                break
    if conduit_rated > 0:
        ig_pct = conduit_ig / conduit_rated * 100
        pfa.conduit_rating_profile = f"{ig_pct:.0f}% investment grade ({conduit_rated} rated)"

    # Generate comparison insights
    norm = _normalize_rating(inputs.expected_rating)
    if norm and norm in _IG_RATINGS:
        pfa.prospect_advantages.append(
            "Investment-grade rating supports direct issuance — "
            "potentially lower all-in cost vs. conduit structure"
        )
    if pfa.conduit_median_par and inputs.deal_size > pfa.conduit_median_par:
        pfa.prospect_advantages.append(
            f"Deal size (${inputs.deal_size / 1e6:.0f}M) exceeds conduit median "
            f"(${pfa.conduit_median_par / 1e6:.0f}M) — sufficient scale for standalone"
        )

    pfa.prospect_considerations.append(
        "Conduit issuance provides access to tax-exempt status for "
        "qualified private-activity projects"
    )
    pfa.prospect_considerations.append(
        "Direct issuance requires own credit standing; conduit uses authority's "
        "borrowing capacity"
    )
    if inputs.state.upper() not in pfa.conduit_states:
        pfa.prospect_considerations.append(
            f"No conduit deals from {inputs.state.upper()} in corpus — "
            f"state-specific conduit options may differ"
        )

    return pfa


# ---------------------------------------------------------------------------
# Market context
# ---------------------------------------------------------------------------

def _build_market_context(
    emma_data: list[dict[str, Any]],
    inputs: ProspectInputs,
) -> MarketContext:
    """Secondary market context for bonds near the prospect's rating."""
    ctx = MarketContext()
    norm = _normalize_rating(inputs.expected_rating)
    if not norm:
        return ctx

    target_bps = get_spread_bps(norm)
    if target_bps is None:
        return ctx

    # Collect trades from bonds within ±3 notches
    yields_list: list[float] = []
    prices_list: list[float] = []
    bonds_seen: set[str] = set()
    trade_count = 0

    for bond in emma_data:
        # Check if bond's rating is within range
        bond_near = False
        for r in bond.get("ratings", []):
            dist = _notch_distance(inputs.expected_rating, r.get("rating", ""))
            if dist is not None and dist <= 3:
                bond_near = True
                break

        if not bond_near:
            continue

        cusip = bond.get("snapshot", {}).get("cusip", "")
        trades = bond.get("trades", [])
        for t in trades:
            trade_count += 1
            y = t.get("yield")
            if y and isinstance(y, (int, float)) and 0 < y < 20:
                yields_list.append(float(y))
            p = t.get("price")
            if isinstance(p, str):
                try:
                    p = float(p)
                except ValueError:
                    p = None
            if p and isinstance(p, (int, float)) and 50 < p < 200:
                prices_list.append(float(p))
        if trades:
            bonds_seen.add(cusip)

    ctx.n_trades = trade_count
    ctx.n_bonds_trading = len(bonds_seen)
    if yields_list:
        ctx.median_yield = round(statistics.median(yields_list), 3)
        ctx.yield_range = (round(min(yields_list), 3), round(max(yields_list), 3))
    if prices_list:
        ctx.median_price = round(statistics.median(prices_list), 2)

    return ctx


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def generate_benchmark(
    engine: Engine,
    inputs: ProspectInputs,
    emma_data: list[dict[str, Any]] | None = None,
) -> IssuanceBenchmark:
    """Generate a complete issuance benchmark for a prospect.

    Parameters:
        engine: SQLAlchemy engine for the sector corpus database
        inputs: Prospect's issuance parameters
        emma_data: Pre-loaded EMMA data (loaded if None)

    Returns:
        IssuanceBenchmark with all sections populated
    """
    settings = get_settings()
    logger.info(
        "Generating benchmark for %s sector: $%.0fM %s %s %s yr",
        settings.sector, inputs.deal_size / 1e6, inputs.state,
        inputs.expected_rating, inputs.maturity_years,
    )

    # Load data
    os_records = load_os_records(engine)
    financial_reports = load_financial_reports(engine)
    rating_actions = load_rating_actions(engine)
    risk_factors = load_risk_factors(engine)
    security_packages = load_security_packages(engine)
    rating_action_factors = load_rating_action_factors(engine)
    if emma_data is None:
        emma_data = load_emma_bond_data()

    # Build EMMA rating lookup by CUSIP
    emma_ratings: dict[str, str] = {}
    for bond in emma_data:
        cusip = bond.get("snapshot", {}).get("cusip", "")
        for r in bond.get("ratings", []):
            rating = r.get("rating", "")
            if rating and cusip:
                norm = _normalize_rating(rating)
                if norm:
                    emma_ratings[cusip] = norm

    # Also load OS-embedded ratings for spread estimation
    os_ratings = load_os_ratings(engine)

    # Build all sections
    spread = _estimate_spread(inputs, emma_data, rating_actions, os_ratings=os_ratings)
    peers = _find_peer_deals(os_records, inputs, emma_ratings)
    structure = _build_structural_norms(security_packages, os_records)
    risk = _build_risk_profile(risk_factors, rating_action_factors, inputs)
    financials = _build_financial_benchmarks(financial_reports)
    pfa = _build_pfa_comparison(os_records, inputs)
    market = _build_market_context(emma_data, inputs)

    return IssuanceBenchmark(
        inputs=inputs,
        spread_estimate=spread,
        peer_comparison=peers,
        structural_norms=structure,
        risk_profile=risk,
        financial_benchmarks=financials,
        pfa_comparison=pfa,
        market_context=market,
        generated_at=datetime.now().isoformat(),
        sector=settings.sector,
    )


# ---------------------------------------------------------------------------
# Export functions
# ---------------------------------------------------------------------------

def export_json(
    benchmark: IssuanceBenchmark,
    output_path: Path | None = None,
) -> Path:
    """Export benchmark to JSON file."""
    if output_path is None:
        output_path = get_settings().analysis_dir / "issuance_benchmark.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(benchmark.to_dict(), f, indent=2, default=str)

    logger.info("Exported benchmark JSON to %s", output_path)
    return output_path


def export_markdown(
    benchmark: IssuanceBenchmark,
    output_path: Path | None = None,
) -> Path:
    """Export benchmark to Markdown report."""
    if output_path is None:
        output_path = get_settings().analysis_dir / "issuance_benchmark.md"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    b = benchmark
    inp = b.inputs
    lines = [
        f"# Issuance Benchmark Report — {b.sector.title()} Sector",
        f"",
        f"**Generated**: {b.generated_at}",
        f"",
        f"## Prospect Inputs",
        f"",
        f"| Parameter | Value |",
        f"|-----------|-------|",
        f"| Deal Size | ${inp.deal_size / 1e6:.1f}M |",
        f"| State | {inp.state.upper()} |",
        f"| Expected Rating | {inp.expected_rating} |",
        f"| Maturity | {inp.maturity_years:.0f} years |",
        f"",
    ]

    # Spread estimate
    se = b.spread_estimate
    lines.extend([
        f"## Spread Estimate",
        f"",
        f"- **Expected spread**: {se.expected_spread_bps} bps over AAA MMD"
        if se.expected_spread_bps is not None
        else "- **Expected spread**: N/A",
        f"- **Rating (normalized)**: {se.rating_normalized}",
    ])
    if se.sector_median_spread_bps is not None:
        lines.append(
            f"- **Sector median spread**: {se.sector_median_spread_bps} bps "
            f"({se.spread_vs_sector} than sector)"
        )
    lines.append(f"- **Rated peers in corpus**: {se.n_rated_peers}")
    lines.append("")

    # Peer comparison
    pc = b.peer_comparison
    lines.extend([
        f"## Peer Comparison ({pc.n_peers_found} peers)",
        f"",
    ])
    if pc.size_percentile is not None:
        lines.append(
            f"Your deal is at the **{pc.size_percentile:.0f}th percentile** by size "
            f"in the {b.sector} sector."
        )
    if pc.peer_par_median:
        lines.append(
            f"- Peer median par: ${pc.peer_par_median / 1e6:.1f}M"
        )
    if pc.peer_deals:
        lines.extend(["", "| Issuer | State | Par ($M) | Type | Similarity |",
                       "|--------|-------|----------|------|------------|"])
        for p in pc.peer_deals[:10]:
            par_str = f"${p.par_amount / 1e6:.1f}" if p.par_amount > 0 else "N/A"
            lines.append(
                f"| {p.issuer_name[:30]} | {p.state} | {par_str} | "
                f"{p.bond_type[:15]} | {p.similarity_score:.0%} |"
            )
    lines.append("")

    # Structural norms
    sn = b.structural_norms
    lines.extend([
        f"## Structural Norms ({sn.n_packages} security packages)",
        f"",
    ])
    if sn.pledge_type_distribution:
        lines.append(f"**Pledge types**: {', '.join(f'{k} ({v})' for k, v in sn.pledge_type_distribution.items())}")
    if sn.typical_coverage_ratio is not None:
        lines.append(f"- Typical min coverage ratio: **{sn.typical_coverage_ratio:.2f}x**")
    if sn.abt_coverage_median is not None:
        lines.append(f"- ABT historical coverage median: **{sn.abt_coverage_median:.2f}x**")
    lines.append(f"- DSRF prevalence: **{sn.dsrf_prevalence * 100:.0f}%** of deals")
    if sn.enhancement_types:
        lines.append(f"- Credit enhancements: {', '.join(f'{k} ({v})' for k, v in sn.enhancement_types.items())}")
    lines.append("")

    # Financial benchmarks
    fb = b.financial_benchmarks
    lines.extend([
        f"## Financial Benchmarks ({fb.n_reports} reports)",
        f"",
    ])
    if fb.dscr_median is not None:
        lines.append(
            f"- **DSCR**: {fb.dscr_median:.2f}x median "
            f"({fb.dscr_iqr[0]:.2f}x - {fb.dscr_iqr[1]:.2f}x IQR)"
        )
    if fb.operating_margin_median is not None:
        lines.append(f"- **Operating margin**: {fb.operating_margin_median * 100:.1f}%")
    if fb.leverage_median is not None:
        lines.append(f"- **Leverage**: {fb.leverage_median:.2f}x (liabilities/assets)")
    if fb.days_cash_median is not None:
        lines.append(f"- **Days cash on hand**: {fb.days_cash_median:.0f}")
    lines.append("")

    # Risk profile
    rp = b.risk_profile
    lines.extend([
        f"## Risk Landscape ({rp.n_risk_factors} factors)",
        f"",
        f"Overall mitigation rate: **{rp.overall_mitigation_rate * 100:.0f}%**",
        f"",
    ])
    if rp.top_risk_categories:
        lines.extend(["| Category | Count | % | Mitigated |",
                       "|----------|-------|---|-----------|"])
        for tc in rp.top_risk_categories:
            lines.append(
                f"| {tc['category']} | {tc['count']} | "
                f"{tc['pct_of_total']:.0f}% | {tc['mitigation_rate_pct']:.0f}% |"
            )
    if rp.prospect_risk_flags:
        lines.extend(["", "**Prospect-specific flags:**"])
        for flag in rp.prospect_risk_flags:
            lines.append(f"- {flag}")
    lines.append("")

    # PFA comparison
    pfa = b.pfa_comparison
    lines.extend([
        f"## Conduit / PFA Comparison",
        f"",
        f"Conduit deals in corpus: **{pfa.conduit_deals_in_corpus}**",
        f"",
    ])
    if pfa.conduit_median_par:
        lines.append(f"- Conduit median par: ${pfa.conduit_median_par / 1e6:.1f}M")
    if pfa.conduit_rating_profile:
        lines.append(f"- Conduit rating profile: {pfa.conduit_rating_profile}")
    if pfa.prospect_advantages:
        lines.extend(["", "**Advantages of direct issuance:**"])
        for a in pfa.prospect_advantages:
            lines.append(f"- {a}")
    if pfa.prospect_considerations:
        lines.extend(["", "**Considerations:**"])
        for c in pfa.prospect_considerations:
            lines.append(f"- {c}")
    lines.append("")

    # Market context
    mc = b.market_context
    if mc.n_trades > 0:
        lines.extend([
            f"## Secondary Market Context",
            f"",
            f"- Trades at similar rating tier: **{mc.n_trades}** across {mc.n_bonds_trading} bonds",
        ])
        if mc.median_yield is not None:
            lines.append(f"- Median yield: **{mc.median_yield:.2f}%**")
        if mc.yield_range != (0.0, 0.0):
            lines.append(f"- Yield range: {mc.yield_range[0]:.2f}% - {mc.yield_range[1]:.2f}%")
        if mc.median_price is not None:
            lines.append(f"- Median price: **${mc.median_price:.2f}**")
        lines.append("")

    # Footer
    lines.extend([
        "---",
        f"*Generated by Muni-Pal Issuance Benchmarking Calculator v1*",
        f"*Data source: EMMA corpus ({b.sector} sector)*",
    ])

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    logger.info("Exported benchmark Markdown to %s", output_path)
    return output_path
