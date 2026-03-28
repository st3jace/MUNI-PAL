"""
Revenue diversification visualization contracts.

These schemas back the Muni-Pal visualization capability for comparing
current-state revenue concentration against diversified scenario mixes.
"""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import Field

from munipal.core.schemas.base import BaseSchema


class RevenueStabilityClass(str, Enum):
    """Revenue-stream stability posture used for rendering and legend grouping."""

    STABLE = "stable"
    BALANCED = "balanced"
    VOLATILE = "volatile"


class RevenueScenarioSafety(str, Enum):
    """High-level scenario safety classification."""

    FRAGILE = "fragile"
    SAFE = "safe"
    FORTRESS = "fortress"


class RevenueStreamDefinition(BaseSchema):
    """Platform registry entry for one revenue stream."""

    stream_id: str = Field(..., min_length=1)
    label: str = Field(..., min_length=1)
    color: str = Field(..., min_length=4)
    stability_class: RevenueStabilityClass
    description: str = Field(..., min_length=1)


class RevenueStreamSlice(BaseSchema):
    """One revenue stream within a scenario mix."""

    stream_id: str = Field(..., min_length=1)
    label: str = Field(..., min_length=1)
    amount: float = Field(..., ge=0.0)
    pct_of_total: float = Field(..., ge=0.0, le=1.0)
    color: str = Field(..., min_length=4)
    stability_class: RevenueStabilityClass
    is_inferred: bool = False
    source_path: str | None = None


class RevenueScenarioMix(BaseSchema):
    """Scenario payload for the diversification comparison chart."""

    scenario_id: str = Field(..., min_length=1)
    label: str = Field(..., min_length=1)
    total_revenue: float = Field(..., ge=0.0)
    revenue_streams: list[RevenueStreamSlice] = Field(default_factory=list)
    dscr_mean: float = Field(..., ge=0.0)
    dscr_minimum: float = Field(..., ge=0.0)
    breach_weeks: int = Field(..., ge=0)
    implied_rating: str = Field(..., min_length=1)
    breakeven_diesel_price: float = Field(..., ge=0.0)
    dscr_parity_diesel_price: float | None = Field(default=None, ge=0.0)
    covenant_trigger_diesel_price: float = Field(..., ge=0.0)
    safety_status: RevenueScenarioSafety
    safety_label: str = Field(..., min_length=1)
    assumptions: list[str] = Field(default_factory=list)


class RevenueRiskProofMetric(BaseSchema):
    """One packet-sourced proof metric comparing baseline and diversified cases."""

    metric_id: str = Field(..., min_length=1)
    label: str = Field(..., min_length=1)
    baseline_value: str = Field(..., min_length=1)
    diversified_value: str = Field(..., min_length=1)
    delta_label: str = Field(..., min_length=1)


class RevenueDiversificationRiskProof(BaseSchema):
    """Packet-level proof that diversification changes the risk profile."""

    title: str = Field(..., min_length=1)
    baseline_label: str = Field(..., min_length=1)
    diversified_label: str = Field(..., min_length=1)
    takeaway: str = Field(..., min_length=1)
    metrics: list[RevenueRiskProofMetric] = Field(default_factory=list)


class RevenueDiversificationVisualizationResponse(BaseSchema):
    """Versioned visualization contract for revenue diversification rendering."""

    contract_version: str = "revenue-diversification-v1"
    generated_at: datetime
    project_id: UUID
    project_name: str = Field(..., min_length=1)
    debt_service_annual: float = Field(..., ge=0.0)
    covenant_trigger_dscr: float = Field(..., ge=0.0)
    non_diesel_combined_coverage_dscr: float | None = Field(default=None, ge=0.0)
    non_diesel_senior_coverage_dscr: float | None = Field(default=None, ge=0.0)
    stream_definitions: list[RevenueStreamDefinition] = Field(default_factory=list)
    revenue_scenarios: list[RevenueScenarioMix] = Field(default_factory=list)
    risk_proof: RevenueDiversificationRiskProof | None = None
    data_quality_notes: list[str] = Field(default_factory=list)
