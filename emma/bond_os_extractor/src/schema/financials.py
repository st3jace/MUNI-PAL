from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class HistoricalFinancials(BaseModel):
    fiscal_year_end: str | None = None
    years_reported: list[int] = Field(default_factory=list)

    # Revenue data by year
    gross_revenues: dict[int, Decimal] = Field(default_factory=dict)
    operating_expenses: dict[int, Decimal] = Field(default_factory=dict)
    net_revenues: dict[int, Decimal] = Field(default_factory=dict)

    # Debt service coverage history
    annual_debt_service: dict[int, Decimal] = Field(default_factory=dict)
    dscr_historical: dict[int, Decimal] = Field(default_factory=dict)

    # Other key metrics
    operating_ratio: dict[int, Decimal] | None = None
    days_cash_on_hand: dict[int, int] | None = None

    # Audit information
    auditor_name: str | None = None
    audit_opinion_type: Literal[
        "unmodified", "qualified", "adverse", "disclaimer",
    ] | None = None
    going_concern_flag: bool = False


class ProjectedFinancials(BaseModel):
    projection_years: list[int] = Field(default_factory=list)
    projected_revenues: dict[int, Decimal] = Field(default_factory=dict)
    projected_expenses: dict[int, Decimal] = Field(default_factory=dict)
    projected_net_revenues: dict[int, Decimal] = Field(default_factory=dict)
    projected_debt_service: dict[int, Decimal] = Field(default_factory=dict)
    projected_dscr: dict[int, Decimal] = Field(default_factory=dict)

    # Assumptions
    revenue_growth_rate: Decimal | None = None
    expense_escalation_rate: Decimal | None = None
    inflation_assumption: Decimal | None = None
    capacity_utilization_assumed: Decimal | None = None


class DebtServiceRow(BaseModel):
    fiscal_year: int
    principal: Decimal | None = None
    interest: Decimal | None = None
    total: Decimal | None = None
    outstanding_balance: Decimal | None = None


class DebtServiceSchedule(BaseModel):
    rows: list[DebtServiceRow] = Field(default_factory=list)
    total_principal: Decimal | None = None
    total_interest: Decimal | None = None
    total_debt_service: Decimal | None = None
    maximum_annual_debt_service: Decimal | None = None


class SourcesAndUses(BaseModel):
    # Sources
    bond_proceeds: Decimal | None = None
    original_issue_premium: Decimal | None = None
    original_issue_discount: Decimal | None = None
    equity_contribution: Decimal | None = None
    other_sources: dict[str, Decimal] = Field(default_factory=dict)
    total_sources: Decimal | None = None

    # Uses
    project_fund_deposit: Decimal | None = None
    debt_service_reserve_deposit: Decimal | None = None
    capitalized_interest: Decimal | None = None
    costs_of_issuance: Decimal | None = None
    underwriter_discount: Decimal | None = None
    other_uses: dict[str, Decimal] = Field(default_factory=dict)
    total_uses: Decimal | None = None

    # Derived metrics
    cost_of_issuance_percentage: Decimal | None = None
    underwriter_spread_per_bond: Decimal | None = None
