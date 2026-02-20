"""Municipal bond credit spread table for rating-to-return conversion.

Maps credit ratings to basis point spreads over AAA MMD (Municipal Market Data).
Used by the synthetic return builder to convert rating transitions into
estimated price returns via modified duration.

Spread sources: Bloomberg municipal curve analytics, ICE MMD curves,
typical waste sector revenue bond spreads.
"""
from __future__ import annotations

import logging

logger = logging.getLogger("bond_os_extractor.analysis.spread_table")

# Spreads in basis points over AAA MMD
DEFAULT_MUNI_SPREADS: dict[str, int] = {
    # S&P / Fitch scale
    "AAA": 0, "AA+": 12, "AA": 20, "AA-": 32,
    "A+": 45, "A": 62, "A-": 82,
    "BBB+": 110, "BBB": 145, "BBB-": 190,
    "BB+": 250, "BB": 340, "BB-": 450,
    "B+": 600, "B": 800, "B-": 1000,
    "CCC+": 1100, "CCC": 1200, "CCC-": 1400,
    "CC": 1800, "C": 2500, "D": 5000,
    # Moody's scale (mapped to equivalent S&P spread)
    "Aaa": 0, "Aa1": 12, "Aa2": 20, "Aa3": 32,
    "A1": 45, "A2": 62, "A3": 82,
    "Baa1": 110, "Baa2": 145, "Baa3": 190,
    "Ba1": 250, "Ba2": 340, "Ba3": 450,
    "B1": 600, "B2": 800, "B3": 1000,
    "Caa1": 1100, "Caa2": 1200, "Caa3": 1400,
    "Ca": 1800,
}


def get_spread_bps(
    rating: str | None,
    table: dict[str, int] | None = None,
) -> int | None:
    """Get spread in basis points for a rating string.

    Returns None if rating is unknown.
    """
    if not rating:
        return None
    clean = rating.strip()
    t = table or DEFAULT_MUNI_SPREADS
    return t.get(clean)


def rating_transition_spread_change(
    old_rating: str | None,
    new_rating: str | None,
    table: dict[str, int] | None = None,
) -> float | None:
    """Compute spread change (bps) from a rating transition.

    Returns positive value for downgrades (spread widens),
    negative for upgrades (spread tightens).
    Returns None if either rating is unknown.
    """
    old_bps = get_spread_bps(old_rating, table)
    new_bps = get_spread_bps(new_rating, table)
    if old_bps is None or new_bps is None:
        return None
    return float(new_bps - old_bps)


def estimate_modified_duration(
    coupon_rate: float,
    maturity_years: float,
    yield_rate: float | None = None,
) -> float:
    """Estimate modified duration from bond characteristics.

    Simple semiannual convention approximation:
        ModDur ~ (maturity_years * (1 - coupon/2)) / (1 + yield/2)

    Parameters:
        coupon_rate: Annual coupon rate as decimal (e.g., 0.05 for 5%)
        maturity_years: Years to maturity
        yield_rate: Current yield as decimal (defaults to coupon_rate)

    Returns modified duration in years.
    """
    if maturity_years <= 0:
        return 0.0
    if yield_rate is None:
        yield_rate = coupon_rate
    y = max(yield_rate, 0.001)
    c = coupon_rate
    mod_dur = (maturity_years * (1.0 - c / 2.0)) / (1.0 + y / 2.0)
    return max(mod_dur, 0.5)


def spread_change_to_return(
    delta_spread_bps: float,
    modified_duration: float,
) -> float:
    """Convert a spread change to an approximate price return.

    R_event ~ -ModifiedDuration * DeltaSpread

    Positive spread change (widening/downgrade) => negative return.
    Negative spread change (tightening/upgrade) => positive return.

    Parameters:
        delta_spread_bps: Spread change in basis points
        modified_duration: Modified duration in years

    Returns approximate simple return (e.g., -0.0175 for 1.75% loss).
    """
    delta_spread_decimal = delta_spread_bps / 10000.0
    return -modified_duration * delta_spread_decimal
