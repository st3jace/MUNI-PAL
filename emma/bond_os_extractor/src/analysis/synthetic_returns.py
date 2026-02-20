"""Synthetic bond return series builder for municipal obligors.

Constructs return time series for obligors that lack equity tickers by
cascading through four data sources in priority order:

  Priority 1: EMMA secondary market trade returns (highest fidelity)
  Priority 2: Rating event shocks (spread-based price impact)
  Priority 3: Fundamental drift (DSCR/revenue changes => spread moves)
  Priority 4: Coupon carry interpolation (hold-to-maturity baseline)

The resulting ReturnSeries has asset_type="bond" and frequency="irregular",
and is directly consumable by the Phase 2-5 pipeline.

Summers Paper 1, Section 2: "The return period should match asset
liquidity." Bond returns are inherently irregular -- the frequency
reflects actual secondary market trading activity.
"""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from datetime import datetime as dt, timedelta
from typing import Any

from sqlalchemy.engine import Engine

from .data_loader import (
    load_emma_bonds_by_issuer,
    load_financial_reports_for_obligor,
    load_rating_actions_for_obligor,
)
from .return_series import ReturnSeries, build_bond_returns
from .spread_table import (
    estimate_modified_duration,
    rating_transition_spread_change,
    spread_change_to_return,
)

logger = logging.getLogger("bond_os_extractor.analysis.synthetic_returns")

# Minimum observations for inclusion in the Omega pipeline
MIN_OBSERVATIONS = 8

# Date formats encountered in the data
_DATE_FORMATS = ["%m/%d/%Y %I:%M %p", "%m/%d/%Y", "%Y-%m-%d"]


@dataclass
class SyntheticReturnConfig:
    """Configuration for synthetic return construction."""
    min_observations: int = MIN_OBSERVATIONS
    rating_proximity_days: int = 5
    max_gap_days: int = 180
    coupon_carry_only: bool = False


def _parse_date(date_str: str) -> dt | None:
    """Parse a date string into a datetime, trying multiple formats."""
    if not date_str:
        return None
    clean = date_str.strip()
    for fmt in _DATE_FORMATS:
        try:
            return dt.strptime(clean, fmt)
        except (ValueError, IndexError):
            continue
    # Try just the first 10 chars for YYYY-MM-DD or MM/DD/YYYY
    short = clean[:10]
    for fmt in _DATE_FORMATS[1:]:
        try:
            return dt.strptime(short, fmt)
        except (ValueError, IndexError):
            continue
    return None


def _normalize_date(date_str: str) -> str:
    """Normalize a date string to YYYY-MM-DD for consistent sorting."""
    d = _parse_date(date_str)
    if d:
        return d.strftime("%Y-%m-%d")
    return date_str


def _days_between(date1: str, date2: str) -> float:
    """Compute days between two date strings."""
    d1 = _parse_date(date1)
    d2 = _parse_date(date2)
    if d1 and d2:
        return abs((d2 - d1).days)
    return 30.0  # fallback


# ---------------------------------------------------------------------------
# Priority 1: EMMA Trade Returns
# ---------------------------------------------------------------------------

def _collect_emma_trade_returns(
    emma_bonds: list[dict],
    coupon_rate: float | None = None,
) -> list[tuple[str, float, float]]:
    """Collect (date, return, price) from all EMMA bonds for this obligor.

    Merges trades across multiple CUSIPs. When multiple bonds trade on
    the same date, keeps the first observation (already sorted by time).
    """
    all_observations: list[tuple[str, float, float]] = []

    for bond_data in emma_bonds:
        series = build_bond_returns(bond_data, coupon_rate)
        if series.n < 1:
            continue
        for date, ret, price in zip(series.dates, series.returns, series.prices):
            norm_date = _normalize_date(date)
            all_observations.append((norm_date, ret, price))

    # Sort by date
    all_observations.sort(key=lambda x: x[0])

    # Deduplicate same-date entries (keep first)
    seen_dates: dict[str, tuple[str, float, float]] = {}
    for obs in all_observations:
        date_key = obs[0][:10]
        if date_key not in seen_dates:
            seen_dates[date_key] = obs

    deduped = sorted(seen_dates.values(), key=lambda x: x[0])
    return deduped


# ---------------------------------------------------------------------------
# Priority 2: Rating Event Shocks
# ---------------------------------------------------------------------------

def _insert_rating_shocks(
    observations: list[tuple[str, float, float]],
    rating_actions: list[dict],
    modified_duration: float,
    proximity_days: int = 5,
) -> list[tuple[str, float, float]]:
    """Insert rating transition shocks as return observations.

    Only inserts if no EMMA trade within +/- proximity_days of the event.
    Positive spread change (downgrade) => negative return.
    """
    existing_dates = {obs[0][:10] for obs in observations}
    new_obs = list(observations)

    for action in rating_actions:
        old_rating = action.get("previous_rating")
        new_rating = action.get("new_rating")
        action_date_raw = action.get("action_date")

        if not old_rating or not new_rating or not action_date_raw:
            continue

        delta_bps = rating_transition_spread_change(old_rating, new_rating)
        if delta_bps is None or abs(delta_bps) < 1.0:
            continue

        action_date = _normalize_date(str(action_date_raw))

        # Check proximity to existing observations
        too_close = False
        for existing_date in existing_dates:
            days_diff = _days_between(action_date, existing_date)
            if days_diff <= proximity_days:
                too_close = True
                break

        if too_close:
            continue

        ret = spread_change_to_return(delta_bps, modified_duration)
        new_obs.append((action_date, ret, 100.0))
        logger.debug(
            "Rating shock %s>%s on %s: delta=%+.0f bps, ret=%+.4f",
            old_rating, new_rating, action_date, delta_bps, ret,
        )

    new_obs.sort(key=lambda x: x[0])
    return new_obs


# ---------------------------------------------------------------------------
# Priority 3: Fundamental Drift
# ---------------------------------------------------------------------------

def _insert_fundamental_drift(
    observations: list[tuple[str, float, float]],
    financial_reports: list[dict],
    modified_duration: float,
) -> list[tuple[str, float, float]]:
    """Insert fundamental-driven spread drift in observation gaps.

    DSCR improvement => spread tightening => positive return.
    Revenue growth => spread tightening => positive return.
    """
    if len(financial_reports) < 2:
        return observations

    # Sort reports by date
    dated_reports = []
    for r in financial_reports:
        d = r.get("fiscal_period_end") or str(r.get("fiscal_year", ""))
        if d:
            norm = _normalize_date(str(d))
            dated_reports.append((norm, r))
    dated_reports.sort(key=lambda x: x[0])

    if len(dated_reports) < 2:
        return observations

    existing_dates = {obs[0][:10] for obs in observations}
    new_obs = list(observations)

    for i in range(1, len(dated_reports)):
        prev_date, prev_report = dated_reports[i - 1]
        curr_date, curr_report = dated_reports[i]

        # Skip if this date already has an observation
        if curr_date[:10] in existing_dates:
            continue

        # DSCR signal
        prev_dscr = prev_report.get("debt_service_coverage_ratio")
        curr_dscr = curr_report.get("debt_service_coverage_ratio")
        spread_change_bps = 0.0

        if prev_dscr and curr_dscr and prev_dscr > 0:
            dscr_delta = curr_dscr - prev_dscr
            # Each +0.1x DSCR improvement ~ -5 bps tightening
            spread_change_bps += -dscr_delta * 50.0

        # Revenue signal
        prev_rev = prev_report.get("total_revenue")
        curr_rev = curr_report.get("total_revenue")
        if prev_rev and curr_rev and prev_rev > 0:
            rev_growth = (curr_rev - prev_rev) / prev_rev
            # 10% revenue growth ~ -3 bps tightening
            spread_change_bps += -rev_growth * 30.0

        if abs(spread_change_bps) < 0.5:
            continue

        ret = spread_change_to_return(spread_change_bps, modified_duration)
        new_obs.append((curr_date, ret, 100.0))
        logger.debug(
            "Fundamental drift on %s: delta=%+.1f bps, ret=%+.4f",
            curr_date, spread_change_bps, ret,
        )

    new_obs.sort(key=lambda x: x[0])
    return new_obs


# ---------------------------------------------------------------------------
# Priority 4: Coupon Carry Interpolation
# ---------------------------------------------------------------------------

def _interpolate_carry(
    observations: list[tuple[str, float, float]],
    coupon_rate: float,
    max_gap_days: int = 180,
) -> list[tuple[str, float, float]]:
    """Fill remaining long gaps with monthly coupon carry returns.

    Assumes zero spread change -- pure accrual return.
    Only inserts at monthly intervals within gaps > max_gap_days.
    """
    if len(observations) < 2 or coupon_rate <= 0:
        return observations

    monthly_carry = coupon_rate / 12.0
    new_obs = list(observations)

    for i in range(1, len(observations)):
        prev_date_str = observations[i - 1][0]
        curr_date_str = observations[i][0]

        prev_d = _parse_date(prev_date_str)
        curr_d = _parse_date(curr_date_str)
        if not prev_d or not curr_d:
            continue

        gap_days = (curr_d - prev_d).days
        if gap_days <= max_gap_days:
            continue

        # Insert monthly carry observations in the gap
        n_months = gap_days // 30 - 1
        for m in range(1, max(n_months, 1) + 1):
            interp_d = prev_d + timedelta(days=m * 30)
            if interp_d >= curr_d:
                break
            interp_date = interp_d.strftime("%Y-%m-%d")
            new_obs.append((interp_date, monthly_carry, 100.0))

    new_obs.sort(key=lambda x: x[0])
    return new_obs


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------

def build_synthetic_returns(
    obligor_name: str,
    aliases: list[str] | None,
    engine: Engine,
    emma_bonds: list[dict] | None = None,
    coupon_rate: float | None = None,
    maturity_years: float | None = None,
    start_date: str = "2020-01-01",
    config: SyntheticReturnConfig | None = None,
) -> ReturnSeries | None:
    """Build synthetic return series from cascading bond data sources.

    Priority cascade:
      1. EMMA trade returns (highest fidelity)
      2. Rating event shocks (spread-duration model)
      3. Fundamental drift (DSCR/revenue changes)
      4. Coupon carry interpolation (gaps > max_gap_days)

    Returns None if insufficient data (< min_observations).
    """
    cfg = config or SyntheticReturnConfig()

    # Load EMMA bonds if not provided
    if emma_bonds is None:
        emma_bonds = load_emma_bonds_by_issuer(obligor_name, aliases)

    if not emma_bonds and not coupon_rate:
        logger.info("No EMMA data for %s and no coupon rate", obligor_name)
        return None

    # Extract coupon rate from first available bond
    if coupon_rate is None:
        for bond in (emma_bonds or []):
            cpn_str = bond.get("snapshot", {}).get("coupon_pct", "")
            if cpn_str:
                try:
                    # Handle formats like "5 %" or "3.45%"
                    clean = str(cpn_str).replace("%", "").strip()
                    coupon_rate = float(clean) / 100.0
                    break
                except ValueError:
                    continue
        coupon_rate = coupon_rate or 0.04  # Default 4%

    # Extract maturity from first available bond
    if maturity_years is None:
        for bond in (emma_bonds or []):
            mat_str = bond.get("snapshot", {}).get("maturity_date", "")
            if mat_str:
                mat_dt = _parse_date(str(mat_str))
                if mat_dt:
                    maturity_years = max((mat_dt - dt.now()).days / 365.25, 1.0)
                    break
        maturity_years = maturity_years or 10.0

    mod_duration = estimate_modified_duration(coupon_rate, maturity_years)

    # Priority 1: EMMA trade returns
    observations = _collect_emma_trade_returns(emma_bonds or [], coupon_rate)
    logger.info(
        "P1 EMMA trades: %d observations for %s", len(observations), obligor_name,
    )

    # Priority 2: Rating event shocks
    if not cfg.coupon_carry_only:
        rating_actions = load_rating_actions_for_obligor(engine, obligor_name, aliases)
        if rating_actions:
            observations = _insert_rating_shocks(
                observations, rating_actions, mod_duration, cfg.rating_proximity_days,
            )
            logger.info("P2 +rating shocks: %d observations", len(observations))

    # Priority 3: Fundamental drift
    if not cfg.coupon_carry_only:
        fin_reports = load_financial_reports_for_obligor(engine, obligor_name, aliases)
        if fin_reports:
            observations = _insert_fundamental_drift(
                observations, fin_reports, mod_duration,
            )
            logger.info("P3 +fundamental drift: %d observations", len(observations))

    # Priority 4: Coupon carry interpolation
    observations = _interpolate_carry(observations, coupon_rate, cfg.max_gap_days)
    logger.info("P4 +carry interpolation: %d observations", len(observations))

    # Filter by start_date
    norm_start = _normalize_date(start_date)
    observations = [(d, r, p) for d, r, p in observations if d >= norm_start]

    if len(observations) < cfg.min_observations:
        logger.info(
            "Insufficient synthetic data for %s (%d < %d)",
            obligor_name, len(observations), cfg.min_observations,
        )
        return None

    # Build ReturnSeries
    dates = [o[0] for o in observations]
    returns = [o[1] for o in observations]
    prices = [o[2] for o in observations]
    log_returns = [
        math.log(1.0 + r) if (1.0 + r) > 0 else -10.0 for r in returns
    ]

    # Create a short asset_id from obligor name
    asset_id = obligor_name.replace(" ", "_")[:20]

    logger.info(
        "Built synthetic returns for %s: %d obs, coupon=%.2f%%, ModDur=%.1f",
        obligor_name, len(returns), coupon_rate * 100, mod_duration,
    )

    return ReturnSeries(
        asset_id=asset_id,
        asset_name=obligor_name,
        asset_type="bond",
        dates=dates,
        returns=returns,
        log_returns=log_returns,
        prices=prices,
        frequency="irregular",
    )
