"""Phase 4: Hilbert Space Signal Extraction.

Implements the signal decomposition framework from Summers' "Standard Model
of Complex Economic Systems" — treating return series as elements of L^2[0,T]
(the Hilbert space of square-integrable functions on a time interval).

Three complementary decomposition methods:

  1. FFT Spectral Analysis — Fourier decomposition into frequency components.
     Identifies dominant cycles (periodicity), spectral concentration, and
     signal-to-noise ratio. Maps the return series from the time domain to
     the frequency domain.

  2. DWT/MRA Wavelet Decomposition — Multi-Resolution Analysis using discrete
     wavelets. Separates the return series into scale-specific components:
       - Approximation (trend): low-frequency, long-horizon signal
       - Detail levels: cycle components at progressively shorter horizons
       - Finest detail: high-frequency noise / microstructure
     Unlike FFT, wavelets provide time-frequency localization — they can
     detect when a cycle starts and stops, not just its frequency.

  3. DMD (Dynamic Mode Decomposition) — Data-driven extraction of coherent
     spatiotemporal patterns from multivariate return data. Approximates the
     Koopman operator, finding linear dynamics that best describe the nonlinear
     system. Each DMD mode has a frequency, growth/decay rate, and spatial
     structure across assets.

The extracted signals feed into Phase 5 (Extended Risk Measures) where they
modify the base Omega ratio via spectral, wavelet, and dynamic adjustments.

Summers Paper 2, Section 5: "The functional Omega ratio extends the
discrete formulation to continuous signal spaces, enabling spectral
decomposition of the risk-return tradeoff."
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
from .return_series import ReturnSeries

logger = logging.getLogger("bond_os_extractor.analysis.hilbert")


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class SpectralPeak:
    """A dominant frequency component from FFT analysis."""
    frequency: float          # cycles per trading day
    period_days: float        # trading days per cycle
    period_label: str         # human-readable: "5.2 months", "3 weeks"
    power: float              # spectral power (magnitude squared)
    power_fraction: float     # fraction of total spectral power
    phase: float              # phase angle (radians)


@dataclass
class SpectralAnalysis:
    """Complete FFT spectral decomposition of one return series."""
    asset_id: str
    n_observations: int

    # Summary statistics
    spectral_entropy: float = 0.0     # Normalized Shannon entropy (0=pure tone, 1=white noise)
    snr_db: float = 0.0               # Signal-to-noise ratio in dB
    dominant_period_days: float = 0.0  # Period of strongest frequency component

    # Top peaks (sorted by power)
    peaks: list[SpectralPeak] = field(default_factory=list)

    # Full spectrum (for plotting / export)
    frequencies: list[float] = field(default_factory=list)
    power_spectrum: list[float] = field(default_factory=list)


@dataclass
class WaveletLevel:
    """One level of the wavelet multi-resolution decomposition."""
    level: int
    name: str                 # "D1" (finest detail) ... "Dn", "An" (approximation)
    scale_label: str          # "2-4 days", "4-8 days", etc.
    energy: float             # sum of squared coefficients
    energy_fraction: float    # fraction of total signal energy
    n_coefficients: int
    variance: float = 0.0     # variance of coefficients at this level
    mean: float = 0.0


@dataclass
class WaveletAnalysis:
    """Complete DWT/MRA wavelet decomposition of one return series."""
    asset_id: str
    wavelet: str              # wavelet family used (e.g., "db4")
    n_levels: int
    n_observations: int

    levels: list[WaveletLevel] = field(default_factory=list)

    # Trend signal (approximation coefficients)
    trend_energy_fraction: float = 0.0   # energy in lowest frequency band
    noise_energy_fraction: float = 0.0   # energy in highest frequency band

    # Derived signal quality
    trend_to_noise: float = 0.0          # trend energy / noise energy


@dataclass
class DMDMode:
    """One Dynamic Mode Decomposition mode."""
    mode_index: int
    frequency: float          # cycles per trading day
    period_days: float        # trading days per cycle
    growth_rate: float        # per-period growth/decay rate (>0 = growing)
    amplitude: float          # mode amplitude (norm of spatial vector)
    energy_fraction: float    # fraction of total reconstruction energy

    # Spatial structure: how each asset participates in this mode
    spatial_weights: dict[str, float] = field(default_factory=dict)

    # Stability
    is_stable: bool = True    # |eigenvalue| <= 1


@dataclass
class DMDAnalysis:
    """Complete DMD/Koopman analysis of multivariate return data."""
    asset_ids: list[str]
    n_modes: int
    n_observations: int

    modes: list[DMDMode] = field(default_factory=list)

    # Reconstruction quality
    reconstruction_error: float = 0.0  # Frobenius norm ratio
    n_stable_modes: int = 0
    n_growing_modes: int = 0


@dataclass
class HilbertAnalysis:
    """Complete Phase 4 signal extraction for the investable universe."""
    spectral: dict[str, SpectralAnalysis] = field(default_factory=dict)
    wavelet: dict[str, WaveletAnalysis] = field(default_factory=dict)
    dmd: DMDAnalysis | None = None
    generated_at: str = ""


# ---------------------------------------------------------------------------
# 1. FFT Spectral Analysis
# ---------------------------------------------------------------------------

def _period_to_label(period_days: float) -> str:
    """Convert period in trading days to human-readable label."""
    if period_days >= 252:
        years = period_days / 252
        return f"{years:.1f} years"
    elif period_days >= 21:
        months = period_days / 21
        return f"{months:.1f} months"
    elif period_days >= 5:
        weeks = period_days / 5
        return f"{weeks:.1f} weeks"
    else:
        return f"{period_days:.1f} days"


def compute_spectral_analysis(
    series: ReturnSeries,
    n_peaks: int = 10,
) -> SpectralAnalysis:
    """FFT spectral decomposition of a return series.

    Computes the power spectral density, identifies dominant frequencies,
    and calculates spectral entropy (signal complexity measure).

    Spectral entropy near 0 → signal dominated by a few frequencies (predictable).
    Spectral entropy near 1 → energy spread uniformly (white noise, unpredictable).
    """
    if series.n < 16:
        return SpectralAnalysis(asset_id=series.asset_id, n_observations=series.n)

    returns = np.array(series.returns, dtype=np.float64)

    # Demean the series (remove DC component)
    returns = returns - returns.mean()

    # Apply Hann window to reduce spectral leakage
    window = np.hanning(len(returns))
    windowed = returns * window

    # FFT
    n = len(windowed)
    fft_vals = np.fft.rfft(windowed)
    freqs = np.fft.rfftfreq(n, d=1.0)  # d=1 trading day

    # Power spectral density (magnitude squared, normalized)
    power = np.abs(fft_vals) ** 2
    # Skip DC component (index 0)
    freqs = freqs[1:]
    power = power[1:]

    if power.sum() == 0:
        return SpectralAnalysis(asset_id=series.asset_id, n_observations=series.n)

    # Normalize power to get probability distribution for entropy
    power_norm = power / power.sum()

    # Spectral entropy (Shannon entropy, normalized to [0,1])
    # H = -sum(p * log(p)) / log(N)
    nonzero = power_norm > 0
    entropy_raw = -np.sum(power_norm[nonzero] * np.log(power_norm[nonzero]))
    max_entropy = np.log(len(power_norm)) if len(power_norm) > 1 else 1.0
    spectral_entropy = entropy_raw / max_entropy if max_entropy > 0 else 0.0

    # Signal-to-noise ratio
    # Signal = top 10% of spectral power; noise = bottom 90%
    sorted_power = np.sort(power)[::-1]
    n_signal = max(1, len(sorted_power) // 10)
    signal_power = sorted_power[:n_signal].sum()
    noise_power = sorted_power[n_signal:].sum()
    snr = signal_power / noise_power if noise_power > 0 else float("inf")
    snr_db = 10 * np.log10(snr) if snr > 0 and np.isfinite(snr) else 0.0

    # Find dominant peaks
    peak_indices = np.argsort(power)[::-1][:n_peaks]
    peaks: list[SpectralPeak] = []
    total_power = power.sum()

    for idx in peak_indices:
        freq = float(freqs[idx])
        if freq <= 0:
            continue
        period = 1.0 / freq
        peaks.append(SpectralPeak(
            frequency=freq,
            period_days=period,
            period_label=_period_to_label(period),
            power=float(power[idx]),
            power_fraction=float(power[idx] / total_power),
            phase=float(np.angle(fft_vals[idx + 1])),  # +1 for DC offset
        ))

    dominant_period = peaks[0].period_days if peaks else 0.0

    return SpectralAnalysis(
        asset_id=series.asset_id,
        n_observations=series.n,
        spectral_entropy=float(spectral_entropy),
        snr_db=float(snr_db),
        dominant_period_days=dominant_period,
        peaks=peaks,
        frequencies=[float(f) for f in freqs],
        power_spectrum=[float(p) for p in power],
    )


# ---------------------------------------------------------------------------
# 2. DWT / MRA Wavelet Decomposition
# ---------------------------------------------------------------------------

def _wavelet_decompose(data: np.ndarray, wavelet: str, max_level: int | None = None):
    """Manual Haar/db4 wavelet decomposition without pywt.

    Uses scipy's signal processing for filter-based decomposition.
    Falls back to a simple Haar implementation if needed.
    """
    from scipy.signal import decimate

    n = len(data)
    if max_level is None:
        max_level = int(np.floor(np.log2(n))) - 1
        max_level = min(max_level, 8)  # Cap at 8 levels

    # Haar wavelet filters
    if wavelet == "haar":
        lo = np.array([1, 1]) / np.sqrt(2)  # Scaling (lowpass)
        hi = np.array([1, -1]) / np.sqrt(2)  # Wavelet (highpass)
    else:
        # Daubechies-4 coefficients
        h0 = (1 + np.sqrt(3)) / (4 * np.sqrt(2))
        h1 = (3 + np.sqrt(3)) / (4 * np.sqrt(2))
        h2 = (3 - np.sqrt(3)) / (4 * np.sqrt(2))
        h3 = (1 - np.sqrt(3)) / (4 * np.sqrt(2))
        lo = np.array([h0, h1, h2, h3])
        hi = np.array([h3, -h2, h1, -h0])

    details = []
    approx = data.copy()

    for level in range(max_level):
        n_cur = len(approx)
        if n_cur < 2 * len(lo):
            break

        # Convolve and downsample by 2
        detail_full = np.convolve(approx, hi, mode='full')
        approx_full = np.convolve(approx, lo, mode='full')

        # Downsample by 2
        detail_ds = detail_full[1::2][:n_cur // 2]
        approx_ds = approx_full[1::2][:n_cur // 2]

        details.append(detail_ds)
        approx = approx_ds

    return approx, details


def compute_wavelet_analysis(
    series: ReturnSeries,
    wavelet: str = "db4",
) -> WaveletAnalysis:
    """Multi-Resolution Analysis via discrete wavelet transform.

    Decomposes the return series into scale-specific components:
      - D1 (finest detail): 2-4 day cycles — market microstructure / noise
      - D2: 4-8 day cycles — weekly patterns
      - D3: 8-16 day cycles — bi-weekly / options expiration
      - D4: 16-32 day cycles — monthly cycles
      - D5: 32-64 day cycles — quarterly patterns
      - D6: 64-128 day cycles — semi-annual
      - D7: 128-256 day cycles — annual cycles
      - A7 (approximation): > 256 days — long-term trend

    Energy distribution across levels reveals whether returns are driven
    by trend (low-frequency) or noise (high-frequency).
    """
    if series.n < 32:
        return WaveletAnalysis(
            asset_id=series.asset_id, wavelet=wavelet,
            n_levels=0, n_observations=series.n,
        )

    returns = np.array(series.returns, dtype=np.float64)

    # Decompose
    approx, details = _wavelet_decompose(returns, wavelet)
    n_levels = len(details)

    # Compute energy at each level
    total_energy = np.sum(returns ** 2)
    if total_energy == 0:
        total_energy = 1.0  # Avoid division by zero

    levels: list[WaveletLevel] = []

    # Detail levels (D1 = finest, Dn = coarsest detail)
    scale_ranges = [
        (2, 4), (4, 8), (8, 16), (16, 32), (32, 64),
        (64, 128), (128, 256), (256, 512), (512, 1024),
    ]

    for i, detail in enumerate(details):
        level_num = i + 1
        energy = float(np.sum(detail ** 2))
        lo, hi = scale_ranges[i] if i < len(scale_ranges) else (2 ** (i + 1), 2 ** (i + 2))
        levels.append(WaveletLevel(
            level=level_num,
            name=f"D{level_num}",
            scale_label=f"{lo}-{hi} days",
            energy=energy,
            energy_fraction=energy / total_energy,
            n_coefficients=len(detail),
            variance=float(np.var(detail)) if len(detail) > 0 else 0.0,
            mean=float(np.mean(detail)) if len(detail) > 0 else 0.0,
        ))

    # Approximation level (trend)
    approx_energy = float(np.sum(approx ** 2))
    lo_bound = 2 ** (n_levels + 1) if n_levels < len(scale_ranges) else scale_ranges[-1][1]
    levels.append(WaveletLevel(
        level=n_levels + 1,
        name=f"A{n_levels}",
        scale_label=f">{lo_bound} days (trend)",
        energy=approx_energy,
        energy_fraction=approx_energy / total_energy,
        n_coefficients=len(approx),
        variance=float(np.var(approx)) if len(approx) > 0 else 0.0,
        mean=float(np.mean(approx)) if len(approx) > 0 else 0.0,
    ))

    # Trend vs noise energy
    trend_frac = approx_energy / total_energy
    noise_frac = levels[0].energy_fraction if levels else 0.0  # D1 = noise
    trend_to_noise = trend_frac / noise_frac if noise_frac > 0 else float("inf")

    return WaveletAnalysis(
        asset_id=series.asset_id,
        wavelet=wavelet,
        n_levels=n_levels,
        n_observations=series.n,
        levels=levels,
        trend_energy_fraction=trend_frac,
        noise_energy_fraction=noise_frac,
        trend_to_noise=float(trend_to_noise) if np.isfinite(trend_to_noise) else 0.0,
    )


# ---------------------------------------------------------------------------
# 3. DMD / Koopman Operator
# ---------------------------------------------------------------------------

def compute_dmd_analysis(
    series_list: list[ReturnSeries],
    n_modes: int = 10,
    n_delays: int = 5,
) -> DMDAnalysis:
    """Dynamic Mode Decomposition of multivariate return data.

    Uses time-delay embedding on cumulative log returns (wealth paths) to
    enrich the state space before extracting DMD modes. Raw daily returns
    are approximately white noise and yield degenerate DMD — cumulative
    returns carry the dynamical structure of the price process.

    The delay embedding X_d = [x_t, x_{t-1}, ..., x_{t-d}]^T maps each
    asset's 1D trajectory into a (d+1)-dimensional state, giving the SVD
    enough structure to identify coherent modes.

    Eigenvalues of the reduced operator A_tilde give mode frequencies
    (oscillation period) and growth rates (trend/decay). Eigenvectors
    give spatial structure (how each asset participates in each mode).
    """
    if len(series_list) < 2:
        return DMDAnalysis(
            asset_ids=[s.asset_id for s in series_list],
            n_modes=0,
            n_observations=0,
        )

    asset_ids = [s.asset_id for s in series_list]

    # Find common dates
    date_sets = [set(s.dates) for s in series_list]
    common_dates = sorted(set.intersection(*date_sets))

    if len(common_dates) < 30 + n_delays:
        logger.warning(
            "Insufficient common dates for DMD (%d). Need at least %d.",
            len(common_dates), 30 + n_delays,
        )
        return DMDAnalysis(
            asset_ids=asset_ids, n_modes=0,
            n_observations=len(common_dates),
        )

    n_assets = len(series_list)
    n_time = len(common_dates)

    # Build cumulative log-return matrix (wealth paths)
    date_lookups = []
    for s in series_list:
        lookup = dict(zip(s.dates, s.returns))
        date_lookups.append(lookup)

    raw_returns = np.zeros((n_assets, n_time))
    for i, lookup in enumerate(date_lookups):
        for j, date in enumerate(common_dates):
            raw_returns[i, j] = lookup.get(date, 0.0)

    # Cumulative log returns: log(wealth) path
    cum_log = np.cumsum(np.log1p(raw_returns), axis=1)

    # Time-delay embedding: stack [x_t, x_{t-1}, ..., x_{t-d}] per asset
    # This creates a (n_assets * (n_delays+1)) x (n_time - n_delays) matrix
    n_embedded = n_time - n_delays
    n_state = n_assets * (n_delays + 1)

    X_delay = np.zeros((n_state, n_embedded))
    for d in range(n_delays + 1):
        row_start = d * n_assets
        row_end = (d + 1) * n_assets
        col_start = n_delays - d
        X_delay[row_start:row_end, :] = cum_log[:, col_start:col_start + n_embedded]

    # Split into X and X'
    X = X_delay[:, :-1]
    Xp = X_delay[:, 1:]

    # SVD of X
    try:
        U, S, Vt = np.linalg.svd(X, full_matrices=False)
    except np.linalg.LinAlgError:
        logger.warning("SVD failed for DMD computation")
        return DMDAnalysis(asset_ids=asset_ids, n_modes=0, n_observations=n_time)

    # Truncate: keep modes with significant singular values
    energy_threshold = 0.999  # Keep 99.9% of energy
    total_sv_energy = np.sum(S ** 2)
    cum_energy = np.cumsum(S ** 2) / total_sv_energy
    r = int(np.searchsorted(cum_energy, energy_threshold)) + 1
    r = min(r, n_modes, len(S))
    r = max(r, 1)

    U_r = U[:, :r]
    S_inv = np.diag(1.0 / S[:r])
    Vt_r = Vt[:r, :]

    # DMD operator: A_tilde = U_r^T X' V_r S_r^{-1}
    A_tilde = U_r.T @ Xp @ Vt_r.T @ S_inv

    # Eigendecomposition
    try:
        eigenvalues, eigvecs_tilde = np.linalg.eig(A_tilde)
    except np.linalg.LinAlgError:
        logger.warning("Eigendecomposition failed for DMD")
        return DMDAnalysis(asset_ids=asset_ids, n_modes=0, n_observations=n_time)

    # Project eigenvectors back to full (delay-embedded) space
    Phi_full = U_r @ eigvecs_tilde  # (n_state x r)

    # Extract spatial weights from the first delay block (current time)
    Phi_current = Phi_full[:n_assets, :]  # Original asset space

    # Mode amplitudes from initial condition
    x0 = X_delay[:, 0]
    try:
        b = np.linalg.lstsq(Phi_full, x0, rcond=None)[0]
    except np.linalg.LinAlgError:
        b = np.ones(r)

    # Reconstruction error on cumulative returns
    X_recon = np.zeros_like(X_delay)
    for k in range(X_delay.shape[1]):
        X_recon[:, k] = np.real(Phi_full @ np.diag(eigenvalues ** k) @ b)
    recon_err = np.linalg.norm(X_delay - X_recon, 'fro')
    total_norm = np.linalg.norm(X_delay, 'fro')
    rel_error = recon_err / total_norm if total_norm > 0 else 1.0

    # Build DMDMode objects
    total_mode_energy = np.sum(np.abs(b) ** 2) or 1.0
    modes: list[DMDMode] = []

    for i in range(r):
        lam = eigenvalues[i]
        lam_abs = abs(lam)

        omega = float(np.angle(lam))
        frequency = abs(omega) / (2 * np.pi)
        period = 1.0 / frequency if frequency > 1e-10 else float("inf")
        growth_rate = float(np.log(lam_abs)) if lam_abs > 0 else -float("inf")
        is_stable = lam_abs <= 1.0 + 1e-10

        # Spatial weights from current-time block
        mode_vec = Phi_current[:, i]
        spatial = {}
        norm = np.linalg.norm(mode_vec) or 1.0
        for j, aid in enumerate(asset_ids):
            spatial[aid] = float(np.abs(mode_vec[j]) / norm)

        amplitude = float(np.abs(b[i]))
        energy_frac = float(np.abs(b[i]) ** 2 / total_mode_energy)

        modes.append(DMDMode(
            mode_index=i,
            frequency=frequency,
            period_days=period,
            growth_rate=growth_rate,
            amplitude=amplitude,
            energy_fraction=energy_frac,
            spatial_weights=spatial,
            is_stable=is_stable,
        ))

    modes.sort(key=lambda m: m.energy_fraction, reverse=True)
    for i, m in enumerate(modes):
        m.mode_index = i

    n_stable = sum(1 for m in modes if m.is_stable)
    n_growing = sum(1 for m in modes if not m.is_stable)

    return DMDAnalysis(
        asset_ids=asset_ids,
        n_modes=len(modes),
        n_observations=n_time,
        modes=modes,
        reconstruction_error=float(rel_error),
        n_stable_modes=n_stable,
        n_growing_modes=n_growing,
    )


# ---------------------------------------------------------------------------
# Universe-level analysis
# ---------------------------------------------------------------------------

def analyze_signals(
    series_list: list[ReturnSeries],
    market_series: ReturnSeries | None = None,
    wavelet: str = "db4",
    n_dmd_modes: int = 10,
) -> HilbertAnalysis:
    """Run complete Phase 4 signal extraction on the investable universe.

    For each asset: FFT spectral analysis + wavelet decomposition.
    Across all assets: DMD/Koopman multivariate analysis.
    """
    result = HilbertAnalysis(generated_at=datetime.now().isoformat())

    all_series = list(series_list)
    if market_series is not None:
        all_series.append(market_series)

    # Per-asset analysis
    for series in all_series:
        logger.info("Spectral analysis: %s (%d obs)", series.asset_id, series.n)
        result.spectral[series.asset_id] = compute_spectral_analysis(series)

        logger.info("Wavelet analysis: %s", series.asset_id)
        result.wavelet[series.asset_id] = compute_wavelet_analysis(series, wavelet)

    # Cross-asset DMD (equity assets only, exclude market benchmark)
    equity_series = [s for s in series_list if s.asset_type == "equity"]
    if len(equity_series) >= 2:
        logger.info("DMD analysis: %d assets", len(equity_series))
        result.dmd = compute_dmd_analysis(equity_series, n_dmd_modes)

    return result


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

def export_hilbert(
    analysis: HilbertAnalysis,
    output_path: Path | None = None,
) -> Path:
    """Export Phase 4 signal extraction results to JSON."""
    if output_path is None:
        output_path = get_settings().data_dir / "analysis" / "hilbert_results.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    data: dict[str, Any] = {
        "analysis": "Phase 4 -- Hilbert Space Signal Extraction",
        "generated_at": analysis.generated_at,
        "spectral": {},
        "wavelet": {},
        "dmd": None,
    }

    # Spectral
    for aid, sa in analysis.spectral.items():
        data["spectral"][aid] = {
            "n_observations": sa.n_observations,
            "spectral_entropy": round(sa.spectral_entropy, 4),
            "snr_db": round(sa.snr_db, 2),
            "dominant_period_days": round(sa.dominant_period_days, 1),
            "dominant_period_label": _period_to_label(sa.dominant_period_days)
            if sa.dominant_period_days > 0 else "N/A",
            "peaks": [
                {
                    "period_days": round(p.period_days, 1),
                    "period_label": p.period_label,
                    "power_fraction_pct": round(p.power_fraction * 100, 2),
                    "frequency": round(p.frequency, 6),
                }
                for p in sa.peaks[:5]  # Top 5 only for export
            ],
        }

    # Wavelet
    for aid, wa in analysis.wavelet.items():
        data["wavelet"][aid] = {
            "wavelet": wa.wavelet,
            "n_levels": wa.n_levels,
            "n_observations": wa.n_observations,
            "trend_energy_pct": round(wa.trend_energy_fraction * 100, 2),
            "noise_energy_pct": round(wa.noise_energy_fraction * 100, 2),
            "trend_to_noise": round(wa.trend_to_noise, 4),
            "levels": [
                {
                    "name": lv.name,
                    "scale": lv.scale_label,
                    "energy_pct": round(lv.energy_fraction * 100, 2),
                    "n_coefficients": lv.n_coefficients,
                }
                for lv in wa.levels
            ],
        }

    # DMD
    if analysis.dmd and analysis.dmd.n_modes > 0:
        dmd = analysis.dmd
        data["dmd"] = {
            "asset_ids": dmd.asset_ids,
            "n_modes": dmd.n_modes,
            "n_observations": dmd.n_observations,
            "reconstruction_error_pct": round(dmd.reconstruction_error * 100, 2),
            "n_stable_modes": dmd.n_stable_modes,
            "n_growing_modes": dmd.n_growing_modes,
            "modes": [
                {
                    "mode_index": m.mode_index,
                    "period_days": round(m.period_days, 1) if m.period_days < 1e6 else "inf",
                    "period_label": _period_to_label(m.period_days) if m.period_days < 1e6 else "DC/trend",
                    "growth_rate": round(m.growth_rate, 6),
                    "energy_pct": round(m.energy_fraction * 100, 2),
                    "is_stable": m.is_stable,
                    "spatial_weights": {
                        k: round(v, 4) for k, v in m.spatial_weights.items()
                    },
                }
                for m in dmd.modes[:10]
            ],
        }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)

    logger.info("Exported Hilbert analysis to %s", output_path)
    return output_path
