"""Bank Analyzer API — standalone FastAPI service.

Run with:
    uvicorn munipal.engines.bank_analyzer.api:app --port 8100 --reload

Or:
    python -m munipal.engines.bank_analyzer.api
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .ingest import load_all_banks
from .matching import match_banks_to_deal
from .models import (
    BankScorecard,
    DealMatchRequest,
    DealMatchResult,
)
from .scoring import score_all_banks, score_bank

logger = logging.getLogger("bank_analyzer.api")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_DATA_DIR = Path(
    r"C:\Users\st3ja\OneDrive\Documents\MEGA\PROJECTS\INNOVATION FACTORY\TOUCAN"
)

# ---------------------------------------------------------------------------
# App startup — load and score banks once
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Muni-Pal Bank Analyzer",
    description="Market intelligence engine — scores and matches commercial banks to municipal bond deal opportunities.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory bank data (loaded on startup)
_banks = []
_scorecards: list[BankScorecard] = []


@app.on_event("startup")
async def _load_banks() -> None:
    global _banks, _scorecards
    _banks = load_all_banks(DEFAULT_DATA_DIR)
    _scorecards = score_all_banks(_banks)
    logger.info("Bank Analyzer ready: %d banks scored", len(_scorecards))


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class HealthResponse(BaseModel):
    status: str = "ok"
    banks_loaded: int = 0
    version: str = "0.1.0"


class ScoreboardResponse(BaseModel):
    total: int
    sort_by: str
    banks: list[BankScorecard]


class DistressEntry(BaseModel):
    bank_name: str
    state: str | None
    total_assets: float
    distress_score: float
    opportunity_type: str
    cre_npl_ratio: float
    cre_concentration_pct: float
    total_reo: float
    distress_segments: list[str]


class DistressResponse(BaseModel):
    total_distressed: int
    threshold: float
    banks: list[DistressEntry]


class GreenFinanceEntry(BaseModel):
    bank_name: str
    state: str | None
    total_assets: float
    green_score: float
    esg_level: str
    has_carbon_deals: bool
    carbon_deal_volume: float
    carbon_deal_types: list[str]


class GreenFinanceResponse(BaseModel):
    total: int
    banks: list[GreenFinanceEntry]


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(banks_loaded=len(_scorecards))


@app.get("/banks", response_model=ScoreboardResponse)
async def list_banks(
    sort_by: Literal["composite", "cre", "enhancement", "purchase", "green"] = "composite",
    limit: int = Query(25, ge=1, le=500),
    offset: int = Query(0, ge=0),
    state: str | None = None,
    min_assets: float | None = None,
    max_assets: float | None = None,
    pca: str | None = None,
) -> ScoreboardResponse:
    """List scored banks with optional filters and sorting."""
    filtered = _scorecards[:]

    if state:
        filtered = [s for s in filtered if s.state and s.state.upper() == state.upper()]
    if min_assets is not None:
        filtered = [s for s in filtered if s.total_assets >= min_assets]
    if max_assets is not None:
        filtered = [s for s in filtered if s.total_assets <= max_assets]
    if pca:
        filtered = [s for s in filtered if s.pca_category == pca]

    sort_keys = {
        "composite": lambda s: -s.composite_score,
        "cre": lambda s: -s.cre_distress.score,
        "enhancement": lambda s: -s.credit_enhancement.score,
        "purchase": lambda s: -s.direct_purchase.score,
        "green": lambda s: -s.green_finance.score,
    }
    filtered.sort(key=sort_keys[sort_by])

    return ScoreboardResponse(
        total=len(filtered),
        sort_by=sort_by,
        banks=filtered[offset : offset + limit],
    )


@app.get("/banks/{rssd_id}", response_model=BankScorecard)
async def get_bank(rssd_id: int) -> BankScorecard:
    """Get detailed scorecard for a specific bank by RSSD ID."""
    for sc in _scorecards:
        if sc.id_rssd == rssd_id:
            return sc
    from fastapi import HTTPException
    raise HTTPException(status_code=404, detail=f"Bank RSSD {rssd_id} not found")


@app.get("/banks/search/{name}", response_model=list[BankScorecard])
async def search_banks(
    name: str,
    limit: int = Query(10, ge=1, le=50),
) -> list[BankScorecard]:
    """Search banks by name (case-insensitive substring match)."""
    name_upper = name.upper()
    matches = [sc for sc in _scorecards if name_upper in sc.bank_name.upper()]
    matches.sort(key=lambda s: -s.composite_score)
    return matches[:limit]


@app.get("/distress", response_model=DistressResponse)
async def distress_analysis(
    threshold: float = Query(20.0, ge=0, le=100),
    limit: int = Query(25, ge=1, le=100),
) -> DistressResponse:
    """Banks with CRE distress above threshold — workout advisory opportunities."""
    distressed = [
        DistressEntry(
            bank_name=sc.bank_name,
            state=sc.state,
            total_assets=sc.total_assets,
            distress_score=sc.cre_distress.score,
            opportunity_type=sc.cre_distress.opportunity_type,
            cre_npl_ratio=sc.cre_distress.cre_npl_ratio,
            cre_concentration_pct=sc.cre_distress.cre_concentration_pct,
            total_reo=sc.cre_distress.total_reo,
            distress_segments=sc.cre_distress.distress_segments,
        )
        for sc in _scorecards
        if sc.cre_distress.score >= threshold
    ]
    distressed.sort(key=lambda d: -d.distress_score)
    return DistressResponse(
        total_distressed=len(distressed),
        threshold=threshold,
        banks=distressed[:limit],
    )


@app.get("/green", response_model=GreenFinanceResponse)
async def green_finance(
    min_score: float = Query(10.0, ge=0, le=100),
    limit: int = Query(25, ge=1, le=100),
) -> GreenFinanceResponse:
    """Banks with green/ESG finance capability."""
    greens = [
        GreenFinanceEntry(
            bank_name=sc.bank_name,
            state=sc.state,
            total_assets=sc.total_assets,
            green_score=sc.green_finance.score,
            esg_level=sc.green_finance.esg_commitment_level,
            has_carbon_deals=sc.green_finance.has_carbon_deals,
            carbon_deal_volume=sc.green_finance.carbon_deal_volume,
            carbon_deal_types=sc.green_finance.carbon_deal_types,
        )
        for sc in _scorecards
        if sc.green_finance.score >= min_score
    ]
    greens.sort(key=lambda g: -g.green_score)
    return GreenFinanceResponse(total=len(greens), banks=greens[:limit])


@app.post("/match", response_model=DealMatchResult)
async def match_deal(deal: DealMatchRequest) -> DealMatchResult:
    """Match banks to a specific deal profile."""
    return match_banks_to_deal(_scorecards, deal)


@app.post("/reload")
async def reload_data() -> dict:
    """Reload bank data from CSVs (for data refresh without restart)."""
    global _banks, _scorecards
    _banks = load_all_banks(DEFAULT_DATA_DIR)
    _scorecards = score_all_banks(_banks)
    return {"status": "reloaded", "banks": len(_scorecards)}


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

def main() -> None:
    import uvicorn
    uvicorn.run(
        "munipal.engines.bank_analyzer.api:app",
        host="0.0.0.0",
        port=8100,
        reload=True,
    )


if __name__ == "__main__":
    main()
