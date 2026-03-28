"""Sensing Component Service — wraps EMMA corpus analysis tools.

Bridges the EMMA bond_os_extractor analysis modules (market intelligence,
benchmarking calculator, readiness assessment) into the FastAPI backend.

These tools use synchronous SQLAlchemy against a separate SQLite corpus.db,
so all calls are run in a threadpool executor.
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Any

# EMMA bond_os_extractor lives at a known path relative to the Muni-Pal root.
_MUNIPAL_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_EMMA_EXTRACTOR = _MUNIPAL_ROOT / "emma" / "bond_os_extractor"


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

def _run_market_intelligence(sector: str) -> dict[str, Any]:
    """Generate market intelligence report (sync, runs in threadpool)."""
    _ensure_emma_path()
    from src.config import set_sector
    from src.analysis.market_intelligence import generate_market_intelligence

    set_sector(sector)
    engine = _get_corpus_engine(sector)
    report = generate_market_intelligence(engine)
    return report.to_dict()


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

def _run_credit_spread_monitor(
    sector: str,
    par_amount: float,
    out_of_state: bool,
) -> dict[str, Any]:
    """Generate credit spread monitor report (sync, runs in threadpool)."""
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
    return report.to_dict()


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
    _ensure_emma_path()
    from src.config import set_sector
    from src.analysis.readiness_assessment import (
        AssessmentResponse,
        score_assessment,
    )

    set_sector(sector)
    engine = _get_corpus_engine(sector)

    # Merge evidence IDs into responses dict (evidence items use
    # the same item_id format: risk.{dim}.evidence.{n})
    merged_responses = dict(responses)
    for eid in evidence_ids:
        merged_responses[eid] = True

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
    """List sectors that have a corpus.db file."""
    data_root = _EMMA_EXTRACTOR / "data"
    sectors = []
    for sector_dir in sorted(data_root.iterdir()):
        if sector_dir.is_dir() and (sector_dir / "corpus.db").exists():
            sectors.append({
                "id": sector_dir.name,
                "name": sector_dir.name.replace("_", " ").title(),
            })
    return sectors
