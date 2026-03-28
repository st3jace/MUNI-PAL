"""Bank-Deal matching engine.

Given a deal profile, scores and ranks banks by fit across relevant dimensions.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from .models import (
    BankMatch,
    BankScorecard,
    DealMatchRequest,
    DealMatchResult,
)

logger = logging.getLogger("bank_analyzer.matching")


def match_banks_to_deal(
    scorecards: list[BankScorecard],
    deal: DealMatchRequest,
    top_n: int = 20,
) -> DealMatchResult:
    """Match scored banks to a specific deal, returning ranked results."""
    matches: list[BankMatch] = []

    for sc in scorecards:
        match_score = 0.0
        reasons: list[str] = []
        concerns: list[str] = []
        role = None

        # --- Size filter ---
        if deal.min_bank_assets and sc.total_assets < deal.min_bank_assets:
            continue
        if deal.max_bank_assets and sc.total_assets > deal.max_bank_assets:
            continue

        # --- State proximity bonus ---
        if deal.state and sc.state and sc.state == deal.state:
            match_score += 10
            reasons.append(f"Same state ({sc.state})")

        # --- PCA gate: undercapitalized banks can't enhance ---
        if sc.pca_category in ("undercapitalized", "significantly_undercapitalized", "critically_undercapitalized"):
            if deal.needs_credit_enhancement:
                continue  # Skip entirely
            concerns.append(f"PCA: {sc.pca_category}")

        # --- Credit enhancement deals ---
        if deal.needs_credit_enhancement:
            match_score += sc.credit_enhancement.score * 0.6
            if sc.credit_enhancement.score >= 60:
                reasons.append(f"Strong credit enhancement capacity ({sc.credit_enhancement.score:.0f})")
                if deal.enhancement_type in sc.credit_enhancement.enhancement_types:
                    match_score += 15
                    reasons.append(f"Offers {deal.enhancement_type.upper()}")
                role = "credit_enhancer"
            if deal.deal_size > sc.credit_enhancement.max_enhancement_estimate * 5:
                concerns.append("Deal size may exceed enhancement capacity")

        # --- Direct purchase / private placement ---
        if deal.deal_type in ("private_placement", "revenue_bond", "go_bond"):
            match_score += sc.direct_purchase.score * 0.4
            if sc.direct_purchase.score >= 50:
                reasons.append(f"Strong direct purchase appetite ({sc.direct_purchase.score:.0f})")
            if deal.bank_qualified and sc.direct_purchase.bank_qualified_eligible:
                match_score += 15
                reasons.append("Bank-qualified eligible — enhanced tax benefit")
                role = role or "direct_purchaser"
            elif deal.bank_qualified and not sc.direct_purchase.bank_qualified_eligible:
                match_score -= 10
                concerns.append("Not bank-qualified eligible (>$10B assets)")

        # --- Green / carbon deals ---
        if deal.is_green or deal.is_carbon_credit:
            match_score += sc.green_finance.score * 0.5
            if sc.green_finance.has_carbon_deals:
                match_score += 20
                reasons.append(f"Active carbon credit lender ({sc.green_finance.esg_commitment_level})")
                for dt in sc.green_finance.carbon_deal_types:
                    reasons.append(f"  Deal type: {dt}")
                role = role or "lead_underwriter"
            elif sc.green_finance.esg_commitment_level in ("active", "emerging"):
                match_score += 10
                reasons.append(f"ESG commitment: {sc.green_finance.esg_commitment_level}")
                role = role or "syndicate_member"
            if sc.green_finance.esg_commitment_level == "retreating":
                concerns.append("Retreating from ESG commitments")
                match_score -= 15

        # --- Project finance ---
        if deal.deal_type == "project_finance":
            # Prefer well-capitalized larger banks
            if sc.total_assets >= 50e9 and sc.pca_category == "well_capitalized":
                match_score += 20
                reasons.append("Scale and capital for project finance")
                role = role or "lead_underwriter"
            elif sc.total_assets >= 10e9:
                match_score += 10
                role = role or "syndicate_member"

        # --- Conduit ---
        if deal.deal_type == "conduit":
            match_score += sc.credit_enhancement.score * 0.3
            match_score += sc.direct_purchase.score * 0.3
            role = role or "co_manager"

        # --- CRE distress opportunity (inverse matching) ---
        # Banks with CRE distress are TARGETS for advisory, not providers
        if sc.cre_distress.score >= 30:
            if deal.deal_type not in ("credit_enhancement",):
                reasons.append(f"CRE distress ({sc.cre_distress.opportunity_type}) — advisory opportunity")

        # Default role
        if role is None:
            if sc.total_assets >= 100e9:
                role = "lead_underwriter"
            elif sc.total_assets >= 10e9:
                role = "co_manager"
            else:
                role = "direct_purchaser"

        if match_score > 0:
            matches.append(BankMatch(
                bank_name=sc.bank_name,
                id_rssd=sc.id_rssd,
                state=sc.state,
                total_assets=sc.total_assets,
                match_score=round(min(match_score, 100.0), 1),
                match_reasons=reasons,
                concerns=concerns,
                recommended_role=role,
            ))

    # Sort by match score descending
    matches.sort(key=lambda m: -m.match_score)

    return DealMatchResult(
        deal=deal,
        matches=matches[:top_n],
        total_banks_screened=len(scorecards),
        timestamp=datetime.now(timezone.utc),
    )
