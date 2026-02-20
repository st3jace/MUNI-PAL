"""Phase 3: Benchmark Construction & Index Development.

Builds on Phase 1 (fundamental scores) and Phase 2 (S_Omega) to construct:

  1. Sector Benchmark — S_Omega-weighted composite representing the waste sector's
     quality-adjusted performance. Unlike the equal-weighted market benchmark in
     Phase 2, this weights constituents by their risk-adjusted performance.

  2. SIC Efficiency Frontier — Plots assets in (R_A, E_A) space to identify
     efficient positions. The efficiency ratio E_A / R_A gives return per unit
     of annualized risk.

  3. Composite Ranking Index (CRI) — Multi-factor rank combining:
       - S_Omega rank (40% weight) — total risk-adjusted performance
       - SIC efficiency rank (25% weight) — return per unit of risk
       - Drawdown resilience rank (20% weight) — inverse MDDD_S
       - Fundamental quality rank (15% weight) — F_i from Phase 1

  4. Relative Value Analysis — Each asset's S_Omega, SIC, and CRI versus
     the sector benchmark, expressed as spreads and percentiles.

Summers Paper 1, Section 3: "S_Omega provides a single, intuitive measure
that can be used to rank and compare assets... The SIC matrix provides the
complete picture of risk, return, and liquidity characteristics."

This phase produces the ranked investable universe and benchmark analytics
that feed into Phase 4 (Hilbert Space Signal Extraction).
"""
from __future__ import annotations

import json
import logging
import math
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from ..config import get_settings
from .omega import SOmegaResult

logger = logging.getLogger("bond_os_extractor.analysis.benchmark")


# Composite Ranking Index weights
CRI_WEIGHTS = {
    "s_omega": 0.40,        # Total risk-adjusted performance
    "sic_efficiency": 0.25,  # Return per unit of risk (E_A / R_A)
    "drawdown_resilience": 0.20,  # Inverse MDDD_S
    "fundamental_quality": 0.15,  # F_i from Phase 1
}


@dataclass
class ConstituentAnalysis:
    """Analysis of one asset relative to the sector benchmark."""
    asset_id: str
    asset_name: str

    # Raw measures (from Phase 2)
    s_omega: float = 0.0
    omega_at_rf: float = 0.0
    annualized_risk: float = 0.0      # R_A
    annualized_return: float = 0.0    # E_A
    mddd_s_years: float = 0.0        # MDDD_S in years
    max_drawdown_pct: float = 0.0
    f_score: float = 0.0             # F_i from Phase 1
    n_observations: int = 0
    n_years: float = 0.0

    # Derived measures
    sic_efficiency: float = 0.0       # E_A / R_A
    drawdown_resilience: float = 0.0  # 1 / MDDD_S (higher = better)
    benchmark_weight: float = 0.0     # S_Omega-proportional weight

    # Relative value vs benchmark
    s_omega_spread: float = 0.0       # Asset S_Omega - Benchmark S_Omega
    efficiency_spread: float = 0.0    # Asset efficiency - Benchmark efficiency
    return_spread: float = 0.0        # Asset E_A - Benchmark E_A
    risk_spread: float = 0.0          # Asset R_A - Benchmark R_A

    # Composite Ranking Index
    s_omega_rank: int = 0
    efficiency_rank: int = 0
    drawdown_rank: int = 0
    fundamental_rank: int = 0
    cri_score: float = 0.0           # Composite ranking (0-100)
    cri_rank: int = 0

    # Percentile positions (0-100, higher = better)
    s_omega_percentile: float = 0.0
    efficiency_percentile: float = 0.0
    drawdown_percentile: float = 0.0
    fundamental_percentile: float = 0.0

    # Signal
    signal: str = ""                  # "overweight" | "equal" | "underweight"


@dataclass
class SectorBenchmark:
    """Sector-level benchmark analytics."""
    name: str = "Waste Sector Benchmark"
    n_constituents: int = 0

    # Weighted averages (S_Omega-weighted)
    benchmark_s_omega: float = 0.0
    benchmark_efficiency: float = 0.0
    benchmark_return: float = 0.0     # Weighted E_A
    benchmark_risk: float = 0.0       # Weighted R_A
    benchmark_mddd_s: float = 0.0     # Weighted MDDD_S
    benchmark_f_score: float = 0.0    # Weighted F_i

    # Sector envelope (min/max across constituents)
    min_s_omega: float = 0.0
    max_s_omega: float = 0.0
    min_return: float = 0.0
    max_return: float = 0.0
    min_risk: float = 0.0
    max_risk: float = 0.0
    min_mddd_s: float = 0.0
    max_mddd_s: float = 0.0

    # Dispersion
    s_omega_spread: float = 0.0       # max - min
    return_spread: float = 0.0
    risk_spread: float = 0.0

    # Concentration (Herfindahl index of benchmark weights)
    herfindahl: float = 0.0
    effective_n: float = 0.0          # 1 / HHI


@dataclass
class BenchmarkAnalysis:
    """Complete Phase 3 benchmark and index analysis."""
    benchmark: SectorBenchmark
    constituents: list[ConstituentAnalysis] = field(default_factory=list)
    generated_at: str = ""

    @property
    def ranked(self) -> list[ConstituentAnalysis]:
        """Return constituents sorted by CRI rank."""
        return sorted(self.constituents, key=lambda c: c.cri_rank)


def _safe_ratio(num: float, den: float, default: float = 0.0) -> float:
    """Safe division returning default when denominator is zero or negative."""
    if den <= 0 or not math.isfinite(den):
        return default
    result = num / den
    return result if math.isfinite(result) else default


def _percentile_rank(values: list[float], target: float) -> float:
    """Compute percentile rank of target in values (0-100, higher = better)."""
    if not values:
        return 50.0
    n_below = sum(1 for v in values if v < target)
    n_equal = sum(1 for v in values if v == target)
    # Average percentile for ties
    return ((n_below + 0.5 * n_equal) / len(values)) * 100.0


def build_benchmark(
    s_omega_results: list[SOmegaResult],
) -> BenchmarkAnalysis:
    """Construct sector benchmark and relative value analysis from Phase 2 results.

    This is the main entry point for Phase 3. Takes S_Omega results from
    Phase 2 and produces:
      1. S_Omega-weighted sector benchmark
      2. SIC efficiency analysis
      3. Composite Ranking Index
      4. Relative value signals
    """
    if not s_omega_results:
        return BenchmarkAnalysis(
            benchmark=SectorBenchmark(),
            generated_at=datetime.now().isoformat(),
        )

    # Step 1: Build constituent profiles
    constituents: list[ConstituentAnalysis] = []

    for result in s_omega_results:
        sic = result.sic
        ca = ConstituentAnalysis(
            asset_id=result.asset_id,
            asset_name=result.asset_name,
            s_omega=result.s_omega,
            omega_at_rf=result.omega_at_rf,
            annualized_risk=sic.annualized_risk if sic else 0.0,
            annualized_return=sic.annualized_return if sic else 0.0,
            mddd_s_years=sic.max_drawdown_duration_years if sic else 0.0,
            max_drawdown_pct=sic.max_drawdown_pct if sic else 0.0,
            f_score=result.f_score or 0.0,
            n_observations=result.n_observations,
            n_years=result.n_years,
        )

        # SIC efficiency: E_A / R_A (return per unit of annualized risk)
        ca.sic_efficiency = _safe_ratio(ca.annualized_return, ca.annualized_risk)

        # Drawdown resilience: inverse MDDD_S (higher = more resilient)
        ca.drawdown_resilience = 1.0 / ca.mddd_s_years if ca.mddd_s_years > 0 else 0.0

        constituents.append(ca)

    n = len(constituents)

    # Step 2: Compute S_Omega-weighted benchmark
    # Weights proportional to S_Omega (only positive S_Omega assets contribute)
    positive_s_omega = [c for c in constituents if c.s_omega > 0]
    total_s_omega = sum(c.s_omega for c in positive_s_omega) or 1.0

    for c in constituents:
        c.benchmark_weight = max(c.s_omega, 0.0) / total_s_omega

    benchmark = SectorBenchmark(
        n_constituents=n,
        benchmark_s_omega=sum(c.s_omega * c.benchmark_weight for c in constituents),
        benchmark_efficiency=sum(c.sic_efficiency * c.benchmark_weight for c in constituents),
        benchmark_return=sum(c.annualized_return * c.benchmark_weight for c in constituents),
        benchmark_risk=sum(c.annualized_risk * c.benchmark_weight for c in constituents),
        benchmark_mddd_s=sum(c.mddd_s_years * c.benchmark_weight for c in constituents),
        benchmark_f_score=sum(c.f_score * c.benchmark_weight for c in constituents),
    )

    # Sector envelope
    s_omegas = [c.s_omega for c in constituents]
    returns = [c.annualized_return for c in constituents]
    risks = [c.annualized_risk for c in constituents]
    mddds = [c.mddd_s_years for c in constituents]

    benchmark.min_s_omega = min(s_omegas)
    benchmark.max_s_omega = max(s_omegas)
    benchmark.min_return = min(returns)
    benchmark.max_return = max(returns)
    benchmark.min_risk = min(risks)
    benchmark.max_risk = max(risks)
    benchmark.min_mddd_s = min(mddds)
    benchmark.max_mddd_s = max(mddds)

    benchmark.s_omega_spread = benchmark.max_s_omega - benchmark.min_s_omega
    benchmark.return_spread = benchmark.max_return - benchmark.min_return
    benchmark.risk_spread = benchmark.max_risk - benchmark.min_risk

    # Herfindahl concentration index
    weights = [c.benchmark_weight for c in constituents]
    benchmark.herfindahl = sum(w ** 2 for w in weights)
    benchmark.effective_n = 1.0 / benchmark.herfindahl if benchmark.herfindahl > 0 else n

    # Step 3: Relative value analysis (spreads vs benchmark)
    for c in constituents:
        c.s_omega_spread = c.s_omega - benchmark.benchmark_s_omega
        c.efficiency_spread = c.sic_efficiency - benchmark.benchmark_efficiency
        c.return_spread = c.annualized_return - benchmark.benchmark_return
        c.risk_spread = c.annualized_risk - benchmark.benchmark_risk

    # Step 4: Compute ranks (1 = best)
    # S_Omega rank (higher is better)
    sorted_by_s_omega = sorted(constituents, key=lambda c: c.s_omega, reverse=True)
    for i, c in enumerate(sorted_by_s_omega):
        c.s_omega_rank = i + 1
        c.s_omega_percentile = _percentile_rank(s_omegas, c.s_omega)

    # SIC efficiency rank (higher E_A/R_A is better)
    efficiencies = [c.sic_efficiency for c in constituents]
    sorted_by_eff = sorted(constituents, key=lambda c: c.sic_efficiency, reverse=True)
    for i, c in enumerate(sorted_by_eff):
        c.efficiency_rank = i + 1
        c.efficiency_percentile = _percentile_rank(efficiencies, c.sic_efficiency)

    # Drawdown resilience rank (higher is better = shorter MDDD_S)
    resiliences = [c.drawdown_resilience for c in constituents]
    sorted_by_dd = sorted(constituents, key=lambda c: c.drawdown_resilience, reverse=True)
    for i, c in enumerate(sorted_by_dd):
        c.drawdown_rank = i + 1
        c.drawdown_percentile = _percentile_rank(resiliences, c.drawdown_resilience)

    # Fundamental quality rank (higher F_i is better)
    f_scores = [c.f_score for c in constituents]
    sorted_by_fi = sorted(constituents, key=lambda c: c.f_score, reverse=True)
    for i, c in enumerate(sorted_by_fi):
        c.fundamental_rank = i + 1
        c.fundamental_percentile = _percentile_rank(f_scores, c.f_score)

    # Step 5: Composite Ranking Index (CRI)
    # Normalized rank score: (n - rank + 1) / n * 100 gives 100 for rank 1
    for c in constituents:
        rank_scores = {
            "s_omega": (n - c.s_omega_rank + 1) / n * 100.0,
            "sic_efficiency": (n - c.efficiency_rank + 1) / n * 100.0,
            "drawdown_resilience": (n - c.drawdown_rank + 1) / n * 100.0,
            "fundamental_quality": (n - c.fundamental_rank + 1) / n * 100.0,
        }
        c.cri_score = sum(
            rank_scores[dim] * weight
            for dim, weight in CRI_WEIGHTS.items()
        )

    # Assign CRI ranks
    sorted_by_cri = sorted(constituents, key=lambda c: c.cri_score, reverse=True)
    for i, c in enumerate(sorted_by_cri):
        c.cri_rank = i + 1

    # Step 6: Generate signals
    for c in constituents:
        if c.s_omega_spread > 0 and c.cri_rank <= max(1, n // 3):
            c.signal = "overweight"
        elif c.s_omega_spread < 0 or c.cri_rank > max(1, 2 * n // 3):
            c.signal = "underweight"
        else:
            c.signal = "equal"

    return BenchmarkAnalysis(
        benchmark=benchmark,
        constituents=constituents,
        generated_at=datetime.now().isoformat(),
    )


def export_benchmark(
    analysis: BenchmarkAnalysis,
    output_path: Path | None = None,
) -> Path:
    """Export benchmark analysis to JSON."""
    if output_path is None:
        output_path = get_settings().data_dir / "analysis" / "benchmark_results.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    bm = analysis.benchmark
    data = {
        "analysis": "Phase 3 — Benchmark & Index Development",
        "generated_at": analysis.generated_at,
        "benchmark": {
            "name": bm.name,
            "n_constituents": bm.n_constituents,
            "weighted_metrics": {
                "s_omega_pct": round(bm.benchmark_s_omega * 100, 4),
                "sic_efficiency": round(bm.benchmark_efficiency, 4),
                "annualized_return_pct": round(bm.benchmark_return * 100, 4),
                "annualized_risk_pct": round(bm.benchmark_risk * 100, 4),
                "mddd_s_years": round(bm.benchmark_mddd_s, 2),
                "f_score": round(bm.benchmark_f_score, 2),
            },
            "sector_envelope": {
                "s_omega_range_pct": [
                    round(bm.min_s_omega * 100, 4),
                    round(bm.max_s_omega * 100, 4),
                ],
                "return_range_pct": [
                    round(bm.min_return * 100, 4),
                    round(bm.max_return * 100, 4),
                ],
                "risk_range_pct": [
                    round(bm.min_risk * 100, 4),
                    round(bm.max_risk * 100, 4),
                ],
                "mddd_s_range_years": [
                    round(bm.min_mddd_s, 2),
                    round(bm.max_mddd_s, 2),
                ],
            },
            "concentration": {
                "herfindahl": round(bm.herfindahl, 4),
                "effective_n": round(bm.effective_n, 2),
            },
        },
        "cri_weights": CRI_WEIGHTS,
        "constituents": [
            {
                "asset_id": c.asset_id,
                "asset_name": c.asset_name,
                "cri_rank": c.cri_rank,
                "cri_score": round(c.cri_score, 2),
                "signal": c.signal,
                "benchmark_weight_pct": round(c.benchmark_weight * 100, 2),
                "measures": {
                    "s_omega_pct": round(c.s_omega * 100, 4),
                    "omega_at_rf": round(c.omega_at_rf, 4),
                    "sic_efficiency": round(c.sic_efficiency, 4),
                    "annualized_return_pct": round(c.annualized_return * 100, 4),
                    "annualized_risk_pct": round(c.annualized_risk * 100, 4),
                    "mddd_s_years": round(c.mddd_s_years, 2),
                    "max_drawdown_pct": round(c.max_drawdown_pct * 100, 2),
                    "f_score": round(c.f_score, 2),
                },
                "relative_value": {
                    "s_omega_spread_pct": round(c.s_omega_spread * 100, 4),
                    "efficiency_spread": round(c.efficiency_spread, 4),
                    "return_spread_pct": round(c.return_spread * 100, 4),
                    "risk_spread_pct": round(c.risk_spread * 100, 4),
                },
                "ranks": {
                    "s_omega": c.s_omega_rank,
                    "sic_efficiency": c.efficiency_rank,
                    "drawdown_resilience": c.drawdown_rank,
                    "fundamental_quality": c.fundamental_rank,
                },
                "percentiles": {
                    "s_omega": round(c.s_omega_percentile, 1),
                    "sic_efficiency": round(c.efficiency_percentile, 1),
                    "drawdown_resilience": round(c.drawdown_percentile, 1),
                    "fundamental_quality": round(c.fundamental_percentile, 1),
                },
                "n_observations": c.n_observations,
                "n_years": round(c.n_years, 2),
            }
            for c in analysis.ranked
        ],
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)

    logger.info("Exported benchmark analysis to %s", output_path)
    return output_path
