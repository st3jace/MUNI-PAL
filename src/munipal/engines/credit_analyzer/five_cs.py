"""5 Cs Credit Assessment Engine.

Scores a project/borrower across five dimensions based on the
Commercial Banking & Credit Analyst certification framework:

  Character (20%) — Management quality, track record, governance
  Capacity  (30%) — Cash flow adequacy, DSCR, debt service coverage
  Capital   (20%) — Balance sheet strength, leverage, equity contribution
  Collateral(15%) — Security package, pledge quality, lien position
  Conditions(15%) — Market environment, sector, regulatory landscape
"""

from __future__ import annotations

import logging
from typing import Literal

from .models import (
    CScore,
    FiveCsAssessment,
    ProjectInputs,
)

logger = logging.getLogger("credit_analyzer.five_cs")

# Dimension weights
WEIGHTS = {
    "character": 0.20,
    "capacity": 0.30,
    "capital": 0.20,
    "collateral": 0.15,
    "conditions": 0.15,
}


def _grade(score: float) -> Literal["A", "B", "C", "D", "F"]:
    if score >= 80:
        return "A"
    if score >= 65:
        return "B"
    if score >= 50:
        return "C"
    if score >= 35:
        return "D"
    return "F"


# ---------------------------------------------------------------------------
# 1. Character
# ---------------------------------------------------------------------------

def _score_character(p: ProjectInputs) -> CScore:
    score = 0.0
    findings: list[str] = []
    risks: list[str] = []
    mitigants: list[str] = []
    m = p.management

    # Experience (0-30)
    if m.team_experience_years is not None:
        if m.team_experience_years >= 15:
            score += 30
            findings.append(f"Deep experience ({m.team_experience_years:.0f} years)")
        elif m.team_experience_years >= 10:
            score += 22
            findings.append(f"Solid experience ({m.team_experience_years:.0f} years)")
        elif m.team_experience_years >= 5:
            score += 14
        else:
            score += 5
            risks.append(f"Limited experience ({m.team_experience_years:.0f} years)")

    # Track record (0-25)
    if m.prior_projects_completed is not None:
        if m.prior_projects_completed >= 5 and m.prior_project_defaults == 0:
            score += 25
            findings.append(f"{m.prior_projects_completed} projects, zero defaults")
        elif m.prior_projects_completed >= 3:
            score += 18
        elif m.prior_projects_completed >= 1:
            score += 10
        if m.prior_project_defaults > 0:
            score -= 15
            risks.append(f"{m.prior_project_defaults} prior project default(s)")

    # Industry expertise (0-15)
    expertise_scores = {"deep": 15, "moderate": 10, "limited": 5, "none": 0}
    if m.industry_expertise:
        score += expertise_scores.get(m.industry_expertise, 0)
        if m.industry_expertise in ("deep", "moderate"):
            findings.append(f"Industry expertise: {m.industry_expertise}")

    # Governance (0-15)
    gov_scores = {"board_with_independents": 15, "board": 10, "owner_managed": 5, "unclear": 0}
    if m.governance_structure:
        score += gov_scores.get(m.governance_structure, 0)
        if m.governance_structure == "board_with_independents":
            mitigants.append("Independent board governance")
        elif m.governance_structure == "unclear":
            risks.append("Unclear governance structure")

    # Compliance history (0-10)
    compliance_scores = {"clean": 10, "minor_issues": 5, "material_issues": -5, "enforcement_actions": -15}
    if m.regulatory_compliance_history:
        score += compliance_scores.get(m.regulatory_compliance_history, 0)
        if m.regulatory_compliance_history in ("material_issues", "enforcement_actions"):
            risks.append(f"Compliance: {m.regulatory_compliance_history.replace('_', ' ')}")

    # Continuity risk (0-5)
    if m.management_continuity_risk == "low":
        score += 5
    elif m.management_continuity_risk == "high":
        score -= 5
        risks.append("High management continuity risk (key-person dependency)")

    score = max(0, min(score, 100))
    return CScore(
        dimension="Character",
        score=score,
        weight=WEIGHTS["character"],
        weighted_score=score * WEIGHTS["character"],
        grade=_grade(score),
        findings=findings,
        risks=risks,
        mitigants=mitigants,
    )


# ---------------------------------------------------------------------------
# 2. Capacity
# ---------------------------------------------------------------------------

def _score_capacity(p: ProjectInputs) -> CScore:
    score = 0.0
    findings: list[str] = []
    risks: list[str] = []
    mitigants: list[str] = []

    # DSCR (0-35) — most important capacity metric
    dscr = p.historical_dscr
    if dscr is not None:
        if dscr >= 2.0:
            score += 35
            findings.append(f"Strong DSCR: {dscr:.2f}x")
        elif dscr >= 1.5:
            score += 28
            findings.append(f"Adequate DSCR: {dscr:.2f}x")
        elif dscr >= 1.25:
            score += 20
            findings.append(f"Minimum DSCR: {dscr:.2f}x")
        elif dscr >= 1.10:
            score += 10
            risks.append(f"Thin DSCR: {dscr:.2f}x — limited debt service cushion")
        elif dscr >= 1.0:
            score += 5
            risks.append(f"Marginal DSCR: {dscr:.2f}x — breakeven coverage")
        else:
            risks.append(f"Insufficient DSCR: {dscr:.2f}x — does not cover debt service")

    # Operating margin (0-20)
    margin = p.operating_margin
    if margin is not None:
        if margin >= 0.30:
            score += 20
            findings.append(f"Strong operating margin: {margin:.0%}")
        elif margin >= 0.20:
            score += 15
        elif margin >= 0.10:
            score += 10
        elif margin >= 0.05:
            score += 5
            risks.append(f"Thin operating margin: {margin:.0%}")
        else:
            risks.append(f"Negative or minimal margin: {margin:.0%}")

    # Revenue scale (0-15)
    rev = p.historical_revenue
    if rev is not None:
        if rev >= 50e6:
            score += 15
            findings.append(f"Substantial revenue base: ${rev/1e6:.0f}M")
        elif rev >= 20e6:
            score += 12
        elif rev >= 5e6:
            score += 8
        elif rev >= 1e6:
            score += 4
        else:
            risks.append(f"Small revenue base: ${rev/1e6:.1f}M")

    # Revenue growth / projections (0-15)
    if p.revenue_growth_rate is not None:
        if p.revenue_growth_rate >= 0.05:
            score += 15
            findings.append(f"Positive growth trend: {p.revenue_growth_rate:.0%}")
        elif p.revenue_growth_rate >= 0.02:
            score += 10
        elif p.revenue_growth_rate >= 0:
            score += 5
        else:
            risks.append(f"Declining revenue: {p.revenue_growth_rate:.0%}")

    # Revenue projections quality (0-15)
    if len(p.revenue_projections) >= 5:
        score += 15
        findings.append(f"Detailed {len(p.revenue_projections)}-year projections provided")
    elif len(p.revenue_projections) >= 3:
        score += 10
    elif p.revenue_growth_rate is not None:
        score += 5

    score = max(0, min(score, 100))
    return CScore(
        dimension="Capacity",
        score=score,
        weight=WEIGHTS["capacity"],
        weighted_score=score * WEIGHTS["capacity"],
        grade=_grade(score),
        findings=findings,
        risks=risks,
        mitigants=mitigants,
    )


# ---------------------------------------------------------------------------
# 3. Capital
# ---------------------------------------------------------------------------

def _score_capital(p: ProjectInputs) -> CScore:
    score = 0.0
    findings: list[str] = []
    risks: list[str] = []
    mitigants: list[str] = []

    # Equity contribution (0-30) — skin in the game
    if p.equity_contribution_pct is not None:
        if p.equity_contribution_pct >= 0.40:
            score += 30
            findings.append(f"Strong equity: {p.equity_contribution_pct:.0%} of project cost")
        elif p.equity_contribution_pct >= 0.25:
            score += 22
            findings.append(f"Adequate equity: {p.equity_contribution_pct:.0%}")
        elif p.equity_contribution_pct >= 0.15:
            score += 14
        elif p.equity_contribution_pct >= 0.10:
            score += 8
            risks.append(f"Low equity: {p.equity_contribution_pct:.0%}")
        else:
            risks.append(f"Minimal equity: {p.equity_contribution_pct:.0%} — high leverage")
    elif p.equity_contribution and p.total_project_cost:
        pct = p.equity_contribution / p.total_project_cost
        if pct >= 0.25:
            score += 22
            findings.append(f"Equity contribution: ${p.equity_contribution/1e6:.0f}M ({pct:.0%})")
        elif pct >= 0.10:
            score += 12

    # Leverage ratio (0-25)
    lev = p.leverage_ratio
    if lev is not None:
        if lev <= 1.0:
            score += 25
            findings.append(f"Conservative leverage: {lev:.2f}x")
        elif lev <= 2.0:
            score += 18
        elif lev <= 3.0:
            score += 12
        elif lev <= 5.0:
            score += 5
            risks.append(f"Elevated leverage: {lev:.2f}x")
        else:
            risks.append(f"High leverage: {lev:.2f}x")
    elif p.total_liabilities and p.total_equity and p.total_equity > 0:
        lev = p.total_liabilities / p.total_equity
        if lev <= 2.0:
            score += 18
        elif lev <= 4.0:
            score += 10

    # Current ratio / liquidity (0-20)
    cr = p.current_ratio
    if cr is not None:
        if cr >= 2.0:
            score += 20
            findings.append(f"Strong liquidity: {cr:.2f}x current ratio")
        elif cr >= 1.5:
            score += 15
        elif cr >= 1.2:
            score += 10
        elif cr >= 1.0:
            score += 5
            risks.append(f"Tight liquidity: {cr:.2f}x current ratio")
        else:
            risks.append(f"Liquidity concern: {cr:.2f}x current ratio")

    # Net worth / asset base (0-15)
    if p.total_assets and p.total_equity:
        equity_ratio = p.total_equity / p.total_assets
        if equity_ratio >= 0.50:
            score += 15
            mitigants.append(f"Strong equity base: {equity_ratio:.0%} of assets")
        elif equity_ratio >= 0.30:
            score += 10
        elif equity_ratio >= 0.15:
            score += 5

    # Cash reserves (0-10)
    if p.cash_on_hand and p.historical_expenses:
        months_cash = (p.cash_on_hand / p.historical_expenses) * 12
        if months_cash >= 6:
            score += 10
            mitigants.append(f"Cash reserves: {months_cash:.0f} months operating expenses")
        elif months_cash >= 3:
            score += 5

    score = max(0, min(score, 100))
    return CScore(
        dimension="Capital",
        score=score,
        weight=WEIGHTS["capital"],
        weighted_score=score * WEIGHTS["capital"],
        grade=_grade(score),
        findings=findings,
        risks=risks,
        mitigants=mitigants,
    )


# ---------------------------------------------------------------------------
# 4. Collateral
# ---------------------------------------------------------------------------

def _score_collateral(p: ProjectInputs) -> CScore:
    score = 0.0
    findings: list[str] = []
    risks: list[str] = []
    mitigants: list[str] = []

    # Pledge type (0-30)
    pledge_scores = {"gross_revenue": 30, "net_revenue": 22, "specific_revenue": 15, "none": 0}
    if p.pledge_type:
        score += pledge_scores.get(p.pledge_type, 0)
        findings.append(f"Revenue pledge: {p.pledge_type.replace('_', ' ')}")
    else:
        risks.append("No revenue pledge specified")

    # Lien position (0-20)
    lien_scores = {"first": 20, "pari_passu": 12, "second": 5, "subordinate": 0}
    if p.lien_position:
        score += lien_scores.get(p.lien_position, 0)
        if p.lien_position == "first":
            mitigants.append("First lien position")
        elif p.lien_position == "subordinate":
            risks.append("Subordinate lien — structural subordination risk")

    # Physical collateral (0-15)
    if p.has_real_property:
        score += 10
        mitigants.append("Real property mortgage")
    if p.has_equipment_lien:
        score += 5
        mitigants.append("Equipment security interest")

    # Offtake contracts (0-20)
    if p.has_offtake_agreements:
        score += 15
        mitigants.append(f"Offtake agreements assigned ({len(p.offtake_counterparties)} counterparties)")
        if len(p.offtake_counterparties) >= 2:
            score += 5
            mitigants.append("Diversified offtake counterparties")
    else:
        if p.sector in ("waste", "energy"):
            risks.append("No offtake agreements — revenue depends on spot/merchant sales")

    # Insurance (0-10)
    if p.has_insurance:
        score += 10
        mitigants.append("Insurance coverage in place")

    # Credit rating (0-5 bonus)
    if p.credit_rating:
        rating_upper = p.credit_rating.upper()
        if any(ig in rating_upper for ig in ["AAA", "AA", "A", "BBB", "BAA"]):
            score += 5
            findings.append(f"Investment-grade rating: {p.credit_rating}")

    score = max(0, min(score, 100))
    return CScore(
        dimension="Collateral",
        score=score,
        weight=WEIGHTS["collateral"],
        weighted_score=score * WEIGHTS["collateral"],
        grade=_grade(score),
        findings=findings,
        risks=risks,
        mitigants=mitigants,
    )


# ---------------------------------------------------------------------------
# 5. Conditions
# ---------------------------------------------------------------------------

def _score_conditions(p: ProjectInputs) -> CScore:
    score = 0.0
    findings: list[str] = []
    risks: list[str] = []
    mitigants: list[str] = []

    # Market position (0-25)
    position_scores = {"dominant": 25, "strong": 18, "competitive": 12, "weak": 3}
    if p.market_position:
        score += position_scores.get(p.market_position, 0)
        if p.market_position in ("dominant", "strong"):
            findings.append(f"Market position: {p.market_position}")
        elif p.market_position == "weak":
            risks.append("Weak market position")

    # Sector outlook (0-25)
    outlook_scores = {"growing": 25, "stable": 18, "declining": 8, "distressed": 0}
    if p.sector_outlook:
        score += outlook_scores.get(p.sector_outlook, 0)
        if p.sector_outlook == "growing":
            mitigants.append("Growing sector outlook")
        elif p.sector_outlook in ("declining", "distressed"):
            risks.append(f"Sector outlook: {p.sector_outlook}")

    # Regulatory environment (0-20)
    reg_scores = {"favorable": 20, "stable": 15, "challenging": 5, "hostile": 0}
    if p.regulatory_environment:
        score += reg_scores.get(p.regulatory_environment, 0)
        if p.regulatory_environment in ("challenging", "hostile"):
            risks.append(f"Regulatory environment: {p.regulatory_environment}")

    # Competitive threats (0-15)
    comp_scores = {"low": 15, "moderate": 10, "high": 3}
    if p.competitive_threats:
        score += comp_scores.get(p.competitive_threats, 0)
        if p.competitive_threats == "high":
            risks.append("High competitive pressure")

    # Risk factors penalty (0 to -15)
    risk_flags = [
        (p.has_technology_risk, "Technology risk"),
        (p.has_construction_risk, "Construction risk"),
        (p.has_environmental_risk, "Environmental compliance risk"),
        (p.has_feedstock_risk, "Feedstock supply risk"),
        (p.has_regulatory_risk, "Regulatory risk"),
    ]
    for flag, label in risk_flags:
        if flag:
            score -= 3
            risks.append(label)

    # Green bond bonus (0-5)
    if p.is_green:
        score += 5
        mitigants.append("Green bond designation — favorable market reception")

    score = max(0, min(score, 100))
    return CScore(
        dimension="Conditions",
        score=score,
        weight=WEIGHTS["conditions"],
        weighted_score=score * WEIGHTS["conditions"],
        grade=_grade(score),
        findings=findings,
        risks=risks,
        mitigants=mitigants,
    )


# ---------------------------------------------------------------------------
# Composite Assessment
# ---------------------------------------------------------------------------

def assess_five_cs(project: ProjectInputs) -> FiveCsAssessment:
    """Run the complete 5 Cs credit assessment."""
    character = _score_character(project)
    capacity = _score_capacity(project)
    capital = _score_capital(project)
    collateral = _score_collateral(project)
    conditions = _score_conditions(project)

    composite = (
        character.weighted_score
        + capacity.weighted_score
        + capital.weighted_score
        + collateral.weighted_score
        + conditions.weighted_score
    )

    # Recommendation
    if composite >= 75:
        rec = "strong_approve"
    elif composite >= 60:
        rec = "approve"
    elif composite >= 45:
        rec = "conditional_approve"
    elif composite >= 30:
        rec = "additional_review"
    else:
        rec = "decline"

    # Aggregate strengths, risks, conditions
    all_scores = [character, capacity, capital, collateral, conditions]
    key_strengths = []
    key_risks = []
    conditions_list = []
    for cs in all_scores:
        key_strengths.extend(cs.findings[:2])
        key_risks.extend(cs.risks[:2])

    # Auto-generate conditions for approval
    if capacity.grade in ("D", "F"):
        conditions_list.append("Demonstrate minimum 1.25x DSCR through independent feasibility study")
    if collateral.grade in ("D", "F"):
        conditions_list.append("Provide credit enhancement (LOC or bond insurance) to offset weak security")
    if character.grade in ("D", "F"):
        conditions_list.append("Require experienced project management consultant or co-developer")
    if capital.grade in ("D", "F"):
        conditions_list.append("Increase equity contribution to minimum 20% of project cost")

    return FiveCsAssessment(
        project_name=project.project_name,
        character=character,
        capacity=capacity,
        capital=capital,
        collateral=collateral,
        conditions=conditions,
        composite_score=round(composite, 1),
        composite_grade=_grade(composite),
        recommendation=rec,
        key_strengths=key_strengths,
        key_risks=key_risks,
        conditions_for_approval=conditions_list,
    )
