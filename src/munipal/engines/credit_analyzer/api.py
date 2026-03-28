"""Credit Analyzer API — standalone FastAPI service.

Run with:
    uvicorn munipal.engines.credit_analyzer.api:app --port 8200 --reload

Or:
    python -m munipal.engines.credit_analyzer api
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .bond_sizing import size_bond
from .deal_structuring import structure_deal
from .financial_model import build_financial_model
from .five_cs import assess_five_cs
from .models import (
    BondSizingResult,
    CreditAnalysisResult,
    DealStructure,
    FiveCsAssessment,
    ProjectInputs,
    ThreeStatementModel,
)

logger = logging.getLogger("credit_analyzer.api")

app = FastAPI(
    title="Muni-Pal Credit Analyzer",
    description="Credit analysis, bond sizing, and deal structuring engine for municipal bond underwriting.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "version": "0.1.0", "engine": "credit_analyzer"}


@app.post("/five-cs", response_model=FiveCsAssessment)
async def run_five_cs(project: ProjectInputs) -> FiveCsAssessment:
    """Run 5 Cs credit assessment on a project."""
    return assess_five_cs(project)


@app.post("/size", response_model=BondSizingResult)
async def run_bond_sizing(
    project: ProjectInputs,
    target_dscr: float = 1.25,
    coupon_rate: float | None = None,
) -> BondSizingResult:
    """Size a bond issue based on project financials and target DSCR."""
    return size_bond(project, target_dscr=target_dscr, coupon_rate=coupon_rate)


@app.post("/model", response_model=ThreeStatementModel)
async def run_financial_model(
    project: ProjectInputs,
    target_dscr: float = 1.25,
    projection_years: int = 10,
) -> ThreeStatementModel:
    """Build pro forma 3-statement financial model."""
    sizing = size_bond(project, target_dscr=target_dscr)
    return build_financial_model(project, sizing, projection_years)


@app.post("/structure", response_model=DealStructure)
async def run_deal_structuring(
    project: ProjectInputs,
    target_dscr: float = 1.25,
) -> DealStructure:
    """Generate recommended deal structure (covenants, security, pricing)."""
    five_cs = assess_five_cs(project)
    sizing = size_bond(project, target_dscr=target_dscr)
    return structure_deal(project, five_cs, sizing)


@app.post("/analyze", response_model=CreditAnalysisResult)
async def run_full_analysis(
    project: ProjectInputs,
    target_dscr: float = 1.25,
) -> CreditAnalysisResult:
    """Run the full credit analysis pipeline: 5 Cs + Sizing + Model + Structuring."""
    five_cs = assess_five_cs(project)
    sizing = size_bond(project, target_dscr=target_dscr)
    fin_model = build_financial_model(project, sizing)
    deal = structure_deal(project, five_cs, sizing)

    credit_opinion = None
    if five_cs.composite_score >= 70 and sizing.min_dscr >= 1.25:
        credit_opinion = "investment_grade"
    elif five_cs.composite_score >= 55:
        credit_opinion = "crossover"
    elif five_cs.composite_score >= 40:
        credit_opinion = "not_rated_adequate"
    else:
        credit_opinion = "not_rated_weak"

    result = CreditAnalysisResult(
        project_name=project.project_name,
        analysis_timestamp=datetime.now(timezone.utc),
        five_cs=five_cs,
        financial_model=fin_model,
        bond_sizing=sizing,
        deal_structure=deal,
        credit_opinion=credit_opinion,
    )

    # Standard Model integration (capstone)
    from .standard_model import integrate_standard_model
    result = integrate_standard_model(result, project)

    return result


def main() -> None:
    import uvicorn
    uvicorn.run(
        "munipal.engines.credit_analyzer.api:app",
        host="0.0.0.0",
        port=8200,
        reload=True,
    )


if __name__ == "__main__":
    main()
