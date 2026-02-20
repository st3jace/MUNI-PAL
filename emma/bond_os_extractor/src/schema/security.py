from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class RateCovenant(BaseModel):
    covenant_type: Literal["rate", "coverage", "rate_and_coverage"] | None = None
    minimum_coverage_ratio: Decimal | None = None
    coverage_calculation_basis: str | None = None
    additional_revenue_test: Decimal | None = None
    consultant_rate_study_required: bool = False
    cure_period_days: int | None = None


class AdditionalBondsTest(BaseModel):
    historical_coverage_required: Decimal | None = None
    projected_coverage_required: Decimal | None = None
    lookback_period_years: int | None = None
    projection_period_years: int | None = None
    consultant_certification_required: bool = False


class DebtServiceReserve(BaseModel):
    requirement_type: Literal[
        "maximum_annual_debt_service", "average_annual_debt_service",
        "percent_of_par", "fixed_amount", "lesser_of_three_prong",
    ] | None = None
    amount: Decimal | None = None
    funded_at_closing: bool = False
    surety_bond_permitted: bool = False


class SecurityPackage(BaseModel):
    # Revenue pledge
    pledge_type: Literal[
        "gross_revenue", "net_revenue", "specific_revenue", "none",
    ] | None = None
    pledged_revenues_description: str | None = None

    # Lien position
    lien_position: Literal[
        "first", "second", "pari_passu", "subordinate",
    ] | None = None
    senior_debt_outstanding: Decimal | None = None

    # Real property security
    real_property_mortgage: bool = False
    real_property_description: str | None = None

    # Equipment / personal property
    equipment_security_interest: bool = False
    equipment_description: str | None = None

    # Revenue-specific pledges
    offtake_agreements_assigned: bool = False
    offtake_counterparties: list[str] = Field(default_factory=list)

    # Financial covenants
    rate_covenant: RateCovenant | None = None
    additional_bonds_test: AdditionalBondsTest | None = None

    # Reserve requirements
    debt_service_reserve_fund: DebtServiceReserve | None = None
    operating_reserve: Decimal | None = None
    renewal_replacement_fund: Decimal | None = None

    # Insurance requirements
    required_insurance_types: list[str] = Field(default_factory=list)
    minimum_coverage_amount: Decimal | None = None
