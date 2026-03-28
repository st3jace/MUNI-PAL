"""Bank Analyzer data models and scoring schemas."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# PCA (Prompt Corrective Action) Categories
# ---------------------------------------------------------------------------

PCACategory = Literal[
    "well_capitalized",
    "adequately_capitalized",
    "undercapitalized",
    "significantly_undercapitalized",
    "critically_undercapitalized",
]

PCA_THRESHOLDS = {
    "well_capitalized": {
        "total_rbc": 0.10,
        "tier1_rbc": 0.08,
        "cet1": 0.065,
        "tier1_leverage": 0.05,
    },
    "adequately_capitalized": {
        "total_rbc": 0.08,
        "tier1_rbc": 0.06,
        "cet1": 0.045,
        "tier1_leverage": 0.04,
    },
    "undercapitalized": {
        "total_rbc": 0.08,
        "tier1_rbc": 0.06,
        "cet1": 0.045,
        "tier1_leverage": 0.04,
    },
    "significantly_undercapitalized": {
        "total_rbc": 0.06,
        "tier1_rbc": 0.04,
        "cet1": 0.03,
        "tier1_leverage": 0.03,
    },
}

TANGIBLE_EQUITY_CRITICAL_THRESHOLD = 0.02


# ---------------------------------------------------------------------------
# Loan Portfolio Segment
# ---------------------------------------------------------------------------

class LoanSegment(BaseModel):
    """Granular loan portfolio segment with delinquency breakdown."""
    segment_name: str
    portfolio_balance: float = 0.0
    delinquent_30_89: float = 0.0
    delinquent_90_plus: float = 0.0
    nonaccrual: float = 0.0
    charge_offs: float = 0.0
    npl_ratio: float = 0.0
    reo: float = 0.0  # Real estate owned (foreclosed assets)

    @property
    def total_distressed(self) -> float:
        return self.delinquent_90_plus + self.nonaccrual

    @property
    def distress_ratio(self) -> float:
        if self.portfolio_balance <= 0:
            return 0.0
        return self.total_distressed / self.portfolio_balance


# ---------------------------------------------------------------------------
# Bank Profile (ingested from Call Report data)
# ---------------------------------------------------------------------------

class BankProfile(BaseModel):
    """Complete bank profile from FFIEC Call Report data."""

    # Identity
    bank_name: str
    id_rssd: int
    fdic_cert: int | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    website: str | None = None

    # Capital
    total_assets: float = 0.0
    risk_based_capital_ratio: float | None = None
    tier1_leverage_ratio: float | None = None
    tier1_rbc_ratio: float | None = None
    allowance_loan_losses: float = 0.0
    provision_loan_losses: float = 0.0

    # Loan portfolios
    residential_first: LoanSegment | None = None
    residential_junior: LoanSegment | None = None
    heloc: LoanSegment | None = None
    commercial_non_owner: LoanSegment | None = None
    commercial_owner: LoanSegment | None = None
    multifamily: LoanSegment | None = None
    construction_residential: LoanSegment | None = None
    construction_commercial: LoanSegment | None = None
    farmland: LoanSegment | None = None
    ci: LoanSegment | None = None  # Commercial & Industrial
    credit_cards: LoanSegment | None = None
    auto_loans: LoanSegment | None = None

    # Mortgage banking
    loans_held_for_sale: float = 0.0
    held_for_sale_nonaccrual: float = 0.0
    mortgage_first_liens_hfs: float = 0.0
    mortgages_sold_quarter: float = 0.0

    # Metadata
    data_date: date | None = None
    ingestion_timestamp: datetime | None = None

    @property
    def pca_category(self) -> PCACategory:
        """Determine PCA category from capital ratios."""
        rbc = self.risk_based_capital_ratio or 0.0
        t1_rbc = self.tier1_rbc_ratio or 0.0
        t1_lev = self.tier1_leverage_ratio or 0.0

        # Well capitalized: ALL thresholds met
        wc = PCA_THRESHOLDS["well_capitalized"]
        if rbc >= wc["total_rbc"] and t1_rbc >= wc["tier1_rbc"] and t1_lev >= wc["tier1_leverage"]:
            return "well_capitalized"

        # Adequately capitalized
        ac = PCA_THRESHOLDS["adequately_capitalized"]
        if rbc >= ac["total_rbc"] and t1_rbc >= ac["tier1_rbc"] and t1_lev >= ac["tier1_leverage"]:
            return "adequately_capitalized"

        # Significantly undercapitalized
        su = PCA_THRESHOLDS["significantly_undercapitalized"]
        if rbc < su["total_rbc"] or t1_rbc < su["tier1_rbc"] or t1_lev < su["tier1_leverage"]:
            return "significantly_undercapitalized"

        return "undercapitalized"

    @property
    def total_cre_portfolio(self) -> float:
        """Total commercial real estate exposure."""
        total = 0.0
        for seg in [self.commercial_non_owner, self.commercial_owner,
                     self.multifamily, self.construction_residential,
                     self.construction_commercial]:
            if seg:
                total += seg.portfolio_balance
        return total

    @property
    def total_cre_npl(self) -> float:
        """Total CRE non-performing loans."""
        total = 0.0
        for seg in [self.commercial_non_owner, self.commercial_owner,
                     self.multifamily, self.construction_residential,
                     self.construction_commercial]:
            if seg:
                total += seg.total_distressed
        return total

    @property
    def cre_concentration_ratio(self) -> float:
        """CRE as % of total assets."""
        if self.total_assets <= 0:
            return 0.0
        return self.total_cre_portfolio / self.total_assets

    def all_segments(self) -> list[LoanSegment]:
        """Return all non-None loan segments."""
        segments = []
        for attr in [
            "residential_first", "residential_junior", "heloc",
            "commercial_non_owner", "commercial_owner", "multifamily",
            "construction_residential", "construction_commercial",
            "farmland", "ci", "credit_cards", "auto_loans",
        ]:
            seg = getattr(self, attr)
            if seg is not None:
                segments.append(seg)
        return segments


# ---------------------------------------------------------------------------
# Scoring Results
# ---------------------------------------------------------------------------

class CREDistressScore(BaseModel):
    """CRE distress analysis for workout/restructuring opportunities."""
    score: float = 0.0  # 0-100 (higher = more distressed = more opportunity)
    cre_npl_ratio: float = 0.0
    cre_concentration_pct: float = 0.0
    commercial_non_owner_npl: float = 0.0
    multifamily_npl: float = 0.0
    construction_npl: float = 0.0
    total_reo: float = 0.0
    reo_to_assets_pct: float = 0.0
    charge_off_trend: Literal["improving", "stable", "deteriorating"] | None = None
    distress_segments: list[str] = Field(default_factory=list)  # Which segments are distressed
    opportunity_type: Literal[
        "workout_advisory", "asset_acquisition", "credit_restructuring", "none",
    ] = "none"


class CreditEnhancementScore(BaseModel):
    """Capacity to provide credit enhancement (LOC, SBPA, bond insurance)."""
    score: float = 0.0  # 0-100 (higher = more capacity)
    pca_category: PCACategory = "well_capitalized"
    excess_capital_pct: float = 0.0  # Capital above well-capitalized thresholds
    total_rbc_ratio: float = 0.0
    tier1_leverage: float = 0.0
    asset_size_tier: Literal["community", "regional", "super_regional", "money_center"] = "community"
    enhancement_types: list[str] = Field(default_factory=list)  # LOC, SBPA, insurance
    max_enhancement_estimate: float = 0.0  # Rough $ capacity


class DirectPurchaseScore(BaseModel):
    """Appetite for direct municipal bond purchase."""
    score: float = 0.0  # 0-100 (higher = better fit)
    asset_size_tier: str = "community"
    liquidity_ratio: float = 0.0  # Loans HFS + cash / total assets
    tax_position_indicator: Literal["strong", "moderate", "weak"] | None = None
    bank_qualified_eligible: bool = False  # Community banks < $10B
    municipal_appetite_signals: list[str] = Field(default_factory=list)


class GreenFinanceScore(BaseModel):
    """ESG/carbon credit project finance capability."""
    score: float = 0.0  # 0-100 (higher = more capable)
    has_carbon_deals: bool = False
    carbon_deal_volume: float = 0.0
    carbon_deal_types: list[str] = Field(default_factory=list)
    esg_commitment_level: Literal["leader", "active", "emerging", "minimal", "retreating"] = "minimal"
    green_bond_experience: bool = False
    sustainability_linked_lending: bool = False
    net_zero_commitment: bool = False


class BankScorecard(BaseModel):
    """Complete scorecard for a bank across all dimensions."""
    bank_name: str
    id_rssd: int
    state: str | None = None
    total_assets: float = 0.0
    pca_category: PCACategory = "well_capitalized"

    cre_distress: CREDistressScore = Field(default_factory=CREDistressScore)
    credit_enhancement: CreditEnhancementScore = Field(default_factory=CreditEnhancementScore)
    direct_purchase: DirectPurchaseScore = Field(default_factory=DirectPurchaseScore)
    green_finance: GreenFinanceScore = Field(default_factory=GreenFinanceScore)

    composite_score: float = 0.0  # Weighted composite
    ranking: int = 0

    @property
    def asset_tier(self) -> str:
        if self.total_assets >= 250e9:
            return "money_center"
        if self.total_assets >= 50e9:
            return "super_regional"
        if self.total_assets >= 10e9:
            return "regional"
        return "community"


# ---------------------------------------------------------------------------
# Deal Match
# ---------------------------------------------------------------------------

class DealMatchRequest(BaseModel):
    """Parameters for matching banks to a specific deal."""
    deal_type: Literal[
        "revenue_bond", "go_bond", "conduit", "private_placement",
        "credit_enhancement", "green_bond", "project_finance",
    ]
    deal_size: float  # USD
    state: str | None = None
    sector: str | None = None  # waste, healthcare, energy, etc.
    needs_credit_enhancement: bool = False
    enhancement_type: Literal["loc", "sbpa", "bond_insurance"] | None = None
    is_green: bool = False
    is_carbon_credit: bool = False
    bank_qualified: bool = False  # < $10M par for community bank tax benefit
    min_bank_assets: float | None = None
    max_bank_assets: float | None = None


class BankMatch(BaseModel):
    """A scored match between a bank and a deal."""
    bank_name: str
    id_rssd: int
    state: str | None = None
    total_assets: float = 0.0
    match_score: float = 0.0  # 0-100
    match_reasons: list[str] = Field(default_factory=list)
    concerns: list[str] = Field(default_factory=list)
    recommended_role: Literal[
        "lead_underwriter", "co_manager", "credit_enhancer",
        "direct_purchaser", "syndicate_member", "advisor",
    ] | None = None


class DealMatchResult(BaseModel):
    """Results of matching banks to a deal."""
    deal: DealMatchRequest
    matches: list[BankMatch] = Field(default_factory=list)
    total_banks_screened: int = 0
    timestamp: datetime | None = None
