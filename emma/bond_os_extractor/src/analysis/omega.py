"""S_Omega, Omega ratio, and SIC matrix — Summers' performance measures.

Implements the core quantitative framework from:
  Paper 1: "An Intuitive True Total Risk-Adjusted Performance Measure"
  Paper 2: "The Standard Model of Complex Economic Systems"

Key formulas (Summers notation):

  S_Omega = r_f + E[r_f - r_mk]^+ * (E(R_i) - r_f) / E[r_f - r_ik]^+

  Omega(Theta, R_i) = E(R_i - Theta) / E[Theta - r_ik]^+ + 1

  SIC = [R_A(R_i), E_A(R_i), MDDD_S]
    R_A = (E[r_f - r_ik]^+ + 1)^n_Y - 1      (annualized risk)
    E_A = (E(R_i) + 1)^n_Y - 1                (annualized expected return)
    MDDD_S = MDDD_A + t_R                     (Summers max drawdown duration)

  P_BSE = (1/n) * 100%                        (Black Swan Event probability)
  A(S_Omega) = 1 - P_BSE                      (Accuracy)
"""
from __future__ import annotations

import json
import logging
import math
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from ..config import get_settings
from .return_series import ReturnSeries

logger = logging.getLogger("bond_os_extractor.analysis.omega")

# Default risk-free rate (annualized). ~4.5% = current Treasury approximation.
DEFAULT_RF_ANNUAL = 0.045


@dataclass
class OmegaResult:
    """Omega ratio result at a given threshold."""
    threshold: float        # Theta
    omega: float            # Omega(Theta)
    upside: float           # E[R_i - Theta]^+
    downside: float         # E[Theta - r_ik]^+


@dataclass
class SICMatrix:
    """Summers Intuitive Characteristics matrix.

    SIC = [R_A(R_i), E_A(R_i), MDDD_S]

    These three values fully characterize an asset's risk-return-liquidity
    profile in intuitive percentage/duration terms.
    """
    annualized_risk: float          # R_A — annualized downside risk (%)
    annualized_return: float        # E_A — annualized expected return (%)
    max_drawdown_duration: float    # MDDD_S — max drawdown + recovery (periods)
    max_drawdown_duration_years: float = 0.0  # MDDD_S in years

    # Drawdown components
    mddd_a: float = 0.0            # Traditional max drawdown duration (periods)
    recovery_time: float = 0.0     # t_R — additional recovery periods
    max_drawdown_pct: float = 0.0  # Maximum drawdown depth (%)


@dataclass
class SOmegaResult:
    """Complete S_Omega analysis for one asset."""
    asset_id: str
    asset_name: str
    asset_type: str

    # Core Summers measures
    s_omega: float = 0.0           # Summers total risk-adjusted performance (%)
    omega_at_rf: float = 0.0       # Omega ratio at r_f threshold
    sic: SICMatrix | None = None   # SIC characteristics matrix

    # Inputs
    geometric_mean: float = 0.0    # E(R_i) per period
    risk_free_rate: float = 0.0    # r_f per period
    downside_risk: float = 0.0     # E[r_f - r_ik]^+ per period
    market_downside: float = 0.0   # E[r_f - r_mk]^+ per period

    # Statistical summary
    n_observations: int = 0
    n_years: float = 0.0
    periods_per_year: float = 252.0

    # Accuracy (Summers)
    p_bse: float = 0.0            # P_BSE = 1/n (Black Swan probability)
    accuracy: float = 0.0         # A(S_Omega) = 1 - P_BSE

    # Omega curve (multiple thresholds)
    omega_curve: list[OmegaResult] = field(default_factory=list)

    # F_i from Phase 1 (if available)
    f_score: float | None = None


def _period_rf(annual_rf: float, periods_per_year: float) -> float:
    """Convert annual risk-free rate to per-period rate."""
    return (1.0 + annual_rf) ** (1.0 / periods_per_year) - 1.0


def compute_omega(
    series: ReturnSeries,
    threshold: float,
) -> OmegaResult:
    """Compute Omega ratio at a given threshold.

    Keating-Shadwick (2002) definition:
        Omega(Theta) = E[R_i - Theta]^+ / E[Theta - R_i]^+

    This is the ratio of probability-weighted gains above Theta to
    probability-weighted losses below Theta. Always >= 0.

    Omega > 1 means the asset's gain potential exceeds its loss
    potential at that threshold. At the geometric mean, Omega = 1.
    """
    upside = series.upside_expectation(threshold)
    downside = series.downside_expectation(threshold)

    if downside <= 0:
        omega = float("inf") if upside > 0 else 1.0
    elif upside <= 0:
        omega = 0.0
    else:
        omega = upside / downside

    return OmegaResult(
        threshold=threshold,
        omega=omega,
        upside=upside,
        downside=downside,
    )


def compute_omega_curve(
    series: ReturnSeries,
    rf_period: float,
    n_points: int = 21,
) -> list[OmegaResult]:
    """Compute Omega ratio across a range of thresholds.

    Sweeps from well below the mean to well above, centered on r_f.
    This produces the Omega curve for visualization and analysis.
    """
    if not series.returns:
        return []

    min_ret = min(series.returns)
    max_ret = max(series.returns)
    step = (max_ret - min_ret) / (n_points - 1) if n_points > 1 else 0.001

    curve = []
    for i in range(n_points):
        threshold = min_ret + i * step
        result = compute_omega(series, threshold)
        curve.append(result)

    return curve


def compute_sic(
    series: ReturnSeries,
    rf_period: float,
) -> SICMatrix:
    """Compute SIC matrix (Summers Intuitive Characteristics).

    SIC = [R_A(R_i), E_A(R_i), MDDD_S]

    R_A(R_i) = (E[r_f - r_ik]^+ + 1)^n_Y - 1    (annualized risk)
    E_A(R_i) = (E(R_i) + 1)^n_Y - 1              (annualized expected return)
    MDDD_S = MDDD_A + t_R
    """
    n_y = series.periods_per_year
    geo_mean = series.geometric_mean()
    downside = series.downside_expectation(rf_period)

    # Annualized risk
    r_a = (downside + 1.0) ** n_y - 1.0

    # Annualized expected return
    e_a = (geo_mean + 1.0) ** n_y - 1.0

    # MDDD_S = max drawdown duration + recovery time
    mddd_a, recovery, max_dd_pct = _compute_drawdown_metrics(series)
    mddd_s = mddd_a + recovery

    return SICMatrix(
        annualized_risk=r_a,
        annualized_return=e_a,
        max_drawdown_duration=mddd_s,
        max_drawdown_duration_years=mddd_s / n_y if n_y > 0 else 0.0,
        mddd_a=mddd_a,
        recovery_time=recovery,
        max_drawdown_pct=max_dd_pct,
    )


def _compute_drawdown_metrics(series: ReturnSeries) -> tuple[float, float, float]:
    """Compute drawdown duration, recovery time, and max drawdown depth.

    Returns (mddd_a, t_r, max_drawdown_pct):
      - mddd_a: Number of periods in the longest drawdown
      - t_r: Recovery periods after max drawdown (Summers extension)
      - max_drawdown_pct: Deepest drawdown as a fraction (negative)
    """
    cum = series.cumulative_returns()
    if not cum:
        return 0.0, 0.0, 0.0

    running_max = cum[0]
    max_dd = 0.0
    max_dd_start = 0
    max_dd_end = 0

    # Track current drawdown
    current_dd_start = 0
    in_drawdown = False

    # Track the longest drawdown duration
    max_duration = 0
    current_duration = 0
    longest_dd_start = 0
    longest_dd_end = 0

    for i, c in enumerate(cum):
        if c >= running_max:
            if in_drawdown:
                # Drawdown ended
                if current_duration > max_duration:
                    max_duration = current_duration
                    longest_dd_start = current_dd_start
                    longest_dd_end = i
                in_drawdown = False
                current_duration = 0
            running_max = c
        else:
            if not in_drawdown:
                current_dd_start = i
                in_drawdown = True
            current_duration += 1

            dd = (c - running_max) / running_max
            if dd < max_dd:
                max_dd = dd
                max_dd_end = i

    # Handle ongoing drawdown at end of series
    if in_drawdown and current_duration > max_duration:
        max_duration = current_duration
        longest_dd_end = len(cum) - 1

    # Recovery time: periods from max drawdown trough to recovery of peak
    # This is Summers' t_R extension — the forgone expected return period
    geo_mean = series.geometric_mean()
    if max_dd < 0 and geo_mean > 0:
        # Periods needed to recover from max drawdown at the geometric mean rate
        # (1 + geo_mean)^t_R = 1 / (1 + max_dd)
        recovery = math.log(1.0 / (1.0 + max_dd)) / math.log(1.0 + geo_mean)
    else:
        recovery = 0.0

    return float(max_duration), max(recovery, 0.0), max_dd


def compute_s_omega(
    series: ReturnSeries,
    market_series: ReturnSeries,
    rf_annual: float = DEFAULT_RF_ANNUAL,
    f_score: float | None = None,
) -> SOmegaResult:
    """Compute S_Omega — Summers Total Risk-Adjusted Performance Measure.

    S_Omega = r_f + E[r_f - r_mk]^+ * (E(R_i) - r_f) / E[r_f - r_ik]^+

    Where:
      r_f = risk-free rate per period
      E(R_i) = geometric mean return of asset i
      E[r_f - r_ik]^+ = expected downside of asset below r_f (put price)
      E[r_f - r_mk]^+ = expected downside of market below r_f

    S_Omega captures all four statistical moments and is denominated in
    the same units as r_f, making it directly interpretable as a
    risk-adjusted return.
    """
    if series.n < 2:
        logger.warning("Insufficient data for %s (%d obs)", series.asset_id, series.n)
        return SOmegaResult(
            asset_id=series.asset_id,
            asset_name=series.asset_name,
            asset_type=series.asset_type,
            n_observations=series.n,
            f_score=f_score,
        )

    rf_period = _period_rf(rf_annual, series.periods_per_year)
    geo_mean = series.geometric_mean()

    # Asset downside
    asset_downside = series.downside_expectation(rf_period)

    # Market downside (aligned to same period frequency)
    market_rf = _period_rf(rf_annual, market_series.periods_per_year)
    market_downside = market_series.downside_expectation(market_rf)

    # S_Omega calculation
    if asset_downside <= 0:
        # No downside risk — asset never fell below r_f
        s_omega = rf_period + (geo_mean - rf_period) if geo_mean > rf_period else rf_period
    else:
        excess = geo_mean - rf_period
        s_omega = rf_period + market_downside * excess / asset_downside

    # Annualize S_Omega for interpretability
    s_omega_annual = (1.0 + s_omega) ** series.periods_per_year - 1.0

    # Omega at r_f
    omega_at_rf = compute_omega(series, rf_period)

    # SIC matrix
    sic = compute_sic(series, rf_period)

    # Accuracy measures
    p_bse = 1.0 / series.n if series.n > 0 else 1.0
    accuracy = 1.0 - p_bse

    # Omega curve
    omega_curve = compute_omega_curve(series, rf_period)

    return SOmegaResult(
        asset_id=series.asset_id,
        asset_name=series.asset_name,
        asset_type=series.asset_type,
        s_omega=s_omega_annual,
        omega_at_rf=omega_at_rf.omega,
        sic=sic,
        geometric_mean=geo_mean,
        risk_free_rate=rf_period,
        downside_risk=asset_downside,
        market_downside=market_downside,
        n_observations=series.n,
        n_years=series.n_years,
        periods_per_year=series.periods_per_year,
        p_bse=p_bse,
        accuracy=accuracy,
        omega_curve=omega_curve,
        f_score=f_score,
    )


def analyze_universe(
    investable_scores: list[dict],
    ticker_base_dir: Path | None = None,
    rf_annual: float = DEFAULT_RF_ANNUAL,
    start_date: str = "2020-01-01",
    engine: Any = None,
) -> list[SOmegaResult]:
    """Run S_Omega analysis on the investable universe from Phase 1.

    Takes the investable set from the fundamental scoring engine and
    computes Summers' performance measures for each obligor with
    equity or bond data.

    Parameters:
        engine: SQLAlchemy Engine for bond corpus access. Required for
            municipal obligors that use synthetic bond return series.
    """
    from .return_series import build_equity_returns, build_market_benchmark, build_bond_market_benchmark

    logger.info("Building market benchmark...")
    market = build_market_benchmark(
        base_dir=ticker_base_dir, start_date=start_date,
    )

    if market.n < 60:
        logger.error(
            "Market benchmark has insufficient data (%d obs). "
            "Cannot compute S_Omega.", market.n,
        )
        return []

    results: list[SOmegaResult] = []
    bond_market = None  # Lazy — built only if needed

    for score_data in investable_scores:
        ticker = score_data.get("ticker")
        obligor_name = score_data.get("obligor_name", "")
        f_score = score_data.get("f_score")

        if ticker:
            # Equity-backed obligor — use dense daily returns
            series = build_equity_returns(ticker, ticker_base_dir, start_date)
            if series.n < 60:
                logger.info(
                    "Skipping %s -- insufficient equity data (%d obs)",
                    ticker, series.n,
                )
                continue
            asset_market = market
        else:
            # Municipal obligor — try synthetic bond return series
            if engine is None:
                logger.info(
                    "Skipping %s -- no engine for bond data", obligor_name,
                )
                continue

            from .synthetic_returns import build_synthetic_returns
            aliases = score_data.get("aliases", [])
            series = build_synthetic_returns(
                obligor_name, aliases, engine, start_date=start_date,
            )
            if series is None or series.n < 8:
                logger.info(
                    "Skipping %s -- insufficient synthetic data (%d obs)",
                    obligor_name, series.n if series else 0,
                )
                continue

            # Build bond benchmark lazily
            if bond_market is None:
                bond_market = build_bond_market_benchmark(start_date)
                logger.info("Bond benchmark: %d observations", bond_market.n)

            # Use bond benchmark if it has data, otherwise fall back to equity
            asset_market = bond_market if bond_market.n >= 8 else market

        result = compute_s_omega(series, asset_market, rf_annual, f_score)
        results.append(result)
        label = ticker or series.asset_id
        logger.info(
            "  %s: S_Omega=%.2f%%, Omega=%.3f, R_A=%.2f%%, E_A=%.2f%%, "
            "MDDD_S=%.1f yrs, Accuracy=%.1f%%, n=%d",
            label,
            result.s_omega * 100,
            result.omega_at_rf,
            result.sic.annualized_risk * 100 if result.sic else 0,
            result.sic.annualized_return * 100 if result.sic else 0,
            result.sic.max_drawdown_duration_years if result.sic else 0,
            result.accuracy * 100,
            result.n_observations,
        )

    # Sort by S_Omega descending
    results.sort(key=lambda r: r.s_omega, reverse=True)
    return results


def export_s_omega(
    results: list[SOmegaResult],
    output_path: Path | None = None,
) -> Path:
    """Export S_Omega analysis results to JSON."""
    if output_path is None:
        output_path = get_settings().data_dir / "analysis" / "s_omega_results.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "analysis": "S_Omega — Summers Total Risk-Adjusted Performance",
        "generated_at": datetime.now().isoformat(),
        "n_assets": len(results),
        "results": [
            {
                "asset_id": r.asset_id,
                "asset_name": r.asset_name,
                "asset_type": r.asset_type,
                "s_omega_pct": round(r.s_omega * 100, 4),
                "omega_at_rf": round(r.omega_at_rf, 4),
                "sic": {
                    "annualized_risk_pct": round(r.sic.annualized_risk * 100, 4),
                    "annualized_return_pct": round(r.sic.annualized_return * 100, 4),
                    "mddd_s_years": round(r.sic.max_drawdown_duration_years, 2),
                    "mddd_a_periods": round(r.sic.mddd_a, 0),
                    "recovery_periods": round(r.sic.recovery_time, 0),
                    "max_drawdown_pct": round(r.sic.max_drawdown_pct * 100, 2),
                } if r.sic else None,
                "geometric_mean_period": round(r.geometric_mean, 8),
                "risk_free_period": round(r.risk_free_rate, 8),
                "downside_risk_period": round(r.downside_risk, 8),
                "market_downside_period": round(r.market_downside, 8),
                "n_observations": r.n_observations,
                "n_years": round(r.n_years, 2),
                "p_bse_pct": round(r.p_bse * 100, 4),
                "accuracy_pct": round(r.accuracy * 100, 4),
                "f_score": r.f_score,
                "omega_curve": [
                    {
                        "threshold": round(o.threshold, 8),
                        "omega": round(o.omega, 4) if not math.isinf(o.omega) else "inf",
                    }
                    for o in r.omega_curve
                ],
            }
            for r in results
        ],
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)

    logger.info("Exported S_Omega results to %s", output_path)
    return output_path
