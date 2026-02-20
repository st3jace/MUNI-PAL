"""Phase 5: Extended Risk Measures.

Integrates Phase 4 signal extraction into Phase 2's Omega framework to produce
signal-adjusted performance measures. This is the capstone of the Summers
methodology implementation.

Three extended Omega variants:

  1. Spectral Omega (Omega_S) — Adjusts the base Omega by the spectral
     concentration of returns. Assets with low spectral entropy (structured,
     predictable patterns) get an Omega premium; high-entropy (noise-dominated)
     assets get penalized. This captures the information content of the return
     series beyond the first four moments.

     Omega_S = Omega * (1 + alpha_S * (1 - H_norm))
       where H_norm = spectral entropy [0,1], alpha_S = spectral weight

  2. Wavelet Omega (Omega_W) — Adjusts Omega by the trend-to-noise energy
     ratio from wavelet decomposition. Assets with high trend energy relative
     to noise have a more reliable performance trajectory.

     Omega_W = Omega * (1 + alpha_W * log(1 + T/N))
       where T/N = trend energy / noise energy, alpha_W = wavelet weight

  3. Dynamic Omega (Omega_D) — Adjusts Omega by DMD mode stability. Assets
     whose dominant modes are stable (|eigenvalue| <= 1) and have low growth
     rates (mean-reverting) get a resilience premium.

     Omega_D = Omega * (1 + alpha_D * (f_stable - 0.5))
       where f_stable = fraction of stable modes (energy-weighted)

The final Integrated Risk Score (IRS) combines all three:

  IRS = w_S * Omega_S + w_W * Omega_W + w_D * Omega_D

This produces the definitive ranking for the investable universe.

Summers Paper 2, Section 5: "The functional extension preserves the
intuitive interpretation while incorporating the complete spectral
structure of the underlying stochastic process."
"""
from __future__ import annotations

import json
import logging
import math
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

from ..config import get_settings
from .benchmark import ConstituentAnalysis
from .hilbert import HilbertAnalysis, SpectralAnalysis, WaveletAnalysis, DMDAnalysis
from .omega import SOmegaResult

logger = logging.getLogger("bond_os_extractor.analysis.extended_risk")

# Signal adjustment parameters
ALPHA_SPECTRAL = 0.25    # Spectral entropy adjustment strength
ALPHA_WAVELET = 0.15     # Wavelet trend/noise adjustment strength
ALPHA_DYNAMIC = 0.10     # DMD stability adjustment strength

# Integration weights for IRS
IRS_WEIGHTS = {
    "spectral_omega": 0.40,
    "wavelet_omega": 0.35,
    "dynamic_omega": 0.25,
}


@dataclass
class ExtendedOmega:
    """Extended Omega measures for one asset."""
    asset_id: str
    asset_name: str
    asset_type: str = "equity"    # "equity" or "bond"

    # Base measures (from Phase 2)
    base_omega: float = 0.0       # Omega(r_f) from Phase 2
    base_s_omega: float = 0.0     # S_Omega from Phase 2

    # Spectral Omega
    spectral_entropy: float = 0.0  # H_norm [0,1]
    spectral_snr_db: float = 0.0
    spectral_adjustment: float = 0.0  # (1 + alpha * (1 - H))
    spectral_omega: float = 0.0      # Omega_S

    # Wavelet Omega
    trend_energy_pct: float = 0.0
    noise_energy_pct: float = 0.0
    trend_to_noise: float = 0.0
    wavelet_adjustment: float = 0.0   # (1 + alpha * log(1 + T/N))
    wavelet_omega: float = 0.0        # Omega_W

    # Dynamic Omega
    stable_fraction: float = 0.0      # Energy-weighted fraction of stable modes
    dominant_period_days: float = 0.0  # Period of strongest DMD mode
    dynamic_adjustment: float = 0.0   # (1 + alpha * (f_stable - 0.5))
    dynamic_omega: float = 0.0        # Omega_D

    # Integrated Risk Score
    irs: float = 0.0                  # Weighted combination of extended Omegas
    irs_rank: int = 0

    # Phase 1 & 3 context
    f_score: float = 0.0
    cri_score: float = 0.0
    cri_rank: int = 0

    # Overall signal assessment
    signal_quality: str = ""          # "strong" | "moderate" | "weak"


@dataclass
class ExtendedRiskAnalysis:
    """Complete Phase 5 analysis."""
    assets: list[ExtendedOmega] = field(default_factory=list)
    generated_at: str = ""

    # Universe-level summary
    avg_irs: float = 0.0
    best_irs_asset: str = ""
    signal_distribution: dict[str, int] = field(default_factory=dict)

    @property
    def ranked(self) -> list[ExtendedOmega]:
        return sorted(self.assets, key=lambda a: a.irs, reverse=True)


def compute_spectral_omega(
    base_omega: float,
    spectral: SpectralAnalysis | None,
    alpha: float = ALPHA_SPECTRAL,
) -> tuple[float, float]:
    """Compute Spectral Omega adjustment.

    Omega_S = Omega * (1 + alpha * (1 - H_norm))

    Low entropy (structured signal) → larger premium.
    High entropy (noise) → smaller or negative adjustment.

    Returns (spectral_omega, adjustment_factor).
    """
    if spectral is None or spectral.n_observations < 16:
        return base_omega, 1.0

    h = spectral.spectral_entropy  # [0, 1]
    # Signal premium: positive when H < 1 (some structure exists)
    adjustment = 1.0 + alpha * (1.0 - h)
    return base_omega * adjustment, adjustment


def compute_wavelet_omega(
    base_omega: float,
    wavelet: WaveletAnalysis | None,
    alpha: float = ALPHA_WAVELET,
) -> tuple[float, float]:
    """Compute Wavelet Omega adjustment.

    Omega_W = Omega * (1 + alpha * log(1 + T/N))

    High trend-to-noise → logarithmic premium (diminishing returns).
    Low trend-to-noise → minimal adjustment.

    Returns (wavelet_omega, adjustment_factor).
    """
    if wavelet is None or wavelet.n_levels == 0:
        return base_omega, 1.0

    t_n = wavelet.trend_to_noise
    if t_n <= 0 or not math.isfinite(t_n):
        t_n = 0.0

    adjustment = 1.0 + alpha * math.log(1.0 + t_n)
    return base_omega * adjustment, adjustment


def compute_dynamic_omega(
    base_omega: float,
    dmd: DMDAnalysis | None,
    asset_id: str,
    alpha: float = ALPHA_DYNAMIC,
) -> tuple[float, float, float, float]:
    """Compute Dynamic Omega adjustment from DMD mode stability.

    Omega_D = Omega * (1 + alpha * (f_stable - 0.5))

    f_stable = energy-weighted fraction of stable (|lambda| <= 1) modes.
    When f_stable > 0.5, the system is predominantly mean-reverting → premium.
    When f_stable < 0.5, growing/unstable modes dominate → penalty.

    Returns (dynamic_omega, adjustment, stable_fraction, dominant_period).
    """
    if dmd is None or dmd.n_modes == 0:
        return base_omega, 1.0, 0.5, 0.0

    # Energy-weighted stable fraction
    total_energy = sum(m.energy_fraction for m in dmd.modes) or 1.0
    stable_energy = sum(
        m.energy_fraction for m in dmd.modes if m.is_stable
    )
    f_stable = stable_energy / total_energy

    # Dominant period for this asset (highest energy mode)
    dominant_period = 0.0
    if dmd.modes:
        dominant_period = dmd.modes[0].period_days

    adjustment = 1.0 + alpha * (f_stable - 0.5)
    return base_omega * adjustment, adjustment, f_stable, dominant_period


def analyze_extended_risk(
    s_omega_results: list[SOmegaResult],
    hilbert: HilbertAnalysis,
    constituents: list[ConstituentAnalysis] | None = None,
) -> ExtendedRiskAnalysis:
    """Run Phase 5: Extended Risk Measures on the investable universe.

    Combines Phase 2 (S_Omega), Phase 3 (CRI), and Phase 4 (Hilbert)
    into the final Integrated Risk Score.
    """
    analysis = ExtendedRiskAnalysis(generated_at=datetime.now().isoformat())

    # Build CRI lookup from Phase 3
    cri_lookup: dict[str, ConstituentAnalysis] = {}
    if constituents:
        for c in constituents:
            cri_lookup[c.asset_id] = c

    for result in s_omega_results:
        aid = result.asset_id

        eo = ExtendedOmega(
            asset_id=aid,
            asset_name=result.asset_name,
            asset_type=getattr(result, "asset_type", "equity"),
            base_omega=result.omega_at_rf,
            base_s_omega=result.s_omega,
            f_score=result.f_score or 0.0,
        )

        # Phase 3 context
        if aid in cri_lookup:
            eo.cri_score = cri_lookup[aid].cri_score
            eo.cri_rank = cri_lookup[aid].cri_rank

        # Spectral Omega
        spectral = hilbert.spectral.get(aid)
        eo.spectral_omega, eo.spectral_adjustment = compute_spectral_omega(
            eo.base_omega, spectral,
        )
        if spectral:
            eo.spectral_entropy = spectral.spectral_entropy
            eo.spectral_snr_db = spectral.snr_db

        # Wavelet Omega
        wavelet = hilbert.wavelet.get(aid)
        eo.wavelet_omega, eo.wavelet_adjustment = compute_wavelet_omega(
            eo.base_omega, wavelet,
        )
        if wavelet:
            eo.trend_energy_pct = wavelet.trend_energy_fraction * 100
            eo.noise_energy_pct = wavelet.noise_energy_fraction * 100
            eo.trend_to_noise = wavelet.trend_to_noise

        # Dynamic Omega
        dmd = hilbert.dmd
        eo.dynamic_omega, eo.dynamic_adjustment, eo.stable_fraction, eo.dominant_period_days = (
            compute_dynamic_omega(eo.base_omega, dmd, aid)
        )

        # Integrated Risk Score
        eo.irs = (
            IRS_WEIGHTS["spectral_omega"] * eo.spectral_omega
            + IRS_WEIGHTS["wavelet_omega"] * eo.wavelet_omega
            + IRS_WEIGHTS["dynamic_omega"] * eo.dynamic_omega
        )

        # Signal quality assessment
        if eo.spectral_entropy < 0.85 and eo.trend_to_noise > 0.05:
            eo.signal_quality = "strong"
        elif eo.spectral_entropy < 0.95 and eo.trend_to_noise > 0.01:
            eo.signal_quality = "moderate"
        else:
            eo.signal_quality = "weak"

        analysis.assets.append(eo)

    # Assign IRS ranks
    sorted_by_irs = sorted(analysis.assets, key=lambda a: a.irs, reverse=True)
    for i, eo in enumerate(sorted_by_irs):
        eo.irs_rank = i + 1

    # Universe summary
    if analysis.assets:
        analysis.avg_irs = sum(a.irs for a in analysis.assets) / len(analysis.assets)
        analysis.best_irs_asset = sorted_by_irs[0].asset_id if sorted_by_irs else ""
        analysis.signal_distribution = {
            "strong": sum(1 for a in analysis.assets if a.signal_quality == "strong"),
            "moderate": sum(1 for a in analysis.assets if a.signal_quality == "moderate"),
            "weak": sum(1 for a in analysis.assets if a.signal_quality == "weak"),
        }

    return analysis


def export_extended_risk(
    analysis: ExtendedRiskAnalysis,
    output_path: Path | None = None,
) -> Path:
    """Export Phase 5 results to JSON."""
    if output_path is None:
        output_path = get_settings().data_dir / "analysis" / "extended_risk_results.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "analysis": "Phase 5 -- Extended Risk Measures (Summers Integration)",
        "generated_at": analysis.generated_at,
        "parameters": {
            "alpha_spectral": ALPHA_SPECTRAL,
            "alpha_wavelet": ALPHA_WAVELET,
            "alpha_dynamic": ALPHA_DYNAMIC,
            "irs_weights": IRS_WEIGHTS,
        },
        "summary": {
            "n_assets": len(analysis.assets),
            "avg_irs": round(analysis.avg_irs, 4),
            "best_irs_asset": analysis.best_irs_asset,
            "signal_distribution": analysis.signal_distribution,
        },
        "assets": [
            {
                "asset_id": a.asset_id,
                "asset_name": a.asset_name,
                "asset_type": a.asset_type,
                "irs": round(a.irs, 4),
                "irs_rank": a.irs_rank,
                "signal_quality": a.signal_quality,
                "base_measures": {
                    "omega_at_rf": round(a.base_omega, 4),
                    "s_omega_pct": round(a.base_s_omega * 100, 4),
                    "f_score": round(a.f_score, 2),
                    "cri_score": round(a.cri_score, 2),
                    "cri_rank": a.cri_rank,
                },
                "spectral_omega": {
                    "omega_s": round(a.spectral_omega, 4),
                    "adjustment": round(a.spectral_adjustment, 4),
                    "entropy": round(a.spectral_entropy, 4),
                    "snr_db": round(a.spectral_snr_db, 2),
                },
                "wavelet_omega": {
                    "omega_w": round(a.wavelet_omega, 4),
                    "adjustment": round(a.wavelet_adjustment, 4),
                    "trend_energy_pct": round(a.trend_energy_pct, 2),
                    "noise_energy_pct": round(a.noise_energy_pct, 2),
                    "trend_to_noise": round(a.trend_to_noise, 4),
                },
                "dynamic_omega": {
                    "omega_d": round(a.dynamic_omega, 4),
                    "adjustment": round(a.dynamic_adjustment, 4),
                    "stable_fraction": round(a.stable_fraction, 4),
                    "dominant_period_days": round(a.dominant_period_days, 1)
                    if a.dominant_period_days < 1e6 else "inf",
                },
            }
            for a in analysis.ranked
        ],
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)

    logger.info("Exported extended risk analysis to %s", output_path)
    return output_path
