"""Fundamental Scoring Engine — Phase 1 of Summers' Standard Model implementation.

Implements the fundamental screening framework from Section 4.2 of "The Standard
Model of Complex Economic Systems" adapted for municipal bond analysis:

  F_i = w_1 * FinancialStability + w_2 * Profitability + w_3 * CreditQuality
      + w_4 * StructuralQuality  + w_5 * GrowthMomentum

Where:
  - F_i >= F_threshold defines the investable universe
  - Each dimension scores 0-100 based on component metrics
  - Data blends bond-side extractions with equity-side fundamentals

This establishes the investable universe for Phase 2 (S_Omega return series
construction) and Phase 3 (benchmark/index development).
"""
from __future__ import annotations

import json
import logging
import math
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy.engine import Engine

from ..config import get_settings
from .data_loader import (
    get_latest_financials,
    get_revenue_history,
    load_emma_bond_data,
    load_financial_reports,
    load_os_ratings,
    load_os_records,
    load_rating_actions,
    load_ticker_history,
)
from .models import DimensionScore, FundamentalScore, ScoredUniverse
from .obligor_mapping import (
    ObligorProfile,
    build_cusip_mapping,
    get_all_obligors,
    match_issuer_to_obligor,
)

logger = logging.getLogger("bond_os_extractor.analysis.scoring_engine")

# ---------------------------------------------------------------------------
# Rating scale — numeric conversion for credit quality scoring
# ---------------------------------------------------------------------------

RATING_SCALE: dict[str, int] = {
    # S&P / Fitch scale
    "AAA": 21, "AA+": 20, "AA": 19, "AA-": 18,
    "A+": 17, "A": 16, "A-": 15,
    "BBB+": 14, "BBB": 13, "BBB-": 12,
    "BB+": 11, "BB": 10, "BB-": 9,
    "B+": 8, "B": 7, "B-": 6,
    "CCC+": 5, "CCC": 4, "CCC-": 3,
    "CC": 2, "C": 1, "D": 0,
    # Moody's scale (mapped to equivalent)
    "Aaa": 21, "Aa1": 20, "Aa2": 19, "Aa3": 18,
    "A1": 17, "A2": 16, "A3": 15,
    "Baa1": 14, "Baa2": 13, "Baa3": 12,
    "Ba1": 11, "Ba2": 10, "Ba3": 9,
    "B1": 8, "B2": 7, "B3": 6,
    "Caa1": 5, "Caa2": 4, "Caa3": 3,
    "Ca": 2, "C": 1,
}

INVESTMENT_GRADE_FLOOR = 12  # BBB- / Baa3

# Dimension weights (Summers Section 4.2 — adapted for fixed income)
DEFAULT_WEIGHTS = {
    "financial_stability": 0.30,
    "profitability": 0.20,
    "credit_quality": 0.25,
    "structural_quality": 0.15,
    "growth_momentum": 0.10,
}


def _clamp(val: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, val))


def _safe_div(num: float | None, den: float | None) -> float | None:
    if num is None or den is None or den == 0:
        return None
    return num / den


def _rating_to_numeric(rating: str | None) -> int | None:
    if not rating:
        return None
    # Strip whitespace and try exact match
    clean = rating.strip()
    return RATING_SCALE.get(clean)


# ---------------------------------------------------------------------------
# Dimension scorers
# ---------------------------------------------------------------------------

def _score_financial_stability(
    bond_financials: list[dict],
    equity_metrics: dict[str, float | None],
    os_records: list[dict],
) -> DimensionScore:
    """Score Dimension 1: Financial Stability.

    Components (Summers Table 2 — fixed income adaptation):
      - DSCR (Debt Service Coverage Ratio) — threshold >= 1.2x
      - Leverage ratio (Total Debt / Total Assets)
      - Cash coverage (Cash / Annual Debt Service)
      - Current ratio (Current Assets / Current Liabilities)

    Data blending: bond financial reports provide DSCR and debt service metrics;
    equity financials provide leverage and liquidity ratios.
    """
    components: dict[str, float | None] = {}

    # --- DSCR from bond financial reports ---
    dscrs = [
        r["debt_service_coverage_ratio"]
        for r in bond_financials
        if r.get("debt_service_coverage_ratio") is not None
    ]
    dscr = max(dscrs) if dscrs else None
    components["dscr"] = dscr

    # --- Cash coverage from bond data ---
    cash_coverages = []
    for r in bond_financials:
        cash = r.get("cash_and_equivalents")
        ds = r.get("annual_debt_service")
        if cash and ds and ds > 0:
            cash_coverages.append(cash / ds)
    cash_coverage = max(cash_coverages) if cash_coverages else None
    components["cash_coverage"] = cash_coverage

    # --- Leverage from equity data (fallback to bond data) ---
    leverage = _safe_div(
        equity_metrics.get("total_debt"),
        equity_metrics.get("total_assets"),
    )
    if leverage is None:
        # Try from bond financial reports
        for r in bond_financials:
            leverage = _safe_div(
                r.get("total_debt_outstanding") or r.get("total_liabilities"),
                r.get("total_assets"),
            )
            if leverage is not None:
                break
    components["leverage_ratio"] = leverage

    # --- Current ratio from equity data ---
    current_ratio = _safe_div(
        equity_metrics.get("current_assets"),
        equity_metrics.get("current_liabilities"),
    )
    components["current_ratio"] = current_ratio

    # --- Also check OS-level coverage covenants ---
    covenant_ratios = [
        r["min_coverage_ratio"]
        for r in os_records
        if r.get("min_coverage_ratio") is not None
    ]
    if covenant_ratios:
        components["covenant_min_coverage"] = max(covenant_ratios)

    # --- Compute dimension score (0-100) ---
    sub_scores: list[float] = []

    # DSCR score: 1.0x → 0, 1.2x → 50, 2.0x+ → 100
    if dscr is not None:
        if dscr >= 2.0:
            sub_scores.append(100.0)
        elif dscr >= 1.2:
            sub_scores.append(50.0 + (dscr - 1.2) / 0.8 * 50.0)
        elif dscr >= 1.0:
            sub_scores.append((dscr - 1.0) / 0.2 * 50.0)
        else:
            sub_scores.append(0.0)

    # Leverage score: 0.0 → 100, 0.5 → 60, 0.8+ → 0
    if leverage is not None:
        if leverage <= 0.3:
            sub_scores.append(100.0)
        elif leverage <= 0.5:
            sub_scores.append(60.0 + (0.5 - leverage) / 0.2 * 40.0)
        elif leverage <= 0.8:
            sub_scores.append((0.8 - leverage) / 0.3 * 60.0)
        else:
            sub_scores.append(0.0)

    # Cash coverage score: 0x → 0, 1x → 50, 3x+ → 100
    if cash_coverage is not None:
        if cash_coverage >= 3.0:
            sub_scores.append(100.0)
        elif cash_coverage >= 1.0:
            sub_scores.append(50.0 + (cash_coverage - 1.0) / 2.0 * 50.0)
        else:
            sub_scores.append(cash_coverage / 1.0 * 50.0)

    # Current ratio score: <1 → 0, 1 → 30, 1.5 → 60, 2+ → 100
    if current_ratio is not None:
        if current_ratio >= 2.0:
            sub_scores.append(100.0)
        elif current_ratio >= 1.5:
            sub_scores.append(60.0 + (current_ratio - 1.5) / 0.5 * 40.0)
        elif current_ratio >= 1.0:
            sub_scores.append(30.0 + (current_ratio - 1.0) / 0.5 * 30.0)
        else:
            sub_scores.append(current_ratio * 30.0)

    raw = sum(sub_scores) / len(sub_scores) if sub_scores else 0.0
    is_defaulted = len(sub_scores) == 0
    data_source = "blended" if equity_metrics and bond_financials else (
        "equity" if equity_metrics else "bond"
    )

    return DimensionScore(
        name="financial_stability",
        weight=DEFAULT_WEIGHTS["financial_stability"],
        raw_score=_clamp(raw),
        components=components,
        data_source=data_source,
        defaulted=is_defaulted,
    )


def _score_profitability(
    bond_financials: list[dict],
    equity_metrics: dict[str, float | None],
) -> DimensionScore:
    """Score Dimension 2: Profitability / Efficiency.

    Components:
      - Operating margin (Operating Income / Revenue)
      - Net margin (Net Income / Revenue)
      - ROA (Net Income / Total Assets)
      - EBITDA margin (EBITDA / Revenue) — equity only

    For municipal issuers without equity data, falls back to bond financial
    report metrics (revenue, net income, assets).
    """
    components: dict[str, float | None] = {}

    # Prefer equity metrics (more standardized)
    rev = equity_metrics.get("total_revenue")
    op_inc = equity_metrics.get("operating_income")
    net_inc = equity_metrics.get("net_income")
    assets = equity_metrics.get("total_assets")
    ebitda = equity_metrics.get("ebitda")

    # Fallback to bond financial reports
    if rev is None:
        for r in bond_financials:
            if r.get("total_revenue"):
                rev = r["total_revenue"]
                op_inc = op_inc or r.get("operating_income")
                net_inc = net_inc or r.get("net_income")
                assets = assets or r.get("total_assets")
                break

    components["operating_margin"] = _safe_div(op_inc, rev)
    components["net_margin"] = _safe_div(net_inc, rev)
    components["roa"] = _safe_div(net_inc, assets)
    components["ebitda_margin"] = _safe_div(ebitda, rev)

    sub_scores: list[float] = []

    # Operating margin: <0 → 0, 0% → 20, 15% → 60, 30%+ → 100
    om = components["operating_margin"]
    if om is not None:
        if om >= 0.30:
            sub_scores.append(100.0)
        elif om >= 0.15:
            sub_scores.append(60.0 + (om - 0.15) / 0.15 * 40.0)
        elif om >= 0.0:
            sub_scores.append(20.0 + om / 0.15 * 40.0)
        else:
            sub_scores.append(max(0, 20.0 + om * 100))

    # Net margin: <0 → 0, 0% → 20, 10% → 60, 20%+ → 100
    nm = components["net_margin"]
    if nm is not None:
        if nm >= 0.20:
            sub_scores.append(100.0)
        elif nm >= 0.10:
            sub_scores.append(60.0 + (nm - 0.10) / 0.10 * 40.0)
        elif nm >= 0.0:
            sub_scores.append(20.0 + nm / 0.10 * 40.0)
        else:
            sub_scores.append(max(0, 20.0 + nm * 100))

    # ROA: <0 → 0, 0% → 20, 5% → 60, 10%+ → 100
    roa = components["roa"]
    if roa is not None:
        if roa >= 0.10:
            sub_scores.append(100.0)
        elif roa >= 0.05:
            sub_scores.append(60.0 + (roa - 0.05) / 0.05 * 40.0)
        elif roa >= 0.0:
            sub_scores.append(20.0 + roa / 0.05 * 40.0)
        else:
            sub_scores.append(max(0, 20.0 + roa * 100))

    # EBITDA margin (equity-only bonus): 20%+ → 100, 10% → 50
    em = components["ebitda_margin"]
    if em is not None:
        if em >= 0.30:
            sub_scores.append(100.0)
        elif em >= 0.20:
            sub_scores.append(70.0 + (em - 0.20) / 0.10 * 30.0)
        elif em > 0:
            sub_scores.append(em / 0.20 * 70.0)
        else:
            sub_scores.append(0.0)

    raw = sum(sub_scores) / len(sub_scores) if sub_scores else 0.0
    is_defaulted = len(sub_scores) == 0
    data_source = "equity" if equity_metrics.get("total_revenue") else "bond"

    return DimensionScore(
        name="profitability",
        weight=DEFAULT_WEIGHTS["profitability"],
        raw_score=_clamp(raw),
        components=components,
        data_source=data_source,
        defaulted=is_defaulted,
    )


def _score_credit_quality(
    rating_actions: list[dict],
    os_ratings: list[dict],
    emma_ratings: list[dict],
) -> DimensionScore:
    """Score Dimension 3: Credit Quality.

    Components:
      - Current rating level (numeric scale, 0-21)
      - Rating trajectory (net upgrades - downgrades)
      - Outlook (positive/stable/negative)
      - Investment grade status (binary)

    Data sources: rating actions (trajectory), OS ratings (embedded),
    EMMA crawler (most current).
    """
    components: dict[str, float | None] = {}

    # Collect all known ratings
    all_ratings: list[int] = []

    # From OS extractions
    for r in os_ratings:
        num = _rating_to_numeric(r.get("rating"))
        if num is not None:
            all_ratings.append(num)

    # From EMMA crawler
    for r in emma_ratings:
        num = _rating_to_numeric(r.get("rating"))
        if num is not None:
            all_ratings.append(num)

    # From rating actions (use new_rating as most current)
    for r in rating_actions:
        num = _rating_to_numeric(r.get("new_rating"))
        if num is not None:
            all_ratings.append(num)

    # Best rating available
    best_rating = max(all_ratings) if all_ratings else None
    components["best_rating_numeric"] = best_rating
    components["is_investment_grade"] = (
        1.0 if best_rating and best_rating >= INVESTMENT_GRADE_FLOOR else 0.0
    )

    # Rating trajectory from actions
    upgrades = sum(
        1 for r in rating_actions if r.get("action_type") in ("upgrade", "new_rating")
    )
    downgrades = sum(
        1 for r in rating_actions if r.get("action_type") == "downgrade"
    )
    trajectory = upgrades - downgrades
    components["upgrades"] = float(upgrades)
    components["downgrades"] = float(downgrades)
    components["trajectory"] = float(trajectory)

    # Outlook
    outlooks = []
    for r in rating_actions:
        ol = (r.get("new_outlook") or "").lower()
        if ol in ("positive", "stable", "negative", "developing"):
            outlooks.append(ol)
    for r in os_ratings:
        ol = (r.get("outlook") or "").lower()
        if ol in ("positive", "stable", "negative", "developing"):
            outlooks.append(ol)

    outlook_score = 50.0  # default neutral
    if outlooks:
        # Use most recent / best outlook
        if "positive" in outlooks:
            outlook_score = 80.0
        elif "stable" in outlooks:
            outlook_score = 60.0
        elif "developing" in outlooks:
            outlook_score = 40.0
        elif "negative" in outlooks:
            outlook_score = 20.0
    components["outlook_score"] = outlook_score

    # Compute dimension score
    sub_scores: list[float] = []

    # Rating level: D(0)→0, BBB-(12)→50, AAA(21)→100
    if best_rating is not None:
        rating_score = (best_rating / 21.0) * 100.0
        sub_scores.append(rating_score)

    # Trajectory bonus: each net upgrade adds 10 points (capped at +30)
    trajectory_bonus = _clamp(50.0 + trajectory * 10.0)
    sub_scores.append(trajectory_bonus)

    # Outlook
    sub_scores.append(outlook_score)

    # Investment grade bonus
    if best_rating and best_rating >= INVESTMENT_GRADE_FLOOR:
        sub_scores.append(80.0)
    elif best_rating is not None:
        sub_scores.append(20.0)

    raw = sum(sub_scores) / len(sub_scores) if sub_scores else 0.0
    # Defaulted if no real rating data contributed (only outlook_score default)
    has_real_ratings = best_rating is not None or upgrades > 0 or downgrades > 0
    is_defaulted = not has_real_ratings

    return DimensionScore(
        name="credit_quality",
        weight=DEFAULT_WEIGHTS["credit_quality"],
        raw_score=_clamp(raw),
        components=components,
        data_source="blended",
        defaulted=is_defaulted,
    )


def _score_structural_quality(os_records: list[dict]) -> DimensionScore:
    """Score Dimension 4: Structural Quality (bond-specific).

    Components:
      - Credit enhancement type (LOC/insurance → higher)
      - Rate covenant strength (min coverage ratio)
      - Additional bonds test strength
      - DSRF presence and adequacy
      - Pledge type (revenue vs GO)
      - Lien position (senior vs subordinate)

    This dimension has no equity equivalent — it captures the structural
    protections embedded in bond indentures.
    """
    components: dict[str, float | None] = {}

    # Collect structural features across all OS records for this obligor
    has_enhancement = any(
        r.get("credit_enhancement_type") not in (None, "", "none")
        for r in os_records
    )
    components["has_credit_enhancement"] = 1.0 if has_enhancement else 0.0

    # Rate covenant
    covenants = [
        r["min_coverage_ratio"]
        for r in os_records
        if r.get("min_coverage_ratio") is not None
    ]
    best_covenant = max(covenants) if covenants else None
    components["min_coverage_covenant"] = best_covenant

    # Additional bonds test
    abt_values = [
        r["additional_bonds_hist_coverage"]
        for r in os_records
        if r.get("additional_bonds_hist_coverage") is not None
    ]
    best_abt = max(abt_values) if abt_values else None
    components["additional_bonds_test"] = best_abt

    # DSRF
    has_dsrf = any(
        r.get("dsrf_type") not in (None, "", "none")
        for r in os_records
    )
    components["has_dsrf"] = 1.0 if has_dsrf else 0.0

    # Pledge type
    pledge_types = [r.get("pledge_type") for r in os_records if r.get("pledge_type")]
    has_revenue_pledge = any("revenue" in p.lower() for p in pledge_types) if pledge_types else False
    components["has_revenue_pledge"] = 1.0 if has_revenue_pledge else 0.0

    # Lien position
    lien_positions = [r.get("lien_position") for r in os_records if r.get("lien_position")]
    is_senior = any("senior" in l.lower() or "first" in l.lower() for l in lien_positions) if lien_positions else False
    components["is_senior_lien"] = 1.0 if is_senior else 0.0

    # Compute dimension score
    sub_scores: list[float] = []

    # Enhancement: +30 if present
    sub_scores.append(80.0 if has_enhancement else 40.0)

    # Covenant strength: 1.0x → 30, 1.25x → 60, 1.5x+ → 100
    if best_covenant is not None:
        if best_covenant >= 1.5:
            sub_scores.append(100.0)
        elif best_covenant >= 1.25:
            sub_scores.append(60.0 + (best_covenant - 1.25) / 0.25 * 40.0)
        elif best_covenant >= 1.0:
            sub_scores.append(30.0 + (best_covenant - 1.0) / 0.25 * 30.0)
        else:
            sub_scores.append(best_covenant * 30.0)

    # ABT: higher = harder to dilute = better
    if best_abt is not None:
        if best_abt >= 1.5:
            sub_scores.append(100.0)
        elif best_abt >= 1.0:
            sub_scores.append(50.0 + (best_abt - 1.0) / 0.5 * 50.0)
        else:
            sub_scores.append(best_abt * 50.0)

    # DSRF presence
    sub_scores.append(70.0 if has_dsrf else 30.0)

    # Lien position
    sub_scores.append(80.0 if is_senior else 40.0)

    raw = sum(sub_scores) / len(sub_scores) if sub_scores else 0.0
    is_defaulted = len(os_records) == 0

    return DimensionScore(
        name="structural_quality",
        weight=DEFAULT_WEIGHTS["structural_quality"],
        raw_score=_clamp(raw),
        components=components,
        data_source="bond",
        defaulted=is_defaulted,
    )


def _score_growth_momentum(
    ticker: str | None,
    equity_metrics: dict[str, float | None],
    rating_actions: list[dict],
    ticker_base_dir: Path | None = None,
) -> DimensionScore:
    """Score Dimension 5: Growth / Momentum.

    Components:
      - Revenue CAGR (multi-year, from ticker financials)
      - Stock price momentum (12-month return, from ticker history)
      - Rating upgrade trajectory (from rating actions)

    This dimension is equity-heavy — pure municipal issuers without
    equity tickers get scored primarily on rating trajectory.
    """
    components: dict[str, float | None] = {}
    sub_scores: list[float] = []

    # Revenue CAGR (equity data)
    if ticker:
        rev_series = get_revenue_history(ticker, ticker_base_dir)
        if len(rev_series) >= 3:
            earliest = rev_series[0][1]
            latest = rev_series[-1][1]
            n_years = len(rev_series) - 1
            if earliest and latest and earliest > 0 and n_years > 0:
                cagr = (latest / earliest) ** (1.0 / n_years) - 1.0
                components["revenue_cagr"] = cagr
                # CAGR score: <0% → 0, 0% → 30, 5% → 60, 10%+ → 100
                if cagr >= 0.10:
                    sub_scores.append(100.0)
                elif cagr >= 0.05:
                    sub_scores.append(60.0 + (cagr - 0.05) / 0.05 * 40.0)
                elif cagr >= 0.0:
                    sub_scores.append(30.0 + cagr / 0.05 * 30.0)
                else:
                    sub_scores.append(max(0, 30.0 + cagr * 200))

    # Stock price momentum (12-month return)
    if ticker:
        history = load_ticker_history(ticker, ticker_base_dir)
        if len(history) >= 252:
            # Last 252 trading days ≈ 1 year
            recent_close = history[-1].get("adj_close") or history[-1].get("close")
            year_ago_close = history[-252].get("adj_close") or history[-252].get("close")
            if recent_close and year_ago_close and year_ago_close > 0:
                momentum = (recent_close / year_ago_close) - 1.0
                components["price_momentum_12m"] = momentum
                # Momentum score: <-20% → 0, 0% → 40, 15% → 70, 30%+ → 100
                if momentum >= 0.30:
                    sub_scores.append(100.0)
                elif momentum >= 0.15:
                    sub_scores.append(70.0 + (momentum - 0.15) / 0.15 * 30.0)
                elif momentum >= 0.0:
                    sub_scores.append(40.0 + momentum / 0.15 * 30.0)
                elif momentum >= -0.20:
                    sub_scores.append(40.0 + momentum / 0.20 * 40.0)
                else:
                    sub_scores.append(0.0)

    # Rating trajectory (bond data — available for all obligors)
    upgrades = sum(1 for r in rating_actions if r.get("action_type") == "upgrade")
    downgrades = sum(1 for r in rating_actions if r.get("action_type") == "downgrade")
    net = upgrades - downgrades
    components["rating_trajectory"] = float(net)
    trajectory_score = _clamp(50.0 + net * 15.0)
    sub_scores.append(trajectory_score)

    raw = sum(sub_scores) / len(sub_scores) if sub_scores else 0.0
    # Defaulted if only the trajectory default contributed (no equity, no upgrades/downgrades)
    has_real_data = (
        components.get("revenue_cagr") is not None
        or components.get("price_momentum_12m") is not None
        or upgrades > 0 or downgrades > 0
    )
    is_defaulted = not has_real_data

    return DimensionScore(
        name="growth_momentum",
        weight=DEFAULT_WEIGHTS["growth_momentum"],
        raw_score=_clamp(raw),
        components=components,
        data_source="equity" if ticker else "bond",
        defaulted=is_defaulted,
    )


# ---------------------------------------------------------------------------
# Main scoring orchestrator
# ---------------------------------------------------------------------------

def score_obligor(
    obligor: ObligorProfile,
    os_records: list[dict],
    bond_financials: list[dict],
    rating_actions: list[dict],
    os_ratings: list[dict],
    emma_ratings: list[dict],
    equity_metrics: dict[str, float | None],
    threshold: float = 50.0,
    ticker_base_dir: Path | None = None,
) -> FundamentalScore:
    """Score a single obligor across all five dimensions."""
    score = FundamentalScore(
        obligor_id=obligor.ticker or obligor.canonical_name.lower().replace(" ", "_"),
        obligor_name=obligor.canonical_name,
        ticker=obligor.ticker,
        cusips=list(obligor.cusips),
        threshold=threshold,
    )

    # Track data sources
    score.data_sources = {
        "os_records": len(os_records),
        "financial_reports": len(bond_financials),
        "rating_actions": len(rating_actions),
        "os_ratings": len(os_ratings),
        "emma_ratings": len(emma_ratings),
        "has_equity_data": bool(equity_metrics),
    }

    # Score each dimension
    score.financial_stability = _score_financial_stability(
        bond_financials, equity_metrics, os_records,
    )
    score.profitability = _score_profitability(bond_financials, equity_metrics)
    score.credit_quality = _score_credit_quality(
        rating_actions, os_ratings, emma_ratings,
    )
    score.structural_quality = _score_structural_quality(os_records)
    score.growth_momentum = _score_growth_momentum(
        obligor.ticker, equity_metrics, rating_actions, ticker_base_dir,
    )

    score.compute_composite()
    return score


def score_universe(
    engine: Engine,
    threshold: float = 50.0,
    ticker_base_dir: Path | None = None,
) -> ScoredUniverse:
    """Score the full obligor universe.

    Loads all available data, maps obligors to tickers, and scores each one.
    Returns a ScoredUniverse containing all scores and the investable subset.
    """
    logger.info("Loading bond corpus data...")
    all_os = load_os_records(engine)
    all_fin = load_financial_reports(engine)
    all_ra = load_rating_actions(engine)
    all_os_ratings = load_os_ratings(engine)

    # Build obligor mapping
    cusip_map = build_cusip_mapping(all_os, all_fin, all_ra)

    # Load EMMA data for ratings
    emma_data = load_emma_bond_data()

    # Score each known obligor
    obligors = get_all_obligors()
    universe = ScoredUniverse(threshold=threshold)

    for obligor in obligors:
        logger.info("Scoring obligor: %s (%s)", obligor.canonical_name, obligor.ticker)

        # Filter bond data for this obligor
        ob_os = [
            r for r in all_os
            if match_issuer_to_obligor(r.get("issuer_name", "")) == obligor
            or match_issuer_to_obligor(r.get("borrower_name", "")) == obligor
        ]
        ob_fin = [
            r for r in all_fin
            if match_issuer_to_obligor(r.get("issuer_name", "")) == obligor
            or match_issuer_to_obligor(r.get("obligor_name", "")) == obligor
        ]
        ob_ra = [
            r for r in all_ra
            if match_issuer_to_obligor(r.get("issuer_name", "")) == obligor
            or match_issuer_to_obligor(r.get("obligor_name", "")) == obligor
        ]
        ob_os_ratings = [
            r for r in all_os_ratings
            if match_issuer_to_obligor(r.get("issuer_name", "")) == obligor
            or match_issuer_to_obligor(r.get("borrower_name", "")) == obligor
        ]

        # Get EMMA ratings for this obligor's CUSIPs
        ob_emma_ratings: list[dict] = []
        for emma_rec in emma_data:
            sec_name = (emma_rec.get("snapshot", {}).get("security_name", "") or "")
            if match_issuer_to_obligor(sec_name) == obligor:
                for rat in emma_rec.get("ratings", []):
                    if rat.get("rating"):
                        ob_emma_ratings.append(rat)

        # Load equity metrics
        equity_metrics: dict[str, float | None] = {}
        if obligor.ticker:
            equity_metrics = get_latest_financials(obligor.ticker, ticker_base_dir)

        # Check if we have any data at all
        total_data = (
            len(ob_os) + len(ob_fin) + len(ob_ra) +
            len(ob_os_ratings) + len(ob_emma_ratings) + len(equity_metrics)
        )
        if total_data == 0:
            logger.info("  No data found for %s — skipping", obligor.canonical_name)
            continue

        result = score_obligor(
            obligor=obligor,
            os_records=ob_os,
            bond_financials=ob_fin,
            rating_actions=ob_ra,
            os_ratings=ob_os_ratings,
            emma_ratings=ob_emma_ratings,
            equity_metrics=equity_metrics,
            threshold=threshold,
            ticker_base_dir=ticker_base_dir,
        )
        universe.scores.append(result)
        logger.info(
            "  F_i = %.1f (%s) | Sources: %s",
            result.f_score,
            "INVESTABLE" if result.investable else "excluded",
            result.data_sources,
        )

    # Also score unmatched issuers that have bond data but no known ticker
    matched_issuers = set()
    for obligor in obligors:
        for alias in obligor.aliases:
            matched_issuers.add(alias)

    unmatched_issuers: dict[str, list[dict]] = {}
    for r in all_os:
        issuer = r.get("issuer_name") or ""
        if not issuer:
            continue
        if match_issuer_to_obligor(issuer) is None:
            slug = issuer.lower().strip()[:80]
            if slug not in unmatched_issuers:
                unmatched_issuers[slug] = []
            unmatched_issuers[slug].append(r)

    for slug, records in unmatched_issuers.items():
        issuer_name = records[0].get("issuer_name", slug)
        ob = ObligorProfile(canonical_name=issuer_name, sector="municipal")

        # Filter other data types for this issuer
        ob_fin = [
            r for r in all_fin
            if (r.get("issuer_name") or "").lower().strip()[:80] == slug
        ]
        ob_ra = [
            r for r in all_ra
            if (r.get("issuer_name") or "").lower().strip()[:80] == slug
        ]
        ob_os_ratings = [
            r for r in all_os_ratings
            if (r.get("issuer_name") or "").lower().strip()[:80] == slug
        ]

        total = len(records) + len(ob_fin) + len(ob_ra) + len(ob_os_ratings)
        if total < 2:
            continue  # Not enough data for a meaningful score

        result = score_obligor(
            obligor=ob,
            os_records=records,
            bond_financials=ob_fin,
            rating_actions=ob_ra,
            os_ratings=ob_os_ratings,
            emma_ratings=[],
            equity_metrics={},
            threshold=threshold,
        )
        universe.scores.append(result)

    # Sort by score descending
    universe.scores.sort(key=lambda s: s.f_score, reverse=True)

    logger.info(
        "Scored %d obligors. %d investable (F_i >= %.0f). Avg F_i = %.1f",
        len(universe.scores),
        len(universe.investable),
        threshold,
        universe.avg_score,
    )
    return universe


def export_scores(universe: ScoredUniverse, output_path: Path | None = None) -> Path:
    """Export scored universe to JSON."""
    if output_path is None:
        output_path = get_settings().data_dir / "analysis" / "fundamental_scores.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "summary": universe.summary(),
        "scored_at": universe.scored_at.isoformat(),
        "scores": [
            {
                "obligor_id": s.obligor_id,
                "obligor_name": s.obligor_name,
                "ticker": s.ticker,
                "cusips": s.cusips,
                "f_score": s.f_score,
                "investable": s.investable,
                "data_quality": s.data_quality,
                "defaulted_dimensions": s.defaulted_dimensions,
                "dimensions": {
                    dim_name: {
                        "raw_score": getattr(s, dim_name).raw_score,
                        "weighted_score": getattr(s, dim_name).weighted_score,
                        "weight": getattr(s, dim_name).weight,
                        "defaulted": getattr(s, dim_name).defaulted,
                        "components": getattr(s, dim_name).components,
                        "data_source": getattr(s, dim_name).data_source,
                    }
                    for dim_name in [
                        "financial_stability", "profitability",
                        "credit_quality", "structural_quality",
                        "growth_momentum",
                    ]
                    if getattr(s, dim_name) is not None
                },
                "data_sources": s.data_sources,
            }
            for s in universe.scores
        ],
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)

    logger.info("Exported scores to %s", output_path)
    return output_path
