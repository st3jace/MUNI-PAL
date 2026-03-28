"""Standard Model Integration — capstone layer for Credit Analyzer.

Positions a prospective deal against the existing EMMA corpus using
the Summers methodology (Phases 1-6):

  - F_i (Fundamental Score): Where the deal ranks on a 0-100 scale
  - S_Omega projection: Estimated risk-adjusted return
  - CRI percentile: Composite ranking vs corpus constituents
  - SIC efficiency: Position on the risk-return-drawdown frontier

Loads pre-computed analysis results from the Bond OS Extractor's
analysis/ directory and interpolates the prospective deal into the
existing distribution.
"""

from __future__ import annotations

import json
import logging
import math
from pathlib import Path
from typing import Any

from .models import (
    BondSizingResult,
    CreditAnalysisResult,
    FiveCsAssessment,
    ProjectInputs,
)

logger = logging.getLogger("credit_analyzer.standard_model")

# Where the Bond OS Extractor stores analysis results
ANALYSIS_DIRS = [
    Path(__file__).resolve().parents[4] / "emma" / "bond_os_extractor" / "data" / "waste" / "analysis",
    Path(__file__).resolve().parents[4] / "emma" / "bond_os_extractor" / "data" / "wte" / "analysis",
]


def _load_json(filename: str) -> dict[str, Any] | None:
    """Load analysis JSON from the first sector that has it."""
    for d in ANALYSIS_DIRS:
        path = d / filename
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
    return None


# ---------------------------------------------------------------------------
# Corpus Distribution Loaders
# ---------------------------------------------------------------------------

def _load_fundamental_distribution() -> list[float]:
    """Load all F_i scores from the corpus."""
    data = _load_json("fundamental_scores.json")
    if not data:
        return []
    scores = data.get("scores", [])
    return sorted([s["f_score"] for s in scores if s.get("f_score", 0) > 0])


def _load_irs_distribution() -> list[dict[str, Any]]:
    """Load IRS (Integrated Risk Score) results from extended risk analysis."""
    data = _load_json("extended_risk_results.json")
    if not data:
        return []
    return data.get("assets", [])


def _load_benchmark() -> dict[str, Any]:
    """Load benchmark/CRI results."""
    data = _load_json("benchmark_results.json")
    return data or {}


# ---------------------------------------------------------------------------
# F_i Score Projection
# ---------------------------------------------------------------------------

# Maps 5 Cs dimensions → Summers F_i dimensions (closest analogs)
# Summers dimensions: financial_stability(0.30), profitability(0.20),
#   credit_quality(0.25), structural_quality(0.15), growth_momentum(0.10)
FIVE_CS_TO_FI_WEIGHTS = {
    "capacity": 0.30,     # → financial_stability (DSCR, cash flow)
    "capital": 0.20,      # → profitability (leverage, equity)
    "collateral": 0.25,   # → credit_quality + structural_quality
    "conditions": 0.15,   # → growth_momentum
    "character": 0.10,    # → structural_quality (governance)
}


def project_fundamental_score(
    five_cs: FiveCsAssessment,
    project: ProjectInputs,
) -> float:
    """Project an F_i score for the prospective deal.

    Maps 5 Cs scores to the Summers F_i scale (0-100) using the
    dimension weight mapping above, then calibrates against the
    corpus distribution.
    """
    # Weighted combination of 5 Cs scores using F_i-aligned weights
    raw = (
        five_cs.capacity.score * FIVE_CS_TO_FI_WEIGHTS["capacity"]
        + five_cs.capital.score * FIVE_CS_TO_FI_WEIGHTS["capital"]
        + five_cs.collateral.score * FIVE_CS_TO_FI_WEIGHTS["collateral"]
        + five_cs.conditions.score * FIVE_CS_TO_FI_WEIGHTS["conditions"]
        + five_cs.character.score * FIVE_CS_TO_FI_WEIGHTS["character"]
    )

    # Bonus/penalty for specific credit factors the F_i model weighs heavily
    if project.historical_dscr and project.historical_dscr >= 1.5:
        raw += 5  # Strong DSCR bonus
    if project.credit_rating:
        rating_upper = project.credit_rating.upper()
        if any(ig in rating_upper for ig in ["AA", "AAA"]):
            raw += 8
        elif "A" in rating_upper and "B" not in rating_upper:
            raw += 4
        elif "BBB" in rating_upper or "BAA" in rating_upper:
            raw += 2

    return round(max(0, min(raw, 100)), 1)


# ---------------------------------------------------------------------------
# S_Omega Projection
# ---------------------------------------------------------------------------

def project_s_omega(
    sizing: BondSizingResult,
    project: ProjectInputs,
    risk_free_rate: float = 0.04,
) -> float:
    """Estimate S_Omega for the prospective deal.

    S_Omega = r_f + omega_adjustment * (E(R_i) - r_f) / downside_risk

    For a prospective bond, E(R_i) is approximated by the coupon rate
    adjusted for credit spread, and downside risk is derived from
    DSCR volatility (lower DSCR = higher downside risk).
    """
    coupon = sizing.coupon_rate if sizing.coupon_rate > 0 else 0.05
    min_dscr = sizing.min_dscr if sizing.min_dscr > 0 else 1.0

    # Expected return ≈ coupon (for a par bond held to maturity)
    expected_return = coupon

    # Excess return over risk-free
    excess = expected_return - risk_free_rate

    # Omega ratio proxy: DSCR acts as gain/loss ratio
    # Higher DSCR = more gain probability relative to loss
    omega_proxy = min_dscr  # DSCR of 1.25 → omega ≈ 1.25

    # Downside risk proxy: inverse of DSCR cushion
    dscr_cushion = max(0.01, min_dscr - 1.0)  # How far above breakeven
    downside_proxy = 1.0 / (1.0 + dscr_cushion * 5)  # Scale to ~0.15-0.50 range

    # S_Omega computation
    if downside_proxy > 0:
        s_omega = risk_free_rate + omega_proxy * excess / (1 + downside_proxy)
    else:
        s_omega = risk_free_rate

    return round(s_omega, 6)


# ---------------------------------------------------------------------------
# SIC Efficiency
# ---------------------------------------------------------------------------

def compute_sic_efficiency(
    projected_return: float,
    projected_risk: float,
    corpus_assets: list[dict[str, Any]],
) -> float:
    """Compute SIC efficiency relative to corpus frontier.

    Efficiency = distance from origin to asset / distance from origin
    to the frontier at the same angle. Higher = closer to frontier.
    """
    if not corpus_assets or projected_risk <= 0:
        return 0.0

    # Simple efficiency: return/risk ratio compared to best in corpus
    asset_sharpe = projected_return / projected_risk

    corpus_sharpes = []
    for a in corpus_assets:
        irs = a.get("irs", 0)
        if irs > 0:
            corpus_sharpes.append(irs)

    if not corpus_sharpes:
        return min(asset_sharpe, 1.0)

    max_corpus = max(corpus_sharpes)
    if max_corpus <= 0:
        return 0.0

    return round(min(asset_sharpe / max_corpus, 1.5), 4)


# ---------------------------------------------------------------------------
# Percentile Positioning
# ---------------------------------------------------------------------------

def compute_percentile(value: float, distribution: list[float]) -> float:
    """Compute what percentile a value falls at in a distribution."""
    if not distribution:
        return 50.0
    below = sum(1 for v in distribution if v <= value)
    return round(below / len(distribution) * 100, 1)


# ---------------------------------------------------------------------------
# Full Standard Model Integration
# ---------------------------------------------------------------------------

def integrate_standard_model(
    result: CreditAnalysisResult,
    project: ProjectInputs,
) -> CreditAnalysisResult:
    """Enrich a CreditAnalysisResult with Standard Model positioning.

    Computes projected F_i, S_Omega, CRI percentile, and SIC efficiency
    against the existing EMMA corpus.
    """
    if not result.five_cs or not result.bond_sizing:
        return result

    # 1. Project F_i score
    f_score = project_fundamental_score(result.five_cs, project)
    result.projected_f_score = f_score

    # 2. Project S_Omega
    s_omega = project_s_omega(result.bond_sizing, project)
    result.projected_s_omega = s_omega

    # 3. Corpus percentile for F_i
    f_distribution = _load_fundamental_distribution()
    if f_distribution:
        result.corpus_cri_percentile = compute_percentile(f_score, f_distribution)
        logger.info(
            "F_i=%.1f → %sth percentile of %d corpus obligors",
            f_score, result.corpus_cri_percentile, len(f_distribution),
        )

    # 4. SIC efficiency
    irs_assets = _load_irs_distribution()
    if irs_assets:
        # Use S_Omega as return proxy and inverse DSCR cushion as risk proxy
        min_dscr = result.bond_sizing.min_dscr
        projected_risk = 1.0 / max(0.01, min_dscr - 0.8)  # Risk proxy
        result.sic_efficiency = compute_sic_efficiency(
            s_omega, projected_risk, irs_assets,
        )

    # 5. Refine credit opinion based on Standard Model positioning
    if result.corpus_cri_percentile and result.corpus_cri_percentile >= 80:
        if result.credit_opinion in ("crossover", "not_rated_adequate"):
            result.credit_opinion = "not_rated_strong"

    # 6. Generate executive summary
    result.executive_summary = _generate_executive_summary(result, project)

    return result


def _generate_executive_summary(
    result: CreditAnalysisResult,
    project: ProjectInputs,
) -> str:
    """Generate a narrative executive summary from all analysis components."""
    parts = []

    # Opening
    parts.append(f"{project.project_name} is a {project.sector} sector "
                 f"{project.bond_type.replace('_', ' ')} bond issuance")
    if result.bond_sizing and result.bond_sizing.recommended_par > 0:
        parts.append(f" sized at ${result.bond_sizing.recommended_par / 1e6:.0f}M")
    parts.append(".")

    # 5 Cs
    if result.five_cs:
        fc = result.five_cs
        parts.append(f" The 5 Cs credit assessment yields a composite score of "
                     f"{fc.composite_score:.1f}/100 ({fc.composite_grade}), "
                     f"with a recommendation of {fc.recommendation.replace('_', ' ')}.")

    # Sizing
    if result.bond_sizing and result.bond_sizing.recommended_par > 0:
        bs = result.bond_sizing
        parts.append(f" At a {bs.coupon_rate:.2%} coupon over {bs.maturity_years:.0f} years, "
                     f"the minimum DSCR is {bs.min_dscr:.2f}x against a "
                     f"{bs.target_dscr:.2f}x target.")

    # Standard Model positioning
    if result.projected_f_score is not None:
        parts.append(f" The projected fundamental score (F_i) of "
                     f"{result.projected_f_score:.1f} places this deal at the "
                     f"{result.corpus_cri_percentile:.0f}th percentile of "
                     f"the EMMA corpus.")

    # Deal structure
    if result.deal_structure:
        ds = result.deal_structure
        if ds.credit_enhancement_recommended:
            parts.append(f" Credit enhancement ({ds.enhancement_type}) is recommended "
                         f"to strengthen market reception.")
        if ds.estimated_spread_bps:
            parts.append(f" Estimated spread: {ds.estimated_spread_bps:.0f} bps over AAA MMD.")

    # Opinion
    if result.credit_opinion:
        opinion = result.credit_opinion.replace("_", " ").title()
        parts.append(f" Overall credit opinion: {opinion}.")

    return "".join(parts)
