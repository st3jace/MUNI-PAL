from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Carbon Credit Programs
# ---------------------------------------------------------------------------

class CarbonCreditProgram(BaseModel):
    """A carbon credit, offset, or emissions trading program tied to the project."""
    program_type: Literal[
        "compliance", "voluntary", "cap_and_trade", "offset",
    ] | None = None
    registry: str | None = None  # e.g. "California ARB", "Verra", "Gold Standard"
    credit_type: str | None = None  # e.g. "CERs", "VERs", "ARB offsets", "RECs"
    estimated_annual_credits: Decimal | None = None
    price_per_credit: Decimal | None = None
    price_floor: Decimal | None = None
    price_escalator_pct: Decimal | None = None
    contract_term_years: int | None = None
    counterparty: str | None = None
    assigned_as_security: bool = False
    revenue_share_pct: Decimal | None = None


# ---------------------------------------------------------------------------
# Tipping Fee Structures
# ---------------------------------------------------------------------------

class TippingFeeStructure(BaseModel):
    """A tipping fee, disposal fee, or gate rate arrangement."""
    fee_type: Literal[
        "per_ton", "per_cubic_yard", "flat_annual", "tiered",
    ] | None = None
    current_rate: Decimal | None = None  # $/ton or $/cubic yard
    rate_escalator_type: Literal[
        "cpi", "fixed_pct", "contractual", "market",
    ] | None = None
    rate_escalator_pct: Decimal | None = None
    minimum_annual_tonnage: Decimal | None = None  # put-or-pay floor
    guaranteed_annual_revenue: Decimal | None = None
    contract_term_years: int | None = None
    contract_expiry_date: date | None = None
    counterparties: list[str] = Field(default_factory=list)
    put_or_pay: bool = False
    flow_control_ordinance: bool = False


# ---------------------------------------------------------------------------
# Electricity PPAs
# ---------------------------------------------------------------------------

class ElectricityPPA(BaseModel):
    """A power purchase agreement or electricity sale contract."""
    counterparty: str | None = None
    counterparty_credit_rating: str | None = None
    contract_term_years: int | None = None
    contract_start_date: date | None = None
    contract_expiry_date: date | None = None
    price_per_kwh: Decimal | None = None
    price_per_mwh: Decimal | None = None
    price_escalator_type: Literal[
        "cpi", "fixed_pct", "market_indexed", "none",
    ] | None = None
    price_escalator_pct: Decimal | None = None
    capacity_mw: Decimal | None = None
    estimated_annual_generation_mwh: Decimal | None = None
    minimum_delivery_obligation_mwh: Decimal | None = None
    curtailment_provisions: bool = False
    dispatch_priority: Literal[
        "must_take", "baseload", "dispatchable", "as_available",
    ] | None = None
    assigned_as_security: bool = False


# ---------------------------------------------------------------------------
# General Offtake Agreements
# ---------------------------------------------------------------------------

class OfftakeAgreement(BaseModel):
    """An offtake or output sale agreement for non-electricity products."""
    product_type: Literal[
        "steam", "processed_materials", "compost", "recyclables",
        "metals", "ash", "biogas", "rng", "hydrogen", "water",
        "chemicals", "aggregate", "other",
    ] | None = None
    counterparty: str | None = None
    counterparty_credit_rating: str | None = None
    contract_term_years: int | None = None
    contract_expiry_date: date | None = None
    pricing_mechanism: Literal[
        "fixed", "market_indexed", "formula", "negotiated",
    ] | None = None
    minimum_purchase_obligation: Decimal | None = None
    estimated_annual_revenue: Decimal | None = None
    assigned_as_security: bool = False
    take_or_pay: bool = False


# ---------------------------------------------------------------------------
# Top-Level Revenue Stream Profile
# ---------------------------------------------------------------------------

class RevenueStreamProfile(BaseModel):
    """Aggregated revenue stream data extracted from an Official Statement."""
    carbon_credits: list[CarbonCreditProgram] = Field(default_factory=list)
    tipping_fees: list[TippingFeeStructure] = Field(default_factory=list)
    electricity_ppas: list[ElectricityPPA] = Field(default_factory=list)
    offtake_agreements: list[OfftakeAgreement] = Field(default_factory=list)

    # Summary fields
    total_contracted_revenue_pct: Decimal | None = None
    revenue_concentration_risk: Literal["low", "moderate", "high"] | None = None
    shortest_contract_expiry: date | None = None
    has_put_or_pay: bool = False
    has_flow_control: bool = False
    has_take_or_pay: bool = False
