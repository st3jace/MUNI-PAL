"""Credit Analyzer data models — project inputs, scoring, sizing, and structuring."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Project Input (what the user provides)
# ---------------------------------------------------------------------------

class ManagementProfile(BaseModel):
    """Character dimension inputs — management team assessment."""
    team_experience_years: float | None = None
    prior_projects_completed: int | None = None
    prior_project_defaults: int = 0
    industry_expertise: Literal["deep", "moderate", "limited", "none"] | None = None
    governance_structure: Literal["board_with_independents", "board", "owner_managed", "unclear"] | None = None
    regulatory_compliance_history: Literal["clean", "minor_issues", "material_issues", "enforcement_actions"] | None = None
    management_continuity_risk: Literal["low", "moderate", "high"] | None = None
    notes: str | None = None


class RevenueProjection(BaseModel):
    """Single year of revenue projection."""
    year: int
    gross_revenue: float
    operating_expenses: float
    net_revenue: float | None = None  # Computed if not provided
    capital_expenditures: float = 0.0
    debt_service: float | None = None  # Filled by bond sizing


class ProjectInputs(BaseModel):
    """Complete project/borrower inputs for credit analysis."""

    # Identity
    project_name: str
    borrower_name: str | None = None
    state: str | None = None
    sector: Literal["waste", "healthcare", "energy", "water", "transportation", "housing", "other"] = "waste"

    # Character (Management)
    management: ManagementProfile = Field(default_factory=ManagementProfile)

    # Capacity (Cash Flow)
    historical_revenue: float | None = None  # Most recent annual
    historical_expenses: float | None = None
    historical_net_income: float | None = None
    historical_dscr: float | None = None
    revenue_projections: list[RevenueProjection] = Field(default_factory=list)
    revenue_growth_rate: float | None = None  # Annual % if no detailed projections
    operating_margin: float | None = None

    # Capital (Balance Sheet)
    total_assets: float | None = None
    total_liabilities: float | None = None
    total_equity: float | None = None
    existing_debt: float = 0.0
    equity_contribution: float | None = None  # For new projects
    equity_contribution_pct: float | None = None  # As % of total project cost
    leverage_ratio: float | None = None  # Debt / equity
    current_ratio: float | None = None
    cash_on_hand: float | None = None

    # Collateral (Security)
    pledge_type: Literal["gross_revenue", "net_revenue", "specific_revenue", "none"] | None = None
    has_real_property: bool = False
    has_equipment_lien: bool = False
    has_offtake_agreements: bool = False
    offtake_counterparties: list[str] = Field(default_factory=list)
    has_insurance: bool = False
    lien_position: Literal["first", "second", "pari_passu", "subordinate"] | None = None

    # Conditions (Market / Environment)
    credit_rating: str | None = None  # Existing or expected
    rating_agency: str | None = None
    market_position: Literal["dominant", "strong", "competitive", "weak"] | None = None
    regulatory_environment: Literal["favorable", "stable", "challenging", "hostile"] | None = None
    sector_outlook: Literal["growing", "stable", "declining", "distressed"] | None = None
    competitive_threats: Literal["low", "moderate", "high"] | None = None

    # Deal parameters
    target_par_amount: float | None = None  # Desired issuance size
    target_maturity_years: float = 30.0
    target_coupon_rate: float | None = None  # If known
    tax_status: Literal["tax_exempt", "taxable", "amt"] = "tax_exempt"
    bond_type: Literal[
        "revenue", "general_obligation", "conduit_revenue",
        "private_activity", "lease_revenue", "other",
    ] = "revenue"
    is_green: bool = False
    is_refunding: bool = False
    total_project_cost: float | None = None

    # Risk flags
    has_technology_risk: bool = False
    has_construction_risk: bool = False
    has_environmental_risk: bool = False
    has_feedstock_risk: bool = False
    has_regulatory_risk: bool = False


# ---------------------------------------------------------------------------
# 5 Cs Scoring
# ---------------------------------------------------------------------------

class CScore(BaseModel):
    """Score for a single C dimension."""
    dimension: str
    score: float = 0.0  # 0-100
    weight: float = 0.0
    weighted_score: float = 0.0
    grade: Literal["A", "B", "C", "D", "F"] = "F"
    findings: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    mitigants: list[str] = Field(default_factory=list)


class FiveCsAssessment(BaseModel):
    """Complete 5 Cs credit assessment."""
    project_name: str
    character: CScore = Field(default_factory=lambda: CScore(dimension="Character"))
    capacity: CScore = Field(default_factory=lambda: CScore(dimension="Capacity"))
    capital: CScore = Field(default_factory=lambda: CScore(dimension="Capital"))
    collateral: CScore = Field(default_factory=lambda: CScore(dimension="Collateral"))
    conditions: CScore = Field(default_factory=lambda: CScore(dimension="Conditions"))

    composite_score: float = 0.0
    composite_grade: Literal["A", "B", "C", "D", "F"] = "F"
    recommendation: Literal[
        "strong_approve", "approve", "conditional_approve",
        "additional_review", "decline",
    ] = "additional_review"
    key_strengths: list[str] = Field(default_factory=list)
    key_risks: list[str] = Field(default_factory=list)
    conditions_for_approval: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Bond Sizing
# ---------------------------------------------------------------------------

class DebtServiceYear(BaseModel):
    """Single year of projected debt service."""
    year: int
    principal: float = 0.0
    interest: float = 0.0
    total: float = 0.0
    net_revenue: float = 0.0
    dscr: float = 0.0


class BondSizingResult(BaseModel):
    """Output of bond sizing calculation."""
    max_par_amount: float = 0.0
    recommended_par: float = 0.0  # After safety margin
    coupon_rate: float = 0.0
    yield_to_maturity: float | None = None
    maturity_years: float = 30.0
    annual_debt_service: float = 0.0
    max_annual_debt_service: float = 0.0

    # Coverage metrics
    min_dscr: float = 0.0
    avg_dscr: float = 0.0
    target_dscr: float = 1.25
    dscr_cushion_pct: float = 0.0  # How much above target

    # Debt service schedule
    schedule: list[DebtServiceYear] = Field(default_factory=list)

    # Sensitivity
    par_at_dscr_1_20: float = 0.0
    par_at_dscr_1_30: float = 0.0
    par_at_dscr_1_40: float = 0.0
    par_at_dscr_1_50: float = 0.0

    # Sources & Uses
    total_sources: float = 0.0
    total_uses: float = 0.0
    project_fund: float = 0.0
    debt_service_reserve: float = 0.0
    costs_of_issuance: float = 0.0
    underwriter_discount: float = 0.0

    sizing_notes: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# 3-Statement Model
# ---------------------------------------------------------------------------

class IncomeStatementYear(BaseModel):
    year: int
    gross_revenue: float = 0.0
    operating_expenses: float = 0.0
    ebitda: float = 0.0
    depreciation: float = 0.0
    interest_expense: float = 0.0
    net_income: float = 0.0
    operating_margin: float = 0.0
    net_margin: float = 0.0


class BalanceSheetYear(BaseModel):
    year: int
    total_assets: float = 0.0
    current_assets: float = 0.0
    fixed_assets: float = 0.0
    total_liabilities: float = 0.0
    current_liabilities: float = 0.0
    long_term_debt: float = 0.0
    total_equity: float = 0.0
    current_ratio: float = 0.0
    leverage_ratio: float = 0.0


class CashFlowYear(BaseModel):
    year: int
    net_income: float = 0.0
    depreciation: float = 0.0
    operating_cash_flow: float = 0.0
    capital_expenditures: float = 0.0
    debt_service_principal: float = 0.0
    debt_service_interest: float = 0.0
    free_cash_flow: float = 0.0
    dscr: float = 0.0
    cash_balance: float = 0.0


class ThreeStatementModel(BaseModel):
    """Pro forma 3-statement financial model."""
    project_name: str
    projection_years: int = 10
    income_statements: list[IncomeStatementYear] = Field(default_factory=list)
    balance_sheets: list[BalanceSheetYear] = Field(default_factory=list)
    cash_flows: list[CashFlowYear] = Field(default_factory=list)
    assumptions: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Deal Structure
# ---------------------------------------------------------------------------

class CovenantPackage(BaseModel):
    """Recommended covenant structure."""
    rate_covenant_type: Literal["rate", "coverage", "rate_and_coverage"] | None = None
    minimum_coverage_ratio: float | None = None
    additional_bonds_test_historical: float | None = None
    additional_bonds_test_projected: float | None = None
    dsrf_type: Literal[
        "maximum_annual_debt_service", "average_annual_debt_service",
        "percent_of_par", "lesser_of_three_prong",
    ] | None = None
    dsrf_amount: float | None = None
    operating_reserve_months: int | None = None
    renewal_replacement_fund: float | None = None
    consultant_rate_study_required: bool = False
    flow_of_funds: Literal["gross_pledge", "net_pledge"] | None = None
    rationale: list[str] = Field(default_factory=list)


class SecurityPackageRecommendation(BaseModel):
    """Recommended security package."""
    pledge_type: str | None = None
    lien_position: str | None = None
    real_property_mortgage: bool = False
    equipment_security_interest: bool = False
    offtake_assignment: bool = False
    insurance_requirements: list[str] = Field(default_factory=list)
    credit_enhancement_needed: bool = False
    enhancement_type: str | None = None
    rationale: list[str] = Field(default_factory=list)


class DealStructure(BaseModel):
    """Complete recommended deal structure."""
    project_name: str
    bond_type: str = "revenue"
    tax_status: str = "tax_exempt"
    par_amount: float = 0.0
    coupon_rate: float = 0.0
    maturity_years: float = 30.0
    maturity_type: Literal["serial", "term", "serial_and_term"] = "serial_and_term"

    # Call provisions
    optional_redemption_date: str | None = None  # Typically 10yr par call
    optional_redemption_price: float = 100.0
    make_whole_call: bool = False
    extraordinary_redemption: bool = False

    # Covenants & Security
    covenants: CovenantPackage = Field(default_factory=CovenantPackage)
    security: SecurityPackageRecommendation = Field(default_factory=SecurityPackageRecommendation)

    # Credit enhancement (from Bank Analyzer)
    credit_enhancement_recommended: bool = False
    enhancement_type: str | None = None
    estimated_enhancement_cost_bps: float | None = None

    # Pricing guidance
    estimated_spread_bps: float | None = None
    estimated_yield: float | None = None
    comparable_deals: list[str] = Field(default_factory=list)

    structuring_notes: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Complete Analysis Result
# ---------------------------------------------------------------------------

class CreditAnalysisResult(BaseModel):
    """Full credit analysis pipeline output."""
    project_name: str
    analysis_timestamp: datetime | None = None

    # Pipeline outputs
    five_cs: FiveCsAssessment | None = None
    financial_model: ThreeStatementModel | None = None
    bond_sizing: BondSizingResult | None = None
    deal_structure: DealStructure | None = None

    # Standard Model positioning (filled by capstone integration)
    projected_f_score: float | None = None  # Fundamental score
    projected_s_omega: float | None = None  # Risk-adjusted return
    corpus_cri_percentile: float | None = None  # Where it ranks vs corpus
    sic_efficiency: float | None = None

    # Overall
    credit_opinion: Literal[
        "investment_grade", "crossover", "high_yield", "not_rated_strong",
        "not_rated_adequate", "not_rated_weak",
    ] | None = None
    recommended_rating: str | None = None
    executive_summary: str | None = None
