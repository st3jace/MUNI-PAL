from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from .deal_identity import DealIdentity
from .deal_structure import DealStructure, MaturitySchedule
from .security import SecurityPackage
from .financials import (
    DebtServiceSchedule,
    HistoricalFinancials,
    ProjectedFinancials,
    SourcesAndUses,
)
from .additional import (
    ContinuingDisclosureProfile,
    DemographicContext,
    FlowOfFunds,
    LegalProvisions,
    RatingProfile,
    RefundingInfo,
    RiskFactorProfile,
    UnderwritingTerms,
)
from .revenue_streams import RevenueStreamProfile


class ReviewFlag(BaseModel):
    field_path: str
    issue: str
    confidence: float = 0.0
    suggested_value: Any = None
    alternative_value: Any = None


class DealRecord(BaseModel):
    # Metadata
    extraction_id: str = ""
    source_file: str = ""
    source_hash: str = ""
    extraction_timestamp: datetime | None = None
    extraction_version: str = "0.1.0"
    completeness_score: float = 0.0
    confidence_scores: dict[str, float] = Field(default_factory=dict)

    # Extracted content
    identity: DealIdentity = Field(default_factory=DealIdentity)
    structure: DealStructure = Field(default_factory=DealStructure)
    maturity_schedule: MaturitySchedule | None = None
    security: SecurityPackage | None = None
    financials_historical: HistoricalFinancials | None = None
    financials_projected: ProjectedFinancials | None = None
    debt_service: DebtServiceSchedule | None = None
    risk_factors: RiskFactorProfile | None = None
    sources_uses: SourcesAndUses | None = None
    flow_of_funds: FlowOfFunds | None = None
    legal_provisions: LegalProvisions | None = None
    continuing_disclosure: ContinuingDisclosureProfile | None = None
    ratings: RatingProfile | None = None
    demographics: DemographicContext | None = None
    refunding: RefundingInfo | None = None
    underwriting: UnderwritingTerms | None = None
    revenue_streams: RevenueStreamProfile | None = None

    # Fields needing human review
    review_flags: list[ReviewFlag] = Field(default_factory=list)

    # Classification (filled by classifier)
    primary_classification: str | None = None
    secondary_classification: str | None = None
    tertiary_classification: str | None = None
    size_classification: str | None = None

    def compute_completeness(self) -> float:
        """Calculate what percentage of key fields are populated."""
        key_fields = [
            self.identity.issuer_name,
            self.identity.cusip_base,
            self.identity.document_type,
            self.structure.par_amount,
            self.structure.bond_type,
            self.structure.tax_status,
            self.structure.interest_type,
            self.structure.final_maturity_date,
            self.maturity_schedule,
            self.security,
            self.debt_service,
            self.sources_uses,
            self.ratings,
        ]
        populated = sum(1 for f in key_fields if f is not None)
        score = populated / len(key_fields) if key_fields else 0.0
        self.completeness_score = round(score, 3)
        return self.completeness_score
