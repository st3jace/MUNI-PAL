"""Return series construction for S_Omega calculation.

Builds return time series from two data channels:

  1. Equity returns (daily): Close-to-close log returns from ticker history.
     Dense, regular, suitable for full Hilbert space analysis (Phase 4).

  2. Bond returns (irregular): Total return from EMMA secondary market trades
     incorporating price changes and coupon accrual. Sparse, matched to
     asset liquidity per Summers Paper 1 Section 2.

  3. Market benchmark: Equal-weighted basket of all waste sector tickers
     with available data. Represents the sector "market" for S_Omega's
     market downside term E[r_f - r_mk]^+.

The equity channel provides the primary return series for Phase 2. Bond
returns supplement with asset-specific price discovery where trade data exists.
"""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .data_loader import (
    load_emma_bond_data,
    load_ticker_history,
    get_emma_trades,
)
from .obligor_mapping import get_all_tickers

logger = logging.getLogger("bond_os_extractor.analysis.return_series")


@dataclass
class ReturnSeries:
    """A time series of periodic returns for one asset."""
    asset_id: str               # Ticker symbol or CUSIP
    asset_name: str
    asset_type: str             # "equity" | "bond" | "market"
    dates: list[str] = field(default_factory=list)
    returns: list[float] = field(default_factory=list)      # Simple returns
    log_returns: list[float] = field(default_factory=list)   # ln(1 + r)
    prices: list[float] = field(default_factory=list)        # Underlying prices
    frequency: str = "daily"    # "daily" | "monthly" | "irregular"

    @property
    def n(self) -> int:
        """Number of return observations."""
        return len(self.returns)

    @property
    def n_years(self) -> float:
        """Approximate number of years of data."""
        if self.frequency == "daily":
            return self.n / 252.0
        elif self.frequency == "monthly":
            return self.n / 12.0
        # Irregular: compute from actual date range
        years = self._date_range_years()
        if years > 0:
            return years
        return self.n / 252.0  # fallback

    @property
    def periods_per_year(self) -> float:
        """n_Y — number of return periods per year (Summers notation)."""
        if self.frequency == "daily":
            return 252.0
        elif self.frequency == "monthly":
            return 12.0
        # Irregular: actual observation density
        years = self._date_range_years()
        if years > 0 and self.n > 0:
            return self.n / years
        return 252.0  # fallback

    def _date_range_years(self) -> float:
        """Compute span in years from first to last date."""
        if len(self.dates) < 2:
            return 0.0
        from datetime import datetime as _dt
        formats = ["%m/%d/%Y %I:%M %p", "%m/%d/%Y", "%Y-%m-%d"]
        d_first = d_last = None
        for fmt in formats:
            try:
                d_first = _dt.strptime(self.dates[0].strip()[:10], fmt)
                break
            except (ValueError, IndexError):
                continue
        for fmt in formats:
            try:
                d_last = _dt.strptime(self.dates[-1].strip()[:10], fmt)
                break
            except (ValueError, IndexError):
                continue
        if d_first and d_last:
            delta_days = abs((d_last - d_first).days)
            return max(delta_days / 365.25, 0.01)
        return 0.0

    def geometric_mean(self) -> float:
        """E(R_i) — geometric mean return per period.

        Summers Paper 1, Eq. 1:
            E(R) = [∏(R_k + 1)]^(1/n) - 1
        """
        if not self.returns:
            return 0.0
        product = 1.0
        for r in self.returns:
            product *= (1.0 + r)
        if product <= 0:
            return -1.0  # Total loss
        return product ** (1.0 / self.n) - 1.0

    def downside_expectation(self, threshold: float) -> float:
        """E[Θ - r_ik]^+ — expected value of the put (downside below threshold).

        Summers Paper 1, used in Omega denominator and S_Omega.
        This is the average of max(threshold - r_i, 0) across all periods.
        """
        if not self.returns:
            return 0.0
        shortfalls = [max(threshold - r, 0.0) for r in self.returns]
        return sum(shortfalls) / self.n

    def upside_expectation(self, threshold: float) -> float:
        """E[r_ik - Θ]^+ — expected value of the call (upside above threshold).

        Summers Paper 1, Omega numerator.
        """
        if not self.returns:
            return 0.0
        gains = [max(r - threshold, 0.0) for r in self.returns]
        return sum(gains) / self.n

    def cumulative_returns(self) -> list[float]:
        """Cumulative wealth index (1 + r_1)(1 + r_2)..."""
        if not self.returns:
            return []
        cum = [1.0 + self.returns[0]]
        for r in self.returns[1:]:
            cum.append(cum[-1] * (1.0 + r))
        return cum

    def drawdown_series(self) -> list[float]:
        """Drawdown from running maximum at each point."""
        cum = self.cumulative_returns()
        if not cum:
            return []
        running_max = cum[0]
        dd = []
        for c in cum:
            running_max = max(running_max, c)
            dd.append((c - running_max) / running_max if running_max > 0 else 0.0)
        return dd


def build_equity_returns(
    ticker: str,
    base_dir: Path | None = None,
    start_date: str | None = None,
) -> ReturnSeries:
    """Build daily return series from equity price history.

    Uses adjusted close prices to account for dividends and splits.
    Returns are simple close-to-close: r_t = (P_t / P_{t-1}) - 1.
    """
    history = load_ticker_history(ticker, base_dir)
    if not history:
        return ReturnSeries(
            asset_id=ticker, asset_name=ticker, asset_type="equity",
        )

    # Filter by start date if specified
    if start_date:
        history = [h for h in history if h["date"] >= start_date]

    # Extract valid prices
    filtered = []
    for h in history:
        price = h.get("adj_close") or h.get("close")
        if price is not None and price > 0:
            filtered.append((h["date"], price))

    if len(filtered) < 2:
        return ReturnSeries(
            asset_id=ticker, asset_name=ticker, asset_type="equity",
        )

    dates = []
    returns = []
    log_returns = []
    prices = []

    for i in range(1, len(filtered)):
        prev_price = filtered[i - 1][1]
        curr_price = filtered[i][1]
        r = (curr_price / prev_price) - 1.0
        lr = math.log(curr_price / prev_price)

        dates.append(filtered[i][0])
        returns.append(r)
        log_returns.append(lr)
        prices.append(curr_price)

    logger.info(
        "Built equity returns for %s: %d observations, %.1f years",
        ticker, len(returns), len(returns) / 252.0,
    )

    return ReturnSeries(
        asset_id=ticker,
        asset_name=ticker,
        asset_type="equity",
        dates=dates,
        returns=returns,
        log_returns=log_returns,
        prices=prices,
        frequency="daily",
    )


def build_bond_returns(
    emma_bond_data: dict,
    coupon_rate: float | None = None,
) -> ReturnSeries:
    """Build return series from EMMA secondary market trades.

    Bond total return per trade interval:
        r = (P_t - P_{t-1} + accrued_coupon) / P_{t-1}

    Where accrued_coupon is approximated from the annual coupon rate
    prorated over the trade interval.

    Per Summers Paper 1: return period should match asset liquidity.
    Bond returns are irregular — the frequency reflects actual trading.
    """
    sec_name = emma_bond_data.get("snapshot", {}).get("security_name", "Unknown")
    cusip = emma_bond_data.get("cusip", "")

    trades = get_emma_trades(emma_bond_data)
    if len(trades) < 2:
        return ReturnSeries(
            asset_id=cusip, asset_name=sec_name, asset_type="bond",
            frequency="irregular",
        )

    # Sort trades by date
    valid_trades = [
        t for t in trades
        if t.get("price") is not None and t["price"] > 0
    ]
    valid_trades.sort(key=lambda t: t.get("trade_date", ""))

    if len(valid_trades) < 2:
        return ReturnSeries(
            asset_id=cusip, asset_name=sec_name, asset_type="bond",
            frequency="irregular",
        )

    # Get coupon from snapshot if not provided
    if coupon_rate is None:
        coupon_str = emma_bond_data.get("snapshot", {}).get("coupon_pct", "")
        if coupon_str:
            try:
                coupon_rate = float(coupon_str) / 100.0
            except (ValueError, TypeError):
                coupon_rate = 0.0
        else:
            coupon_rate = 0.0

    dates = []
    returns = []
    log_returns = []
    prices = []

    for i in range(1, len(valid_trades)):
        prev_price = valid_trades[i - 1]["price"]
        curr_price = valid_trades[i]["price"]

        # Estimate days between trades for coupon accrual
        prev_date = valid_trades[i - 1].get("trade_date", "")
        curr_date = valid_trades[i].get("trade_date", "")

        # Rough day count from date strings (MM/DD/YYYY HH:MM AM/PM)
        days_between = _estimate_days(prev_date, curr_date)

        # Accrued coupon (simple day-count approximation)
        accrued = coupon_rate * (days_between / 365.0) * 100.0  # Per $100 par

        # Total return
        r = (curr_price - prev_price + accrued) / prev_price
        lr = math.log(1.0 + r) if (1.0 + r) > 0 else -10.0

        dates.append(curr_date)
        returns.append(r)
        log_returns.append(lr)
        prices.append(curr_price)

    logger.info(
        "Built bond returns for %s: %d observations from %d trades",
        cusip[:16], len(returns), len(valid_trades),
    )

    return ReturnSeries(
        asset_id=cusip,
        asset_name=sec_name,
        asset_type="bond",
        dates=dates,
        returns=returns,
        log_returns=log_returns,
        prices=prices,
        frequency="irregular",
    )


def build_market_benchmark(
    tickers: list[str] | None = None,
    base_dir: Path | None = None,
    start_date: str = "2020-01-01",
) -> ReturnSeries:
    """Build equal-weighted market benchmark from waste sector basket.

    The benchmark represents the waste sector "market" for S_Omega's
    market downside term E[r_f - r_mk]^+.

    Equal-weighted daily returns across all tickers with data on each date.
    """
    if tickers is None:
        tickers = get_all_tickers()

    # Load all equity return series
    all_series: dict[str, ReturnSeries] = {}
    for ticker in tickers:
        rs = build_equity_returns(ticker, base_dir, start_date)
        if rs.n >= 60:  # At least ~3 months of data
            all_series[ticker] = rs

    if not all_series:
        logger.warning("No tickers with sufficient data for benchmark")
        return ReturnSeries(
            asset_id="MARKET", asset_name="Waste Sector Benchmark",
            asset_type="market",
        )

    # Build date-aligned equal-weighted returns
    # Collect all returns by date across tickers
    date_returns: dict[str, list[float]] = {}
    for ticker, rs in all_series.items():
        for date, ret in zip(rs.dates, rs.returns):
            if date not in date_returns:
                date_returns[date] = []
            date_returns[date].append(ret)

    # Only keep dates where at least 3 tickers have data (for diversification)
    min_tickers = min(3, len(all_series))
    valid_dates = sorted(
        d for d, rets in date_returns.items() if len(rets) >= min_tickers
    )

    if not valid_dates:
        return ReturnSeries(
            asset_id="MARKET", asset_name="Waste Sector Benchmark",
            asset_type="market",
        )

    dates = []
    returns = []
    log_returns = []

    for date in valid_dates:
        rets = date_returns[date]
        avg_ret = sum(rets) / len(rets)
        dates.append(date)
        returns.append(avg_ret)
        log_returns.append(math.log(1.0 + avg_ret) if (1.0 + avg_ret) > 0 else -10.0)

    logger.info(
        "Built market benchmark: %d dates, %d tickers, from %s to %s",
        len(dates), len(all_series), dates[0], dates[-1],
    )

    return ReturnSeries(
        asset_id="MARKET",
        asset_name=f"Waste Sector Benchmark ({len(all_series)} tickers)",
        asset_type="market",
        dates=dates,
        returns=returns,
        log_returns=log_returns,
        frequency="daily",
    )


def _estimate_days(date1: str, date2: str) -> float:
    """Rough day count between two date strings.

    Handles formats like 'MM/DD/YYYY HH:MM AM/PM' and 'YYYY-MM-DD'.
    Falls back to 30 days if parsing fails.
    """
    from datetime import datetime as dt

    formats = [
        "%m/%d/%Y %I:%M %p",
        "%m/%d/%Y",
        "%Y-%m-%d",
    ]

    d1 = d2 = None
    for fmt in formats:
        try:
            d1 = dt.strptime(date1.strip()[:10] if len(date1) > 10 and "-" in date1 else date1.strip(), fmt)
            break
        except (ValueError, IndexError):
            continue

    for fmt in formats:
        try:
            d2 = dt.strptime(date2.strip()[:10] if len(date2) > 10 and "-" in date2 else date2.strip(), fmt)
            break
        except (ValueError, IndexError):
            continue

    if d1 and d2:
        delta = abs((d2 - d1).days)
        return max(delta, 1)

    return 30.0  # Fallback


# ---------------------------------------------------------------------------
# Bond return aggregation and benchmark
# ---------------------------------------------------------------------------

_BOND_DATE_FMTS = ["%m/%d/%Y %I:%M %p", "%m/%d/%Y", "%Y-%m-%d"]


def _normalize_bond_date(date_str: str) -> str:
    """Normalize a bond date string to YYYY-MM-DD for consistent sorting."""
    from datetime import datetime as _dt
    clean = date_str.strip()
    for fmt in _BOND_DATE_FMTS:
        try:
            return _dt.strptime(clean, fmt).strftime("%Y-%m-%d")
        except (ValueError, IndexError):
            continue
    # Try just the first 10 chars
    short = clean[:10]
    for fmt in _BOND_DATE_FMTS[1:]:
        try:
            return _dt.strptime(short, fmt).strftime("%Y-%m-%d")
        except (ValueError, IndexError):
            continue
    return date_str[:10]


def merge_return_series(
    series_list: list[ReturnSeries],
    name: str = "Merged",
) -> ReturnSeries:
    """Merge multiple bond CUSIP series into one obligor-level series.

    When multiple CUSIPs have returns on the same date, takes the
    equal-weighted average. Preserves chronological order.
    """
    if not series_list:
        return ReturnSeries(asset_id="MERGED", asset_name=name, asset_type="bond")

    if len(series_list) == 1:
        return series_list[0]

    # Collect all observations by date (normalize to YYYY-MM-DD)
    date_returns: dict[str, list[float]] = {}
    date_prices: dict[str, list[float]] = {}

    for s in series_list:
        for date, ret, price in zip(s.dates, s.returns, s.prices):
            date_key = _normalize_bond_date(date)
            if date_key not in date_returns:
                date_returns[date_key] = []
                date_prices[date_key] = []
            date_returns[date_key].append(ret)
            date_prices[date_key].append(price)

    sorted_dates = sorted(date_returns.keys())
    dates = []
    returns = []
    log_rets = []
    prices = []

    for d in sorted_dates:
        avg_ret = sum(date_returns[d]) / len(date_returns[d])
        avg_price = sum(date_prices[d]) / len(date_prices[d])
        dates.append(d)
        returns.append(avg_ret)
        log_rets.append(math.log(1.0 + avg_ret) if (1.0 + avg_ret) > 0 else -10.0)
        prices.append(avg_price)

    return ReturnSeries(
        asset_id=series_list[0].asset_id,
        asset_name=name,
        asset_type="bond",
        dates=dates,
        returns=returns,
        log_returns=log_rets,
        prices=prices,
        frequency="irregular",
    )


def build_bond_market_benchmark(
    start_date: str = "2020-01-01",
) -> ReturnSeries:
    """Build municipal bond market benchmark from all EMMA waste sector trades.

    Equal-weighted average return across all bonds with trade data on each
    date. Provides the bond-appropriate market comparator for S_Omega's
    E[r_f - r_mk]^+ term.
    """
    all_bonds = load_emma_bond_data()
    if not all_bonds:
        return ReturnSeries(
            asset_id="BOND_MKT", asset_name="Waste Sector Bond Benchmark",
            asset_type="market", frequency="irregular",
        )

    # Build returns for each bond
    bond_series = []
    for bond_data in all_bonds:
        series = build_bond_returns(bond_data)
        if series.n >= 2:
            bond_series.append(series)

    if not bond_series:
        return ReturnSeries(
            asset_id="BOND_MKT", asset_name="Waste Sector Bond Benchmark",
            asset_type="market", frequency="irregular",
        )

    # Merge all into benchmark
    merged = merge_return_series(bond_series, "Waste Sector Bond Benchmark")

    # Filter by start_date
    filtered_dates = []
    filtered_returns = []
    filtered_log_returns = []
    filtered_prices = []
    for d, r, lr, p in zip(merged.dates, merged.returns, merged.log_returns, merged.prices):
        if d >= start_date:
            filtered_dates.append(d)
            filtered_returns.append(r)
            filtered_log_returns.append(lr)
            filtered_prices.append(p)

    logger.info(
        "Built bond benchmark: %d dates from %d bonds",
        len(filtered_dates), len(bond_series),
    )

    return ReturnSeries(
        asset_id="BOND_MKT",
        asset_name=f"Waste Sector Bond Benchmark ({len(bond_series)} bonds)",
        asset_type="market",
        dates=filtered_dates,
        returns=filtered_returns,
        log_returns=filtered_log_returns,
        prices=filtered_prices,
        frequency="irregular",
    )
