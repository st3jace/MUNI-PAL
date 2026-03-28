"""Bond Sizing Engine — DSCR-driven par amount calculation.

Sizes a bond issue based on projected net revenues and target coverage ratios.
Produces a debt service schedule and sensitivity analysis across DSCR targets.
"""

from __future__ import annotations

import logging
import math

from .models import (
    BondSizingResult,
    DebtServiceYear,
    ProjectInputs,
)

logger = logging.getLogger("credit_analyzer.bond_sizing")

# Default assumptions
DEFAULT_COUPON_RATE = 0.05          # 5.00%
DEFAULT_TARGET_DSCR = 1.25         # 1.25x minimum
DEFAULT_COI_PCT = 0.015            # 1.5% costs of issuance
DEFAULT_UW_DISCOUNT_PCT = 0.005    # 50 bps underwriter discount
DEFAULT_DSRF_MONTHS = 12           # 12 months max annual debt service
DEFAULT_DEPRECIATION_RATE = 0.025  # 2.5% annual depreciation


def _level_annual_debt_service(par: float, coupon: float, years: float) -> float:
    """Calculate level annual debt service (P&I) for a term bond."""
    if coupon <= 0 or years <= 0 or par <= 0:
        return 0.0
    r = coupon
    n = years
    # Standard mortgage-style amortization
    return par * (r * (1 + r) ** n) / ((1 + r) ** n - 1)


def _max_par_from_net_revenue(
    net_revenue: float,
    target_dscr: float,
    coupon: float,
    maturity_years: float,
) -> float:
    """Calculate maximum par amount given net revenue and target DSCR."""
    max_annual_ds = net_revenue / target_dscr
    if max_annual_ds <= 0:
        return 0.0
    # Invert the level debt service formula to solve for par
    r = coupon
    n = maturity_years
    if r <= 0:
        return max_annual_ds * n
    factor = (r * (1 + r) ** n) / ((1 + r) ** n - 1)
    return max_annual_ds / factor


def _build_debt_service_schedule(
    par: float,
    coupon: float,
    maturity_years: int,
    net_revenues: list[float],
    start_year: int = 1,
) -> list[DebtServiceYear]:
    """Build year-by-year debt service schedule with DSCR."""
    schedule = []
    balance = par
    annual_ds = _level_annual_debt_service(par, coupon, maturity_years)

    for i in range(maturity_years):
        year = start_year + i
        interest = balance * coupon
        principal = annual_ds - interest
        if principal > balance:
            principal = balance
        total = principal + interest
        balance -= principal

        # Net revenue for this year
        if i < len(net_revenues):
            nr = net_revenues[i]
        elif net_revenues:
            nr = net_revenues[-1]  # Extend last year
        else:
            nr = 0.0

        dscr = nr / total if total > 0 else 0.0

        schedule.append(DebtServiceYear(
            year=year,
            principal=round(principal, 2),
            interest=round(interest, 2),
            total=round(total, 2),
            net_revenue=round(nr, 2),
            dscr=round(dscr, 4),
        ))

        if balance <= 0:
            break

    return schedule


def size_bond(
    project: ProjectInputs,
    target_dscr: float = DEFAULT_TARGET_DSCR,
    coupon_rate: float | None = None,
) -> BondSizingResult:
    """Size a bond issue based on project inputs and target DSCR.

    Uses the minimum projected net revenue across the projection period
    to determine the maximum supportable par amount.
    """
    coupon = coupon_rate or project.target_coupon_rate or DEFAULT_COUPON_RATE
    maturity = int(project.target_maturity_years)
    notes: list[str] = []

    # Build net revenue series
    net_revenues: list[float] = []
    if project.revenue_projections:
        for rp in project.revenue_projections:
            nr = rp.net_revenue if rp.net_revenue is not None else (rp.gross_revenue - rp.operating_expenses)
            net_revenues.append(nr)
        notes.append(f"Using {len(net_revenues)}-year detailed projections")
    elif project.historical_revenue and project.historical_expenses:
        # Generate simple projections from growth rate
        base_rev = project.historical_revenue
        base_exp = project.historical_expenses
        growth = project.revenue_growth_rate or 0.02
        exp_growth = growth * 0.8  # Expenses grow slower than revenue

        for i in range(maturity):
            rev = base_rev * (1 + growth) ** (i + 1)
            exp = base_exp * (1 + exp_growth) ** (i + 1)
            net_revenues.append(rev - exp)
        notes.append(f"Projected from historical at {growth:.1%} revenue growth")
    elif project.historical_dscr and project.target_par_amount:
        # Back into net revenue from DSCR
        estimated_ds = _level_annual_debt_service(project.target_par_amount, coupon, maturity)
        estimated_nr = project.historical_dscr * estimated_ds
        net_revenues = [estimated_nr] * maturity
        notes.append(f"Estimated from DSCR {project.historical_dscr:.2f}x")
    else:
        notes.append("Insufficient data for bond sizing — provide revenue projections or historical financials")
        return BondSizingResult(sizing_notes=notes)

    if not net_revenues or min(net_revenues) <= 0:
        notes.append("Net revenue is zero or negative — cannot size bond")
        return BondSizingResult(sizing_notes=notes)

    # Use minimum net revenue for conservative sizing
    min_net_revenue = min(net_revenues)
    avg_net_revenue = sum(net_revenues) / len(net_revenues)
    notes.append(f"Min net revenue: ${min_net_revenue:,.0f} | Avg: ${avg_net_revenue:,.0f}")

    # Calculate max par at target DSCR
    max_par = _max_par_from_net_revenue(min_net_revenue, target_dscr, coupon, maturity)

    # Apply safety margin (size to 90% of max)
    recommended_par = math.floor(max_par / 1e6) * 1e6  # Round down to nearest $1M
    if project.target_par_amount:
        # If user specified target, check if it fits
        if project.target_par_amount <= max_par:
            recommended_par = project.target_par_amount
            notes.append(f"Target par ${project.target_par_amount/1e6:.0f}M fits within max capacity")
        else:
            notes.append(
                f"Target par ${project.target_par_amount/1e6:.0f}M exceeds max capacity "
                f"${max_par/1e6:.1f}M at {target_dscr:.2f}x DSCR"
            )

    # Build debt service schedule
    annual_ds = _level_annual_debt_service(recommended_par, coupon, maturity)
    max_annual_ds = annual_ds  # Level debt service = constant

    start_year = 1
    if project.revenue_projections:
        start_year = project.revenue_projections[0].year

    schedule = _build_debt_service_schedule(
        recommended_par, coupon, maturity, net_revenues, start_year,
    )

    min_dscr = min((yr.dscr for yr in schedule), default=0.0)
    avg_dscr = sum(yr.dscr for yr in schedule) / len(schedule) if schedule else 0.0

    # Sensitivity analysis
    par_120 = _max_par_from_net_revenue(min_net_revenue, 1.20, coupon, maturity)
    par_130 = _max_par_from_net_revenue(min_net_revenue, 1.30, coupon, maturity)
    par_140 = _max_par_from_net_revenue(min_net_revenue, 1.40, coupon, maturity)
    par_150 = _max_par_from_net_revenue(min_net_revenue, 1.50, coupon, maturity)

    # Sources & Uses
    dsrf = max_annual_ds  # 1x MADS
    coi = recommended_par * DEFAULT_COI_PCT
    uw_discount = recommended_par * DEFAULT_UW_DISCOUNT_PCT
    project_fund = recommended_par - dsrf - coi - uw_discount
    if project.total_project_cost:
        project_fund = min(project_fund, project.total_project_cost - (project.equity_contribution or 0))

    total_sources = recommended_par + (project.equity_contribution or 0)
    total_uses = project_fund + dsrf + coi + uw_discount

    return BondSizingResult(
        max_par_amount=round(max_par, 2),
        recommended_par=round(recommended_par, 2),
        coupon_rate=coupon,
        maturity_years=maturity,
        annual_debt_service=round(annual_ds, 2),
        max_annual_debt_service=round(max_annual_ds, 2),
        min_dscr=round(min_dscr, 4),
        avg_dscr=round(avg_dscr, 4),
        target_dscr=target_dscr,
        dscr_cushion_pct=round((min_dscr / target_dscr - 1) * 100, 2) if target_dscr > 0 else 0,
        schedule=schedule[:10],  # First 10 years for display
        par_at_dscr_1_20=round(par_120, 2),
        par_at_dscr_1_30=round(par_130, 2),
        par_at_dscr_1_40=round(par_140, 2),
        par_at_dscr_1_50=round(par_150, 2),
        total_sources=round(total_sources, 2),
        total_uses=round(total_uses, 2),
        project_fund=round(project_fund, 2),
        debt_service_reserve=round(dsrf, 2),
        costs_of_issuance=round(coi, 2),
        underwriter_discount=round(uw_discount, 2),
        sizing_notes=notes,
    )
