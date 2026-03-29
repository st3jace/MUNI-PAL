"""Sensing Component Service — wraps EMMA corpus analysis tools.

Bridges the EMMA bond_os_extractor analysis modules (market intelligence,
benchmarking calculator, readiness assessment) into the FastAPI backend.

These tools use synchronous SQLAlchemy against a separate SQLite corpus.db,
so all calls are run in a threadpool executor.

When the EMMA corpus data is not available (e.g., production deployments
where corpus.db is gitignored), falls back to pre-computed seed data
stored in sensing_seed/.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger("munipal.services.sensing")


def _find_munipal_root() -> Path:
    """Locate the Muni-Pal project root directory.

    Handles both development (source tree) and production (pip-installed
    into a venv) deployments.
    """
    # 1. Explicit environment variable (most reliable for production)
    if env_root := os.environ.get("MUNIPAL_ROOT"):
        return Path(env_root)
    # 2. Relative to source file (works in development, not in venv installs)
    candidate = Path(__file__).resolve().parent.parent.parent.parent
    if (candidate / "emma" / "bond_os_extractor").is_dir():
        return candidate
    # 3. Railway / Docker default working directory
    if Path("/app/emma/bond_os_extractor").is_dir():
        return Path("/app")
    # 4. Current working directory
    cwd = Path.cwd()
    if (cwd / "emma" / "bond_os_extractor").is_dir():
        return cwd
    # 5. Fall back to the relative path (seed data will cover gaps)
    return candidate


_MUNIPAL_ROOT = _find_munipal_root()
_EMMA_EXTRACTOR = _MUNIPAL_ROOT / "emma" / "bond_os_extractor"

# Pre-computed seed data directory (committed to git, always available).
_SEED_DIR = Path(__file__).resolve().parent / "sensing_seed"

# Sectors that have seed data available (even without corpus.db).
_SEED_SECTORS = ["waste", "healthcare"]


def _corpus_available(sector: str) -> bool:
    """Check whether the EMMA corpus.db exists for a sector."""
    return (_EMMA_EXTRACTOR / "data" / sector / "corpus.db").is_file()


def _load_seed(filename: str) -> Any:
    """Load a pre-computed seed JSON file."""
    path = _SEED_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Seed file not found: {path}")
    with open(path) as f:
        return json.load(f)


def _ensure_emma_path() -> None:
    """Add bond_os_extractor to sys.path if not already present."""
    path_str = str(_EMMA_EXTRACTOR)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)


def _get_corpus_engine(sector: str):
    """Create a sync SQLAlchemy engine for the sector's corpus.db."""
    _ensure_emma_path()
    from src.config import set_sector, get_settings
    from src.storage.database import init_database

    set_sector(sector)
    return init_database()


# ---------------------------------------------------------------------------
# Market Intelligence
# ---------------------------------------------------------------------------

def _enrich_market_intelligence(result: dict[str, Any]) -> dict[str, Any]:
    """Add top-level summary statistics extracted from the nested report."""
    ds = result.get("deal_structure") or {}
    result["total_deals"] = ds.get("n_deals")
    result["total_par_value"] = ds.get("par_amount_total_usd")
    result["median_deal_size"] = ds.get("par_amount_median_usd")
    return result


def _run_market_intelligence(sector: str) -> dict[str, Any]:
    """Generate market intelligence report (sync, runs in threadpool)."""
    if not _corpus_available(sector):
        logger.info("Corpus unavailable for %s — serving seed data", sector)
        return _enrich_market_intelligence(_load_seed(f"market_intelligence_{sector}.json"))

    _ensure_emma_path()
    from src.config import set_sector
    from src.analysis.market_intelligence import generate_market_intelligence

    set_sector(sector)
    engine = _get_corpus_engine(sector)
    report = generate_market_intelligence(engine)
    return _enrich_market_intelligence(report.to_dict())


async def get_market_intelligence(sector: str) -> dict[str, Any]:
    """Async wrapper for market intelligence generation."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _run_market_intelligence, sector)


# ---------------------------------------------------------------------------
# Benchmarking Calculator
# ---------------------------------------------------------------------------

def _run_benchmark(
    sector: str,
    deal_size: float,
    state: str,
    rating: str,
    maturity: float,
) -> dict[str, Any]:
    """Generate issuance benchmark (sync, runs in threadpool)."""
    if not _corpus_available(sector):
        logger.info("Corpus unavailable for %s — serving seed benchmark", sector)
        seed = _load_seed(f"benchmark_baseline_{sector}.json")
        # Overlay the prospect's inputs onto the seed baseline
        seed["prospect_inputs"] = {
            "sector": sector,
            "deal_size": deal_size,
            "state": state.upper(),
            "expected_rating": rating,
            "maturity_years": maturity,
        }
        return seed

    _ensure_emma_path()
    from src.config import set_sector
    from src.analysis.benchmarking_calculator import (
        ProspectInputs,
        generate_benchmark,
    )

    set_sector(sector)
    engine = _get_corpus_engine(sector)
    inputs = ProspectInputs(
        sector=sector,
        deal_size=deal_size,
        state=state.upper(),
        expected_rating=rating,
        maturity_years=maturity,
    )
    result = generate_benchmark(engine, inputs)
    return result.to_dict()


async def get_benchmark(
    sector: str,
    deal_size: float,
    state: str,
    rating: str,
    maturity: float = 30.0,
) -> dict[str, Any]:
    """Async wrapper for benchmark generation."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None, _run_benchmark, sector, deal_size, state, rating, maturity
    )


# ---------------------------------------------------------------------------
# Credit Spread Monitor
# ---------------------------------------------------------------------------

def _enrich_credit_spreads(result: dict[str, Any], sector: str) -> dict[str, Any]:
    """Overlay seed corpus spread data for entries missing observations.

    The EMMA corpus path may produce partial results — some rating buckets
    have trade data while others don't (e.g. AA trades missing but A trades
    present). For each cost_grid entry and corpus_spreads bucket with zero
    observations, overlay the pre-computed seed values.
    """
    if sector not in _SEED_SECTORS:
        return result

    try:
        seed = _load_seed(f"credit_spreads_{sector}.json")
    except FileNotFoundError:
        return result

    # Merge corpus_spreads: fill missing rating buckets from seed
    live_spreads = result.get("corpus_spreads") or {}
    seed_spreads = seed.get("corpus_spreads") or {}
    if seed_spreads:
        merged = dict(seed_spreads)  # start with seed as base
        merged.update(live_spreads)  # live data takes precedence
        result["corpus_spreads"] = merged

    # Overlay n_corpus_obs and corpus_observed_yield per cost_grid entry
    seed_grid_map: dict[tuple[str, int], dict[str, Any]] = {}
    for entry in seed.get("cost_grid", []):
        seed_grid_map[(entry["rating"], entry["tenor"])] = entry

    patched = False
    for entry in result.get("cost_grid", []):
        if entry.get("n_corpus_obs", 0) > 0:
            continue
        key = (entry["rating"], entry["tenor"])
        seed_entry = seed_grid_map.get(key)
        if seed_entry and seed_entry.get("n_corpus_obs", 0) > 0:
            entry["n_corpus_obs"] = seed_entry["n_corpus_obs"]
            entry["corpus_observed_yield"] = seed_entry.get("corpus_observed_yield")
            patched = True

    if patched:
        logger.info("Overlaid seed corpus spreads for %s (filled gaps in live data)", sector)

    return result


def _run_credit_spread_monitor(
    sector: str,
    par_amount: float,
    out_of_state: bool,
) -> dict[str, Any]:
    """Generate credit spread monitor report (sync, runs in threadpool)."""
    if not _corpus_available(sector):
        logger.info("Corpus unavailable for %s — serving seed credit spreads", sector)
        return _load_seed(f"credit_spreads_{sector}.json")

    _ensure_emma_path()
    from src.config import set_sector
    from src.analysis.credit_spread_monitor import generate_credit_spread_report

    set_sector(sector)
    engine = _get_corpus_engine(sector)
    report = generate_credit_spread_report(
        engine,
        par_amount=par_amount,
        out_of_state=out_of_state,
    )
    return _enrich_credit_spreads(report.to_dict(), sector)


async def get_credit_spread_monitor(
    sector: str,
    par_amount: float = 50_000_000.0,
    out_of_state: bool = False,
) -> dict[str, Any]:
    """Async wrapper for credit spread monitor generation."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None, _run_credit_spread_monitor, sector, par_amount, out_of_state
    )


# ---------------------------------------------------------------------------
# Readiness Assessment
# ---------------------------------------------------------------------------

def _readiness_result_to_dict(result) -> dict[str, Any]:  # type: ignore[no-untyped-def]
    """Serialize ReadinessResult to dict (mirrors export_json logic)."""
    data: dict[str, Any] = {
        "project_name": result.project_name,
        "generated_at": result.generated_at,
        "sector": result.sector,
        "readiness_score": round(result.adjusted_score, 1),
        "raw_score": round(result.raw_score, 1),
        "tier": result.readiness_tier,
        "tier_guidance": result.tier_guidance,
        "dimensions_addressed": result.dimensions_addressed,
        "dimensions_partial": result.dimensions_partial,
        "dimensions_missing": result.dimensions_missing,
        "evidence_present": result.total_evidence_present,
        "evidence_possible": result.total_evidence_possible,
        "evidence_completeness_pct": round(result.evidence_completeness_pct, 1),
        "dimensions": [],
        "financial_assessment": {
            "dscr_assessment": result.financial_assessment.dscr_narrative,
            "dscr_score": result.financial_assessment.dscr_score,
            "coverage_assessment": result.financial_assessment.coverage_narrative,
            "coverage_score": result.financial_assessment.coverage_score,
            "revenue_assessment": result.financial_assessment.revenue_narrative,
            "revenue_score": result.financial_assessment.revenue_score,
            "total_adjustment": result.financial_assessment.adjustment_points,
            "flags": result.financial_assessment.financial_flags,
        },
        "priority_actions": result.priority_actions,
        "gap_analysis": [],
        "corpus_summary": result.corpus_summary,
    }
    for dim in result.dimension_scores:
        dim_dict = {
            "dimension": dim.dimension,
            "display_name": dim.display_name,
            "score": round(dim.score, 1),
            "max_score": dim.max_score,
            "pct": round(dim.pct, 1),
            "description_provided": dim.description_answered,
            "mitigants_provided": dim.mitigants_answered,
            "evidence_count": dim.evidence_count,
            "evidence_total": dim.evidence_total,
        }
        data["dimensions"].append(dim_dict)
        if dim.gap_severity and dim.gap_severity != "acceptable":
            data["gap_analysis"].append({
                "dimension": dim.dimension,
                "dimension_name": dim.display_name,
                "severity": dim.gap_severity,
                "narrative": dim.gap_narrative,
                "recommendations": dim.recommendations,
            })
    return data


def _score_readiness_from_seed(
    sector: str,
    project_name: str,
    responses: dict[str, bool],
    dscr: float | None,
    revenue: float | None,
    coverage_ratio: float | None,
) -> dict[str, Any]:
    """Simplified readiness scoring using seed questionnaire (no corpus)."""
    from datetime import datetime, timezone

    questionnaire = _load_seed(f"questionnaire_{sector}.json")
    # Group items by dimension
    dims: dict[str, list[dict]] = {}
    for item in questionnaire:
        dims.setdefault(item["dimension"], []).append(item)

    total_score = 0.0
    total_max = 0.0
    dim_scores = []
    gap_analysis = []

    for dim_key, items in dims.items():
        dim_max = sum(it["points"] for it in items)
        dim_earned = sum(
            it["points"] for it in items
            if responses.get(it["item_id"], False)
        )
        pct = (dim_earned / dim_max * 100) if dim_max else 0
        total_score += dim_earned
        total_max += dim_max

        evidence_items = [it for it in items if it["category"] == "evidence"]
        desc_items = [it for it in items if it["category"] == "description"]
        mitigant_items = [it for it in items if it["category"] == "mitigant"]

        dim_scores.append({
            "dimension": dim_key,
            "display_name": items[0].get("dimension_label", dim_key),
            "score": round(dim_earned, 1),
            "max_score": dim_max,
            "pct": round(pct, 1),
            "description_provided": any(responses.get(it["item_id"]) for it in desc_items),
            "mitigants_provided": any(responses.get(it["item_id"]) for it in mitigant_items),
            "evidence_count": sum(1 for it in evidence_items if responses.get(it["item_id"])),
            "evidence_total": len(evidence_items),
        })

        severity = "acceptable" if pct >= 60 else ("material" if pct >= 30 else "critical")
        if severity != "acceptable":
            gap_analysis.append({
                "dimension": dim_key,
                "dimension_name": items[0].get("dimension_label", dim_key),
                "severity": severity,
                "narrative": f"Score {pct:.0f}% — additional documentation needed.",
                "recommendations": [it["question"] for it in items if not responses.get(it["item_id"])],
            })

    raw_pct = (total_score / total_max * 100) if total_max else 0

    # Financial adjustment
    fin_adj = 0.0
    fin_flags = []
    if dscr is not None:
        if dscr >= 1.5:
            fin_adj += 5
        elif dscr >= 1.2:
            fin_adj += 2
        else:
            fin_flags.append(f"DSCR {dscr:.2f}x below 1.2x threshold")

    adjusted = min(raw_pct + fin_adj, 100)
    tier = (
        "Bond Ready" if adjusted >= 75
        else "Near Ready" if adjusted >= 50
        else "Developing" if adjusted >= 25
        else "Early Stage"
    )

    return {
        "project_name": project_name,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sector": sector,
        "readiness_score": round(adjusted, 1),
        "raw_score": round(raw_pct, 1),
        "tier": tier,
        "tier_guidance": f"Your project scored {adjusted:.0f}% on the bond readiness assessment.",
        "dimensions_addressed": sum(1 for d in dim_scores if d["pct"] >= 60),
        "dimensions_partial": sum(1 for d in dim_scores if 0 < d["pct"] < 60),
        "dimensions_missing": sum(1 for d in dim_scores if d["pct"] == 0),
        "evidence_present": sum(d["evidence_count"] for d in dim_scores),
        "evidence_possible": sum(d["evidence_total"] for d in dim_scores),
        "evidence_completeness_pct": round(
            sum(d["evidence_count"] for d in dim_scores)
            / max(sum(d["evidence_total"] for d in dim_scores), 1)
            * 100, 1
        ),
        "dimensions": dim_scores,
        "financial_assessment": {
            "dscr_assessment": f"DSCR: {dscr}" if dscr else "Not provided",
            "dscr_score": fin_adj if dscr else 0,
            "coverage_assessment": f"Coverage ratio: {coverage_ratio}" if coverage_ratio else "Not provided",
            "coverage_score": 0,
            "revenue_assessment": f"Revenue: ${revenue:,.0f}" if revenue else "Not provided",
            "revenue_score": 0,
            "total_adjustment": fin_adj,
            "flags": fin_flags,
        },
        "priority_actions": [g["narrative"] for g in gap_analysis[:3]],
        "gap_analysis": gap_analysis,
        "corpus_summary": {"note": "Scored using pre-computed sector benchmarks"},
    }


def _run_readiness_assessment(
    sector: str,
    project_name: str,
    responses: dict[str, bool],
    evidence_ids: list[str],
    dscr: float | None,
    revenue: float | None,
    coverage_ratio: float | None,
) -> dict[str, Any]:
    """Score readiness assessment (sync, runs in threadpool)."""
    # Merge evidence IDs into responses dict
    merged_responses = dict(responses)
    for eid in evidence_ids:
        merged_responses[eid] = True

    if not _corpus_available(sector):
        logger.info("Corpus unavailable for %s — using seed-based readiness scoring", sector)
        return _score_readiness_from_seed(
            sector, project_name, merged_responses, dscr, revenue, coverage_ratio,
        )

    _ensure_emma_path()
    from src.config import set_sector
    from src.analysis.readiness_assessment import (
        AssessmentResponse,
        score_assessment,
    )

    set_sector(sector)
    engine = _get_corpus_engine(sector)

    response = AssessmentResponse(
        project_name=project_name,
        responses=merged_responses,
        dscr=dscr,
        revenue=revenue,
        coverage_ratio=coverage_ratio,
    )
    result = score_assessment(engine, response, sector=sector)
    return _readiness_result_to_dict(result)


async def get_readiness_assessment(
    sector: str,
    project_name: str,
    responses: dict[str, bool],
    evidence_ids: list[str] | None = None,
    dscr: float | None = None,
    revenue: float | None = None,
    coverage_ratio: float | None = None,
) -> dict[str, Any]:
    """Async wrapper for readiness assessment."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        _run_readiness_assessment,
        sector,
        project_name,
        responses,
        evidence_ids or [],
        dscr,
        revenue,
        coverage_ratio,
    )


# ---------------------------------------------------------------------------
# Questionnaire (lightweight — no DB needed)
# ---------------------------------------------------------------------------

def _get_questionnaire(sector: str = "waste") -> list[dict[str, Any]]:
    """Get the readiness questionnaire items for a given sector."""
    # Try seed data first (always available, no EMMA imports needed)
    seed_path = _SEED_DIR / f"questionnaire_{sector}.json"
    if seed_path.exists() and not _corpus_available(sector):
        logger.info("Corpus unavailable for %s — serving seed questionnaire", sector)
        return _load_seed(f"questionnaire_{sector}.json")

    _ensure_emma_path()
    from src.analysis.readiness_assessment import build_questionnaire
    from src.analysis.risk_benchmark import get_readiness_path_config

    path_config = get_readiness_path_config(sector)
    # Build a dimension -> display_name lookup
    dim_names = {path: cfg["display_name"] for path, cfg in path_config.items()}

    items = build_questionnaire(sector=sector)
    return [
        {
            "item_id": item.item_id,
            "dimension": item.dimension,
            "dimension_label": dim_names.get(item.dimension, item.dimension),
            "category": item.category,
            "question": item.question,
            "help_text": item.help_text,
            "points": item.points,
        }
        for item in items
    ]


async def get_questionnaire(sector: str = "waste") -> list[dict[str, Any]]:
    """Async wrapper for questionnaire retrieval."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _get_questionnaire, sector)


# ---------------------------------------------------------------------------
# Available Sectors
# ---------------------------------------------------------------------------

def get_available_sectors() -> list[dict[str, str]]:
    """List sectors that have corpus data or seed data available."""
    sectors: list[dict[str, str]] = []
    seen: set[str] = set()

    # Check for live corpus data
    data_root = _EMMA_EXTRACTOR / "data"
    if data_root.is_dir():
        for sector_dir in sorted(data_root.iterdir()):
            if sector_dir.is_dir() and (sector_dir / "corpus.db").exists():
                name = sector_dir.name
                sectors.append({
                    "id": name,
                    "name": name.replace("_", " ").title(),
                })
                seen.add(name)

    # Fall back to seed sectors if no live corpus found
    if not seen:
        for name in _SEED_SECTORS:
            if name not in seen and (_SEED_DIR / f"market_intelligence_{name}.json").exists():
                sectors.append({
                    "id": name,
                    "name": name.replace("_", " ").title(),
                })
                seen.add(name)

    return sectors
