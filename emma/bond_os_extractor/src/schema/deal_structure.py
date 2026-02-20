from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class SLBKpi(BaseModel):
    kpi_name: str
    kpi_description: str | None = None
    target_value: str | None = None
    measurement_date: date | None = None
    verification_method: str | None = None


class MaturityRow(BaseModel):
    maturity_date: date | None = None
    par_amount: Decimal | None = None
    coupon_rate: Decimal | None = None
    yield_to_maturity: Decimal | None = None
    price: Decimal | None = None
    cusip: str | None = None
    serial_or_term: Literal["serial", "term"] | None = None
    accreted_value: Decimal | None = None
    original_issue_discount: bool = False
    original_issue_premium: bool = False


class MaturitySchedule(BaseModel):
    rows: list[MaturityRow] = Field(default_factory=list)
    total_par: Decimal | None = None
    true_interest_cost: Decimal | None = None
    net_interest_cost: Decimal | None = None
    all_in_tic: Decimal | None = None
    average_coupon: Decimal | None = None
    average_life: Decimal | None = None


class DealStructure(BaseModel):
    # Par amount and denomination
    par_amount: Decimal | None = None
    denomination: Decimal | None = None
    authorized_amount: Decimal | None = None

    # Bond type classification
    bond_type: Literal[
        "general_obligation", "revenue", "conduit_revenue",
        "special_assessment", "tax_increment", "moral_obligation",
        "double_barrel", "lease_revenue", "certificates_of_participation",
        "industrial_development", "private_activity", "qualified_501c3",
    ] | None = None

    tax_status: Literal[
        "tax_exempt", "taxable", "alternative_minimum_tax",
        "bank_qualified", "federally_taxable_state_exempt",
    ] | None = None

    # Interest structure
    interest_type: Literal[
        "fixed_rate", "variable_rate", "capital_appreciation",
        "convertible_cab", "zero_coupon", "stepped_coupon",
        "index_linked", "auction_rate",
    ] | None = None

    # CAB-specific
    cab_enabled: bool = False
    cab_accretion_rate: Decimal | None = None
    cab_accretion_frequency: str | None = None
    cab_accretion_period_years: int | None = None
    cab_conversion_date: date | None = None
    cab_maturity_value: Decimal | None = None
    cab_original_issue_price: Decimal | None = None

    # Sustainability / ESG features
    slb_enabled: bool = False
    green_bond: bool = False
    social_bond: bool = False
    sustainability_bond: bool = False
    slb_kpis: list[SLBKpi] = Field(default_factory=list)
    slb_step_up_bps: Decimal | None = None
    slb_step_down_bps: Decimal | None = None
    slb_observation_dates: list[date] = Field(default_factory=list)
    slb_verification_agent: str | None = None
    slb_second_party_opinion: str | None = None

    # Maturity structure
    maturity_type: Literal[
        "serial", "term", "serial_and_term", "bullet",
        "capital_appreciation", "convertible",
    ] | None = None
    final_maturity_date: date | None = None
    weighted_average_maturity: Decimal | None = None

    # Call provisions
    optional_redemption_date: date | None = None
    optional_redemption_price: Decimal | None = None
    make_whole_call: bool = False
    extraordinary_redemption: bool = False
    mandatory_sinking_fund: bool = False
    turbo_redemption: bool = False

    # Credit enhancement
    credit_enhancement_type: Literal[
        "none", "bond_insurance", "letter_of_credit",
        "standby_purchase_agreement", "state_enhancement",
        "moral_obligation", "federal_guarantee",
    ] | None = None
    credit_enhancer_name: str | None = None
    insurer_rating: str | None = None
