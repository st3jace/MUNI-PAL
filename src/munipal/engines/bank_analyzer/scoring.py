"""Bank Analyzer scoring models.

Four scoring dimensions that evaluate banks for different deal opportunities:
  1. CRE Distress — identifies troubled real estate for workout advisory
  2. Credit Enhancement — capacity to provide LOC/SBPA for municipal bonds
  3. Direct Purchase — appetite for bank-qualified bond purchases
  4. Green Finance — ESG/carbon credit project finance capability
"""

from __future__ import annotations

import logging
from typing import Any

from .models import (
    BankProfile,
    BankScorecard,
    CREDistressScore,
    CreditEnhancementScore,
    DirectPurchaseScore,
    GreenFinanceScore,
    PCA_THRESHOLDS,
)

logger = logging.getLogger("bank_analyzer.scoring")


# ---------------------------------------------------------------------------
# CRE distress thresholds
# ---------------------------------------------------------------------------

# NPL ratio thresholds for distress flagging
CRE_NPL_ELEVATED = 0.03      # 3% NPL ratio = elevated
CRE_NPL_DISTRESSED = 0.05    # 5% = distressed
CRE_NPL_SEVERE = 0.10        # 10% = severe

# REO as % of assets
REO_ELEVATED = 0.001          # 10 bps
REO_DISTRESSED = 0.005        # 50 bps

# Concentration thresholds (CRE / total assets)
CRE_CONCENTRATION_HIGH = 0.30   # 30% of assets in CRE
CRE_CONCENTRATION_EXTREME = 0.50


# ---------------------------------------------------------------------------
# 1. CRE Distress Score
# ---------------------------------------------------------------------------

def score_cre_distress(bank: BankProfile) -> CREDistressScore:
    """Score CRE distress exposure — higher = more distressed = more opportunity."""
    score = 0.0
    distress_segments: list[str] = []

    # CRE NPL ratio (0-35 points)
    cre_npl_ratio = 0.0
    if bank.total_cre_portfolio > 0:
        cre_npl_ratio = bank.total_cre_npl / bank.total_cre_portfolio

    if cre_npl_ratio >= CRE_NPL_SEVERE:
        score += 35
    elif cre_npl_ratio >= CRE_NPL_DISTRESSED:
        score += 25
    elif cre_npl_ratio >= CRE_NPL_ELEVATED:
        score += 15
    elif cre_npl_ratio > 0.01:
        score += 5

    # CRE concentration (0-20 points)
    cre_conc = bank.cre_concentration_ratio
    if cre_conc >= CRE_CONCENTRATION_EXTREME:
        score += 20
    elif cre_conc >= CRE_CONCENTRATION_HIGH:
        score += 12
    elif cre_conc >= 0.20:
        score += 5

    # Per-segment distress (0-30 points, 6 per segment)
    cre_segments = {
        "commercial_non_owner": bank.commercial_non_owner,
        "commercial_owner": bank.commercial_owner,
        "multifamily": bank.multifamily,
        "construction_residential": bank.construction_residential,
        "construction_commercial": bank.construction_commercial,
    }
    for name, seg in cre_segments.items():
        if seg and seg.distress_ratio >= CRE_NPL_ELEVATED:
            score += 6
            distress_segments.append(name)

    # REO burden (0-15 points)
    total_reo = sum(
        (seg.reo if seg else 0.0)
        for seg in [bank.commercial_non_owner, bank.multifamily,
                    bank.construction_residential, bank.residential_first]
    )
    reo_pct = total_reo / bank.total_assets if bank.total_assets > 0 else 0.0
    if reo_pct >= REO_DISTRESSED:
        score += 15
    elif reo_pct >= REO_ELEVATED:
        score += 8

    # Determine opportunity type
    opp = "none"
    if score >= 50:
        opp = "workout_advisory"
    elif score >= 30:
        opp = "credit_restructuring"
    elif score >= 15:
        opp = "asset_acquisition"

    # Per-segment NPLs for detail
    cno_npl = bank.commercial_non_owner.npl_ratio if bank.commercial_non_owner else 0.0
    mf_npl = bank.multifamily.npl_ratio if bank.multifamily else 0.0
    con_npl = 0.0
    for seg in [bank.construction_residential, bank.construction_commercial]:
        if seg:
            con_npl = max(con_npl, seg.npl_ratio)

    return CREDistressScore(
        score=min(score, 100.0),
        cre_npl_ratio=round(cre_npl_ratio, 4),
        cre_concentration_pct=round(cre_conc * 100, 2),
        commercial_non_owner_npl=round(cno_npl, 4),
        multifamily_npl=round(mf_npl, 4),
        construction_npl=round(con_npl, 4),
        total_reo=total_reo,
        reo_to_assets_pct=round(reo_pct * 100, 4),
        distress_segments=distress_segments,
        opportunity_type=opp,
    )


# ---------------------------------------------------------------------------
# 2. Credit Enhancement Capacity Score
# ---------------------------------------------------------------------------

def score_credit_enhancement(bank: BankProfile) -> CreditEnhancementScore:
    """Score capacity to provide credit enhancement for municipal bonds."""
    score = 0.0

    pca = bank.pca_category
    rbc = bank.risk_based_capital_ratio or 0.0
    t1_lev = bank.tier1_leverage_ratio or 0.0

    # PCA category gate (0-30 points)
    pca_scores = {
        "well_capitalized": 30,
        "adequately_capitalized": 15,
        "undercapitalized": 0,
        "significantly_undercapitalized": 0,
        "critically_undercapitalized": 0,
    }
    score += pca_scores.get(pca, 0)

    # Excess capital above well-capitalized (0-25 points)
    wc = PCA_THRESHOLDS["well_capitalized"]
    excess_rbc = max(0, rbc - wc["total_rbc"])
    excess_points = min(25, excess_rbc / 0.01 * 2.5)  # 2.5 pts per 100bps excess
    score += excess_points

    # Asset size tier (0-25 points) — larger banks have more capacity
    tier = "community"
    if bank.total_assets >= 250e9:
        tier = "money_center"
        score += 25
    elif bank.total_assets >= 50e9:
        tier = "super_regional"
        score += 20
    elif bank.total_assets >= 10e9:
        tier = "regional"
        score += 15
    elif bank.total_assets >= 1e9:
        score += 8
        tier = "community"

    # Low delinquency bonus (0-20 points) — clean books = more appetite
    total_npl = 0.0
    total_portfolio = 0.0
    for seg in bank.all_segments():
        total_npl += seg.total_distressed
        total_portfolio += seg.portfolio_balance
    overall_npl_ratio = total_npl / total_portfolio if total_portfolio > 0 else 0.0
    if overall_npl_ratio < 0.005:
        score += 20
    elif overall_npl_ratio < 0.01:
        score += 15
    elif overall_npl_ratio < 0.02:
        score += 10
    elif overall_npl_ratio < 0.03:
        score += 5

    # Enhancement types available
    enhancement_types = []
    if pca in ("well_capitalized", "adequately_capitalized"):
        if bank.total_assets >= 10e9:
            enhancement_types.extend(["loc", "sbpa"])
        elif bank.total_assets >= 1e9:
            enhancement_types.append("loc")
    if bank.total_assets >= 50e9 and pca == "well_capitalized":
        enhancement_types.append("bond_insurance_wrap")

    # Rough max enhancement estimate (2% of excess capital over well-cap)
    excess_capital_dollars = excess_rbc * bank.total_assets
    max_enhancement = excess_capital_dollars * 0.02  # Conservative 2% of excess

    return CreditEnhancementScore(
        score=min(score, 100.0),
        pca_category=pca,
        excess_capital_pct=round(excess_rbc * 100, 2),
        total_rbc_ratio=round(rbc * 100, 2),
        tier1_leverage=round(t1_lev * 100, 2),
        asset_size_tier=tier,
        enhancement_types=enhancement_types,
        max_enhancement_estimate=max_enhancement,
    )


# ---------------------------------------------------------------------------
# 3. Direct Purchase Appetite Score
# ---------------------------------------------------------------------------

def score_direct_purchase(bank: BankProfile) -> DirectPurchaseScore:
    """Score appetite for direct municipal bond purchase."""
    score = 0.0
    signals: list[str] = []

    # Bank-qualified eligibility (community banks < $10B)
    bq_eligible = bank.total_assets < 10e9
    if bq_eligible:
        score += 15
        signals.append("Bank-qualified eligible (<$10B assets)")

    # Asset size sweet spot for muni purchases ($1B-$50B)
    tier = "community"
    if bank.total_assets >= 250e9:
        tier = "money_center"
        score += 10  # Large banks buy munis but in bulk
    elif bank.total_assets >= 50e9:
        tier = "super_regional"
        score += 15
    elif bank.total_assets >= 10e9:
        tier = "regional"
        score += 20  # Sweet spot — tax-driven muni buyers
        signals.append("Regional bank — core muni buyer segment")
    elif bank.total_assets >= 1e9:
        tier = "community"
        score += 18
        signals.append("Community bank — bank-qualified bonds")

    # Capital headroom for investment (0-20 points)
    rbc = bank.risk_based_capital_ratio or 0.0
    if rbc >= 0.14:
        score += 20
        signals.append("Strong capital (RBC >14%) — room for investment")
    elif rbc >= 0.12:
        score += 15
    elif rbc >= 0.10:
        score += 10

    # Low loan-to-asset ratio signals excess liquidity (0-20 points)
    total_loans = sum(seg.portfolio_balance for seg in bank.all_segments())
    loan_ratio = total_loans / bank.total_assets if bank.total_assets > 0 else 0.0
    if loan_ratio < 0.55:
        score += 20
        signals.append("Low loan/asset ratio — excess liquidity for investments")
    elif loan_ratio < 0.65:
        score += 12
    elif loan_ratio < 0.75:
        score += 5

    # Well capitalized bonus (0-15 points)
    if bank.pca_category == "well_capitalized":
        score += 15
    elif bank.pca_category == "adequately_capitalized":
        score += 5

    # Tax position proxy — profitable banks benefit from tax-exempt income
    # Higher provision suggests profitability (banks provision from earnings)
    prov_ratio = bank.provision_loan_losses / bank.total_assets if bank.total_assets > 0 else 0.0
    tax_position = "moderate"
    if prov_ratio > 0.003:
        tax_position = "strong"
        score += 10
        signals.append("Strong earnings proxy — tax-exempt income valuable")
    elif prov_ratio > 0.001:
        score += 5

    return DirectPurchaseScore(
        score=min(score, 100.0),
        asset_size_tier=tier,
        liquidity_ratio=round(1.0 - loan_ratio, 4),
        tax_position_indicator=tax_position,
        bank_qualified_eligible=bq_eligible,
        municipal_appetite_signals=signals,
    )


# ---------------------------------------------------------------------------
# 4. Green Finance Score
# ---------------------------------------------------------------------------

# Known banks with carbon credit deal history (from research docx)
CARBON_ACTIVE_BANKS: dict[str, dict[str, Any]] = {
    "JPMORGAN CHASE BANK": {
        "deals": ["Chestnut Carbon $210M", "Mati Carbon", "CO280 $90M"],
        "volume": 300e6,
        "types": ["non_recourse_pf", "blended_finance", "offtake"],
        "level": "leader",
    },
    "BANK OF AMERICA": {
        "deals": ["Harvestone $205M 45Q", "Tax credit transfer market making"],
        "volume": 205e6,
        "types": ["tax_equity_45q", "tax_credit_transfer"],
        "level": "leader",
    },
    "MORGAN STANLEY": {
        "deals": ["Climeworks/Project Cypress 40K tons"],
        "volume": 0,
        "types": ["offtake"],
        "level": "active",
    },
    "GOLDMAN SACHS": {
        "deals": ["Climate Credit Strategy $1B equity"],
        "volume": 1e9,
        "types": ["private_credit"],
        "level": "active",
    },
    "WELLS FARGO": {
        "deals": [],
        "volume": 0,
        "types": [],
        "level": "retreating",
    },
    "CITIBANK": {
        "deals": [],
        "volume": 0,
        "types": ["green_bond_framework"],
        "level": "emerging",
    },
    "BANK OF MONTREAL": {
        "deals": ["Chestnut Carbon syndicate"],
        "volume": 0,
        "types": ["syndicate", "carbon_trading"],
        "level": "active",
    },
    "COBANK": {
        "deals": ["Chestnut Carbon syndicate", "Trailblazer $1.1B"],
        "volume": 225e6,
        "types": ["non_recourse_pf", "syndicate"],
        "level": "leader",
    },
    "EAST WEST BANK": {
        "deals": ["Chestnut Carbon syndicate"],
        "volume": 0,
        "types": ["syndicate"],
        "level": "emerging",
    },
    "U.S. BANK": {
        "deals": [],
        "volume": 0,
        "types": [],
        "level": "minimal",
    },
    "PNC BANK": {
        "deals": [],
        "volume": 0,
        "types": [],
        "level": "minimal",
    },
}


def _match_carbon_bank(bank_name: str) -> dict[str, Any] | None:
    """Match bank name to carbon-active bank registry.

    Uses strict matching: the registry key must appear as a contiguous
    substring in the bank name, and we require at least 2 words to match
    to avoid "BANK OF" matching everything.
    """
    name_upper = (
        bank_name.upper()
        .replace(", NATIONAL ASSOCIATION", "")
        .replace(", N.A.", "")
        .strip()
    )
    for key, data in CARBON_ACTIVE_BANKS.items():
        if key in name_upper:
            return data
    return None


def score_green_finance(bank: BankProfile) -> GreenFinanceScore:
    """Score ESG/carbon credit project finance capability."""
    score = 0.0

    # Carbon deal history (0-40 points)
    carbon_data = _match_carbon_bank(bank.bank_name)
    has_carbon = carbon_data is not None and len(carbon_data.get("deals", [])) > 0
    carbon_volume = carbon_data.get("volume", 0) if carbon_data else 0
    carbon_types = carbon_data.get("types", []) if carbon_data else []
    esg_level = carbon_data.get("level", "minimal") if carbon_data else "minimal"

    level_scores = {"leader": 40, "active": 25, "emerging": 10, "minimal": 0, "retreating": -5}
    score += level_scores.get(esg_level, 0)

    # Asset size for green finance capacity (0-20 points)
    if bank.total_assets >= 100e9:
        score += 20
    elif bank.total_assets >= 50e9:
        score += 15
    elif bank.total_assets >= 10e9:
        score += 10
    elif bank.total_assets >= 1e9:
        score += 5

    # Capital headroom for project finance (0-20 points)
    rbc = bank.risk_based_capital_ratio or 0.0
    if rbc >= 0.14:
        score += 20
    elif rbc >= 0.12:
        score += 15
    elif rbc >= 0.10:
        score += 10

    # Well capitalized gate (0-20 points)
    if bank.pca_category == "well_capitalized":
        score += 20
    elif bank.pca_category == "adequately_capitalized":
        score += 10

    return GreenFinanceScore(
        score=max(0, min(score, 100.0)),
        has_carbon_deals=has_carbon,
        carbon_deal_volume=carbon_volume,
        carbon_deal_types=carbon_types,
        esg_commitment_level=esg_level,
        green_bond_experience=esg_level in ("leader", "active"),
        sustainability_linked_lending=esg_level == "leader",
        net_zero_commitment=esg_level in ("leader", "active"),
    )


# ---------------------------------------------------------------------------
# Composite Scorecard
# ---------------------------------------------------------------------------

# Default weights for composite scoring
COMPOSITE_WEIGHTS = {
    "cre_distress": 0.20,
    "credit_enhancement": 0.30,
    "direct_purchase": 0.30,
    "green_finance": 0.20,
}


def score_bank(
    bank: BankProfile,
    weights: dict[str, float] | None = None,
) -> BankScorecard:
    """Produce a complete scorecard for a bank across all dimensions."""
    w = weights or COMPOSITE_WEIGHTS

    cre = score_cre_distress(bank)
    ce = score_credit_enhancement(bank)
    dp = score_direct_purchase(bank)
    gf = score_green_finance(bank)

    composite = (
        cre.score * w.get("cre_distress", 0.20)
        + ce.score * w.get("credit_enhancement", 0.30)
        + dp.score * w.get("direct_purchase", 0.30)
        + gf.score * w.get("green_finance", 0.20)
    )

    return BankScorecard(
        bank_name=bank.bank_name,
        id_rssd=bank.id_rssd,
        state=bank.state,
        total_assets=bank.total_assets,
        pca_category=bank.pca_category,
        cre_distress=cre,
        credit_enhancement=ce,
        direct_purchase=dp,
        green_finance=gf,
        composite_score=round(composite, 1),
    )


def score_all_banks(
    banks: list[BankProfile],
    weights: dict[str, float] | None = None,
) -> list[BankScorecard]:
    """Score all banks and rank by composite score."""
    scorecards = [score_bank(b, weights) for b in banks]
    scorecards.sort(key=lambda s: -s.composite_score)
    for i, sc in enumerate(scorecards, 1):
        sc.ranking = i
    return scorecards
