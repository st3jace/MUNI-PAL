"""3-Statement Financial Model for municipal project finance.

Generates pro forma income statement, balance sheet, and cash flow
projections based on project inputs and bond sizing results.

Designed for revenue bond analysis where the cash flow waterfall is:
  Gross Revenue -> Operating Expenses -> Net Revenue ->
  Debt Service (P&I) -> DSRF -> R&R Fund -> Surplus
"""

from __future__ import annotations

import logging

from .models import (
    BalanceSheetYear,
    BondSizingResult,
    CashFlowYear,
    IncomeStatementYear,
    ProjectInputs,
    ThreeStatementModel,
)

logger = logging.getLogger("credit_analyzer.financial_model")

# Default assumptions
DEFAULT_DEPRECIATION_RATE = 0.025    # 2.5% of fixed assets
DEFAULT_EXPENSE_GROWTH_FACTOR = 0.8  # Expenses grow at 80% of revenue growth
DEFAULT_CAPEX_PCT_REVENUE = 0.05     # 5% of revenue for ongoing capex
DEFAULT_WORKING_CAPITAL_DAYS = 45    # 45 days of revenue as working capital
DEFAULT_PROJECTION_YEARS = 10


def build_financial_model(
    project: ProjectInputs,
    sizing: BondSizingResult | None = None,
    projection_years: int = DEFAULT_PROJECTION_YEARS,
) -> ThreeStatementModel:
    """Build a 3-statement pro forma model from project inputs.

    If bond sizing results are provided, debt service is integrated
    into the cash flow projections. Otherwise, existing debt only.
    """
    # --- Resolve base financials ---
    base_revenue = project.historical_revenue or 0.0
    base_expenses = project.historical_expenses or 0.0
    rev_growth = project.revenue_growth_rate or 0.02
    exp_growth = rev_growth * DEFAULT_EXPENSE_GROWTH_FACTOR
    margin = project.operating_margin

    # If margin provided but no expenses, derive expenses
    if base_revenue > 0 and base_expenses == 0 and margin:
        base_expenses = base_revenue * (1 - margin)

    base_assets = project.total_assets or (base_revenue * 3)  # Rule of thumb
    base_liabilities = project.total_liabilities or (base_assets * 0.6)
    base_equity = project.total_equity or (base_assets - base_liabilities)
    base_cash = project.cash_on_hand or (base_revenue * 0.1)

    # Fixed assets estimate (total assets minus working capital)
    wc_estimate = base_revenue * DEFAULT_WORKING_CAPITAL_DAYS / 365
    fixed_assets = max(base_assets - wc_estimate, base_assets * 0.7)

    # New project additions
    new_par = sizing.recommended_par if sizing else 0.0
    new_project_fund = sizing.project_fund if sizing else 0.0
    annual_ds = sizing.annual_debt_service if sizing else 0.0
    dsrf = sizing.debt_service_reserve if sizing else 0.0

    # If detailed projections exist, use them
    has_detailed = len(project.revenue_projections) >= 3
    start_year = 2026
    if has_detailed:
        start_year = project.revenue_projections[0].year

    assumptions = {
        "base_revenue": base_revenue,
        "base_expenses": base_expenses,
        "revenue_growth": rev_growth,
        "expense_growth": exp_growth,
        "depreciation_rate": DEFAULT_DEPRECIATION_RATE,
        "capex_pct_revenue": DEFAULT_CAPEX_PCT_REVENUE,
        "new_bond_par": new_par,
        "annual_debt_service": annual_ds,
        "projection_years": projection_years,
    }

    income_stmts: list[IncomeStatementYear] = []
    balance_sheets: list[BalanceSheetYear] = []
    cash_flows: list[CashFlowYear] = []

    # Running balances
    cum_debt = project.existing_debt + new_par
    cum_equity = base_equity + (project.equity_contribution or 0)
    cum_fixed = fixed_assets + new_project_fund
    cum_cash = base_cash + dsrf

    for i in range(projection_years):
        year = start_year + i

        # --- Revenue & Expenses ---
        if has_detailed and i < len(project.revenue_projections):
            rp = project.revenue_projections[i]
            gross_rev = rp.gross_revenue
            op_exp = rp.operating_expenses
            net_rev = rp.net_revenue if rp.net_revenue is not None else (gross_rev - op_exp)
            capex = rp.capital_expenditures
        else:
            gross_rev = base_revenue * (1 + rev_growth) ** (i + 1)
            op_exp = base_expenses * (1 + exp_growth) ** (i + 1)
            net_rev = gross_rev - op_exp
            capex = gross_rev * DEFAULT_CAPEX_PCT_REVENUE

        # Depreciation
        depreciation = cum_fixed * DEFAULT_DEPRECIATION_RATE

        # EBITDA
        ebitda = gross_rev - op_exp

        # Interest expense (approximate — level debt service split)
        interest = cum_debt * (sizing.coupon_rate if sizing else 0.05) if cum_debt > 0 else 0.0
        principal_payment = max(0, annual_ds - interest)

        # Net income
        net_income = ebitda - depreciation - interest

        # Margins
        op_margin = ebitda / gross_rev if gross_rev > 0 else 0.0
        net_margin = net_income / gross_rev if gross_rev > 0 else 0.0

        # DSCR
        dscr = net_rev / annual_ds if annual_ds > 0 else 0.0

        # --- Income Statement ---
        income_stmts.append(IncomeStatementYear(
            year=year,
            gross_revenue=round(gross_rev, 2),
            operating_expenses=round(op_exp, 2),
            ebitda=round(ebitda, 2),
            depreciation=round(depreciation, 2),
            interest_expense=round(interest, 2),
            net_income=round(net_income, 2),
            operating_margin=round(op_margin, 4),
            net_margin=round(net_margin, 4),
        ))

        # --- Balance Sheet ---
        # Update running balances
        cum_fixed = cum_fixed + capex - depreciation
        cum_debt = max(0, cum_debt - principal_payment)
        cum_equity = cum_equity + net_income
        current_assets = wc_estimate * (1 + rev_growth) ** (i + 1) + cum_cash
        total_assets = current_assets + cum_fixed
        current_liabilities = op_exp / 12 * 2  # ~2 months payables
        total_liabilities = current_liabilities + cum_debt
        cr = current_assets / current_liabilities if current_liabilities > 0 else 0.0
        lev = total_liabilities / cum_equity if cum_equity > 0 else 0.0

        balance_sheets.append(BalanceSheetYear(
            year=year,
            total_assets=round(total_assets, 2),
            current_assets=round(current_assets, 2),
            fixed_assets=round(cum_fixed, 2),
            total_liabilities=round(total_liabilities, 2),
            current_liabilities=round(current_liabilities, 2),
            long_term_debt=round(cum_debt, 2),
            total_equity=round(cum_equity, 2),
            current_ratio=round(cr, 4),
            leverage_ratio=round(lev, 4),
        ))

        # --- Cash Flow ---
        operating_cf = net_income + depreciation
        fcf = operating_cf - capex - annual_ds
        cum_cash = max(0, cum_cash + fcf)

        cash_flows.append(CashFlowYear(
            year=year,
            net_income=round(net_income, 2),
            depreciation=round(depreciation, 2),
            operating_cash_flow=round(operating_cf, 2),
            capital_expenditures=round(capex, 2),
            debt_service_principal=round(principal_payment, 2),
            debt_service_interest=round(interest, 2),
            free_cash_flow=round(fcf, 2),
            dscr=round(dscr, 4),
            cash_balance=round(cum_cash, 2),
        ))

    return ThreeStatementModel(
        project_name=project.project_name,
        projection_years=projection_years,
        income_statements=income_stmts,
        balance_sheets=balance_sheets,
        cash_flows=cash_flows,
        assumptions=assumptions,
    )
