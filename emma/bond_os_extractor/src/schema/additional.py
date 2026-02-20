from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Risk Factors
# ---------------------------------------------------------------------------

class RiskFactor(BaseModel):
    category: Literal[
        "construction", "technology", "market_demand", "regulatory",
        "environmental", "competition", "management", "financial",
        "interest_rate", "tax_law", "force_majeure", "political",
        "feedstock_supply", "offtake_counterparty", "permitting",
        "litigation", "labor", "insurance", "cybersecurity",
        "climate", "pandemic",
    ] | None = None
    title: str = ""
    description: str = ""
    severity_implied: Literal["boilerplate", "material", "significant"] | None = None
    mitigation_described: bool = False
    mitigation_text: str | None = None


class RiskFactorProfile(BaseModel):
    risks: list[RiskFactor] = Field(default_factory=list)
    total_risk_factors_count: int = 0
    unique_categories: list[str] = Field(default_factory=list)
    has_project_specific_risks: bool = False
    has_technology_risk: bool = False
    has_construction_risk: bool = False
    has_environmental_compliance_risk: bool = False


# ---------------------------------------------------------------------------
# Continuing Disclosure
# ---------------------------------------------------------------------------

class ContinuingDisclosureProfile(BaseModel):
    annual_filing_required: bool = False
    annual_filing_contents: list[str] = Field(default_factory=list)
    material_event_notices: bool = False
    emma_filing_commitment: bool = False
    prior_compliance_history: str | None = None


# ---------------------------------------------------------------------------
# Ratings
# ---------------------------------------------------------------------------

class Rating(BaseModel):
    agency: Literal["moodys", "sp", "fitch", "kroll"] | None = None
    rating: str = ""
    outlook: str | None = None


class RatingProfile(BaseModel):
    ratings: list[Rating] = Field(default_factory=list)
    underlying_rating: str | None = None
    enhanced_rating: str | None = None
    outlook: str | None = None


# ---------------------------------------------------------------------------
# Flow of Funds
# ---------------------------------------------------------------------------

class WaterfallStep(BaseModel):
    priority: int = 0
    fund_name: str = ""
    description: str = ""
    amount_or_formula: str = ""


class FlowOfFunds(BaseModel):
    waterfall_steps: list[WaterfallStep] = Field(default_factory=list)
    trapped_cash_provisions: bool = False
    sweep_to_equity_permitted: bool = False


# ---------------------------------------------------------------------------
# Legal Provisions
# ---------------------------------------------------------------------------

class LegalProvisions(BaseModel):
    governing_law_state: str | None = None
    events_of_default: list[str] = Field(default_factory=list)
    remedies_upon_default: list[str] = Field(default_factory=list)
    bondholders_rights: str | None = None
    amendment_provisions: str | None = None
    defeasance_permitted: bool = False
    defeasance_type: Literal[
        "legal", "economic", "crossover", "not_permitted",
    ] | None = None


# ---------------------------------------------------------------------------
# Demographics
# ---------------------------------------------------------------------------

class DemographicContext(BaseModel):
    population: int | None = None
    median_household_income: Decimal | None = None
    unemployment_rate: Decimal | None = None
    top_taxpayers: list[str] | None = None
    top_employers: list[str] | None = None
    assessed_valuation: Decimal | None = None


# ---------------------------------------------------------------------------
# Refunding
# ---------------------------------------------------------------------------

class RefundingInfo(BaseModel):
    is_refunding: bool = False
    refunding_type: Literal[
        "advance_refunding", "current_refunding",
        "crossover_refunding", "none",
    ] | None = None
    refunded_bonds_series: list[str] = Field(default_factory=list)
    refunded_bonds_original_par: Decimal | None = None
    present_value_savings: Decimal | None = None
    savings_as_percentage: Decimal | None = None
    negative_arbitrage: Decimal | None = None


# ---------------------------------------------------------------------------
# Underwriting Terms
# ---------------------------------------------------------------------------

class UnderwritingTerms(BaseModel):
    sale_type: Literal[
        "competitive", "negotiated", "private_placement",
    ] | None = None
    underwriter_discount_per_bond: Decimal | None = None
    management_fee: Decimal | None = None
    takedown: Decimal | None = None
    total_spread: Decimal | None = None
    reoffering_yields: list[Decimal] | None = None
