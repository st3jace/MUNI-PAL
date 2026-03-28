"""Deal Structuring Module — recommends covenant package, security, and call provisions.

Uses EMMA corpus benchmarks and credit analysis results to generate
a recommended deal structure calibrated to market norms.
"""

from __future__ import annotations

import logging

from .models import (
    BondSizingResult,
    CovenantPackage,
    DealStructure,
    FiveCsAssessment,
    ProjectInputs,
    SecurityPackageRecommendation,
)

logger = logging.getLogger("credit_analyzer.deal_structuring")

# Corpus-derived benchmarks (from EMMA waste sector analysis)
CORPUS_MEDIAN_COVERAGE = 1.37
CORPUS_P25_COVERAGE = 1.20
CORPUS_P75_COVERAGE = 1.50

# Spread table (simplified, from spread_table.py)
RATING_SPREADS_BPS = {
    "AAA": 10, "AA+": 20, "AA": 30, "AA-": 45,
    "A+": 55, "A": 65, "A-": 80,
    "BBB+": 100, "BBB": 120, "BBB-": 150,
    "BB+": 200, "BB": 250, "BB-": 300,
    "B+": 375, "B": 450,
}


def structure_deal(
    project: ProjectInputs,
    five_cs: FiveCsAssessment | None = None,
    sizing: BondSizingResult | None = None,
) -> DealStructure:
    """Generate a recommended deal structure based on credit analysis."""
    notes: list[str] = []
    composite = five_cs.composite_score if five_cs else 50.0
    grade = five_cs.composite_grade if five_cs else "C"

    par = sizing.recommended_par if sizing else (project.target_par_amount or 0)
    coupon = sizing.coupon_rate if sizing else (project.target_coupon_rate or 0.05)
    maturity = project.target_maturity_years

    # --- Covenant Package ---
    covenants = _recommend_covenants(project, composite, sizing)

    # --- Security Package ---
    security = _recommend_security(project, composite)

    # --- Credit Enhancement ---
    needs_enhancement = composite < 55 or grade in ("D", "F")
    enhancement_type = None
    enhancement_cost = None
    if needs_enhancement:
        if par <= 20e6:
            enhancement_type = "bond_insurance"
            enhancement_cost = 30.0  # ~30 bps
            notes.append("Bond insurance recommended due to credit profile")
        else:
            enhancement_type = "loc"
            enhancement_cost = 75.0  # ~75 bps
            notes.append("Letter of credit recommended — consult Bank Analyzer for provider match")

    # --- Call Provisions ---
    # Standard 10-year par call for fixed rate
    redemption_date = None
    if maturity >= 15:
        redemption_year = 10
        redemption_date = f"{2026 + redemption_year}-01-01"
        notes.append(f"Standard {redemption_year}-year optional redemption at par")

    extraordinary = project.has_construction_risk or project.has_technology_risk
    if extraordinary:
        notes.append("Extraordinary redemption provision recommended (construction/technology risk)")

    # --- Maturity Type ---
    if maturity <= 10:
        mat_type = "serial"
        notes.append("Serial maturity structure (short maturity)")
    elif par >= 50e6:
        mat_type = "serial_and_term"
        notes.append("Serial and term structure (large deal, investor diversification)")
    else:
        mat_type = "term"
        notes.append("Term bond structure")

    # --- Spread Estimation ---
    estimated_spread = None
    estimated_yield = None
    rating = project.credit_rating
    if rating and rating.upper() in RATING_SPREADS_BPS:
        estimated_spread = RATING_SPREADS_BPS[rating.upper()]
        estimated_yield = coupon  # Simplified; real pricing uses MMD curve
        notes.append(f"Estimated spread: {estimated_spread} bps over AAA MMD ({rating})")
    elif composite >= 70:
        estimated_spread = 65  # A-range proxy
        notes.append("No rating — estimated A-range spread based on credit profile")
    elif composite >= 55:
        estimated_spread = 120  # BBB proxy
        notes.append("No rating — estimated BBB-range spread")
    else:
        estimated_spread = 250  # BB proxy
        notes.append("No rating — estimated BB-range spread (consider enhancement)")

    # --- Comparable Deals ---
    comparables = _suggest_comparables(project)

    return DealStructure(
        project_name=project.project_name,
        bond_type=project.bond_type,
        tax_status=project.tax_status,
        par_amount=par,
        coupon_rate=coupon,
        maturity_years=maturity,
        maturity_type=mat_type,
        optional_redemption_date=redemption_date,
        optional_redemption_price=100.0,
        make_whole_call=par >= 100e6,
        extraordinary_redemption=extraordinary,
        covenants=covenants,
        security=security,
        credit_enhancement_recommended=needs_enhancement,
        enhancement_type=enhancement_type,
        estimated_enhancement_cost_bps=enhancement_cost,
        estimated_spread_bps=estimated_spread,
        estimated_yield=estimated_yield,
        comparable_deals=comparables,
        structuring_notes=notes,
    )


def _recommend_covenants(
    project: ProjectInputs,
    composite: float,
    sizing: BondSizingResult | None,
) -> CovenantPackage:
    """Recommend covenant structure based on credit quality and corpus norms."""
    rationale: list[str] = []

    # Rate covenant type
    if project.pledge_type in ("gross_revenue", "net_revenue"):
        cov_type = "rate_and_coverage"
        rationale.append("Rate and coverage covenant — standard for revenue bonds")
    else:
        cov_type = "coverage"
        rationale.append("Coverage covenant only — no rate-setting authority")

    # Coverage ratio — calibrated to credit quality
    if composite >= 75:
        min_coverage = 1.20
        rationale.append(f"1.20x coverage — strong credit supports lower threshold")
    elif composite >= 60:
        min_coverage = 1.25
        rationale.append(f"1.25x coverage — standard for investment-grade")
    elif composite >= 45:
        min_coverage = 1.35
        rationale.append(f"1.35x coverage — tighter covenant for weaker credit")
    else:
        min_coverage = 1.50
        rationale.append(f"1.50x coverage — restrictive covenant, credit enhancement needed")

    # Additional bonds test
    abt_hist = min_coverage + 0.10  # 10 bps above rate covenant
    abt_proj = min_coverage + 0.05

    # DSRF
    dsrf_type = "maximum_annual_debt_service"
    dsrf_amount = sizing.max_annual_debt_service if sizing else None
    rationale.append("DSRF at 1x MADS — corpus standard")

    # Operating reserve
    op_reserve_months = 3
    if composite < 50:
        op_reserve_months = 6
        rationale.append("6-month operating reserve — compensates for credit risk")
    else:
        rationale.append("3-month operating reserve — standard")

    # R&R fund
    rr_fund = None
    if project.has_construction_risk or project.has_technology_risk:
        rr_fund = (sizing.recommended_par if sizing else 0) * 0.005  # 0.5% of par
        rationale.append("R&R fund required — construction/technology risk")

    # Flow of funds
    flow = "gross_pledge" if project.pledge_type == "gross_revenue" else "net_pledge"

    return CovenantPackage(
        rate_covenant_type=cov_type,
        minimum_coverage_ratio=min_coverage,
        additional_bonds_test_historical=abt_hist,
        additional_bonds_test_projected=abt_proj,
        dsrf_type=dsrf_type,
        dsrf_amount=dsrf_amount,
        operating_reserve_months=op_reserve_months,
        renewal_replacement_fund=rr_fund,
        consultant_rate_study_required=composite < 60,
        flow_of_funds=flow,
        rationale=rationale,
    )


def _recommend_security(
    project: ProjectInputs,
    composite: float,
) -> SecurityPackageRecommendation:
    """Recommend security package based on project characteristics."""
    rationale: list[str] = []

    pledge = project.pledge_type or "gross_revenue"
    lien = project.lien_position or "first"
    rationale.append(f"{pledge.replace('_', ' ').title()} pledge, {lien} lien")

    # Real property
    real_prop = project.has_real_property
    if not real_prop and composite < 60:
        real_prop = True
        rationale.append("Real property mortgage recommended — strengthens security for weaker credit")

    # Equipment
    equip = project.has_equipment_lien
    if not equip and project.sector in ("waste", "energy"):
        equip = True
        rationale.append("Equipment security interest recommended for asset-intensive project")

    # Offtake assignment
    offtake = project.has_offtake_agreements
    if offtake:
        rationale.append(f"Offtake agreements assigned ({len(project.offtake_counterparties)} counterparties)")

    # Insurance
    insurance = ["property/casualty", "general_liability"]
    if project.has_construction_risk:
        insurance.append("builders_risk")
    if project.has_environmental_risk:
        insurance.append("environmental_liability")
    if project.sector == "waste":
        insurance.append("pollution_legal_liability")

    # Enhancement needed?
    enhancement = composite < 55
    enh_type = None
    if enhancement:
        enh_type = "loc" if project.target_par_amount and project.target_par_amount > 20e6 else "bond_insurance"

    return SecurityPackageRecommendation(
        pledge_type=pledge,
        lien_position=lien,
        real_property_mortgage=real_prop,
        equipment_security_interest=equip,
        offtake_assignment=offtake,
        insurance_requirements=insurance,
        credit_enhancement_needed=enhancement,
        enhancement_type=enh_type,
        rationale=rationale,
    )


def _suggest_comparables(project: ProjectInputs) -> list[str]:
    """Suggest comparable deals from the corpus based on project type."""
    comps = []
    sector = project.sector

    if sector == "waste":
        comps.extend([
            "Hillsborough County FL Resource Recovery Rev Bonds 2025",
            "Western Placer WMA Solid Waste Rev Bonds 2022A (MRF, Green)",
            "Pasco County FL Solid Waste System Rev Bonds 2022",
        ])
        if project.is_green:
            comps.append("Graphic Packaging International Green Bonds 2025")
        if project.has_technology_risk:
            comps.append("Jefferson Enterprise Energy LLC WTE 2021B-1")
    elif sector == "healthcare":
        comps.extend([
            "CCHCI Healthcare Rev Bonds (corpus benchmark)",
        ])
    elif sector == "energy":
        comps.extend([
            "Chestnut Carbon $210M Non-Recourse PF (JPM 2025)",
            "Harvestone Low Carbon Partners $205M 45Q (BofA 2024)",
        ])

    return comps[:5]
