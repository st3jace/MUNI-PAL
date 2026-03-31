"""Sensing Component API — Market Intelligence, Benchmarking, Readiness.

Top-of-funnel tools for municipal bond prospects. These endpoints are
lightly authenticated (no project context required) and serve as the
web-facing version of the CLI sensing tools.

Lead flow:
  GET  /sectors                   → list available sectors
  GET  /market-intelligence       → sector benchmark report
  POST /benchmark                 → prospect-specific issuance benchmark
  GET  /questionnaire             → readiness assessment questions
  POST /readiness                 → scored readiness assessment
  POST /lead                      → capture lead + store report snapshot
  POST /event                     → funnel event tracking
  GET  /leads                     → list captured leads (admin)
"""
from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from munipal.db.session import get_async_session
from munipal.services import sensing

router = APIRouter()


# ---------------------------------------------------------------------------
# Request/Response Models
# ---------------------------------------------------------------------------

class BenchmarkRequest(BaseModel):
    sector: str = Field(..., description="Sector (waste, healthcare)")
    deal_size: float = Field(..., gt=0, description="Deal size in USD")
    state: str = Field(..., min_length=2, max_length=2, description="State abbreviation")
    rating: str = Field(..., description="Expected credit rating (e.g., A, BBB+, Aa2)")
    maturity: float = Field(default=30.0, gt=0, description="Years to final maturity")


class CreditSpreadRequest(BaseModel):
    """Parameters for the credit spread monitor."""
    sector: str = Field(..., description="Sector (waste, healthcare, etc.)")
    par_amount: float = Field(default=50_000_000.0, gt=0, description="Representative par amount for fee calculations")
    out_of_state: bool = Field(default=False, description="Whether borrower is out-of-state (affects IDA fees)")


class ReadinessRequest(BaseModel):
    sector: str = Field(..., description="Sector (waste, healthcare)")
    project_name: str = Field(default="Project", description="Project name")
    responses: dict[str, bool] = Field(
        default_factory=dict,
        description="Dimension responses (e.g., risk.technology.description: true)",
    )
    evidence_ids: list[str] = Field(
        default_factory=list,
        description="Evidence item IDs present (e.g., risk.technology.evidence.1)",
    )
    dscr: float | None = Field(default=None, description="Debt Service Coverage Ratio")
    revenue: float | None = Field(default=None, description="Annual revenue in USD")
    coverage_ratio: float | None = Field(default=None, description="Minimum coverage ratio")


class LeadCaptureRequest(BaseModel):
    """Lead info submitted before combined report PDF download."""
    # Required contact
    email: str = Field(..., description="Contact email")
    name: str = Field(..., description="Full name")
    organization: str = Field(..., description="Organization / entity name")
    # Optional contact
    title: str | None = Field(default=None, description="Job title / role")
    phone: str | None = Field(default=None, description="Phone number")
    # Deal context
    sector: str = Field(..., description="Primary sector of interest")
    deal_size_estimate: float | None = Field(default=None, description="Estimated deal size USD")
    state: str | None = Field(default=None, description="State abbreviation")
    expected_rating: str | None = Field(default=None, description="Expected rating")
    # Referral
    referral_source: str | None = Field(default=None, description="How they heard about us")
    # Session link
    session_id: str = Field(..., description="Client session ID for event linkage")
    # Report data snapshots (JSON strings)
    market_intel_json: str | None = Field(default=None, description="Market intelligence report JSON")
    benchmark_json: str | None = Field(default=None, description="Benchmark results JSON")
    readiness_json: str | None = Field(default=None, description="Readiness assessment JSON")


class EventRequest(BaseModel):
    """Funnel event tracking."""
    session_id: str = Field(..., description="Client session ID")
    event_type: str = Field(..., description="Event type (page_view, benchmark_run, etc.)")
    sector: str | None = Field(default=None)
    event_data: str | None = Field(default=None, description="Optional JSON payload")


# ---------------------------------------------------------------------------
# Existing Sensing Endpoints
# ---------------------------------------------------------------------------

@router.get("/sectors")
async def list_sectors() -> list[dict[str, str]]:
    """List available sectors with corpus data."""
    return sensing.get_available_sectors()


@router.get("/market-intelligence")
async def market_intelligence(
    sector: str = Query(..., description="Sector (waste, healthcare)"),
) -> dict[str, Any]:
    """Generate Sector Market Intelligence Report."""
    _validate_sector(sector)
    return await sensing.get_market_intelligence(sector)


@router.post("/benchmark")
async def benchmark_issuance(request: BenchmarkRequest) -> dict[str, Any]:
    """Benchmark a prospective issuance against the EMMA corpus."""
    _validate_sector(request.sector)
    return await sensing.get_benchmark(
        sector=request.sector,
        deal_size=request.deal_size,
        state=request.state,
        rating=request.rating,
        maturity=request.maturity,
    )


@router.post("/credit-spreads")
async def credit_spread_monitor(request: CreditSpreadRequest) -> dict[str, Any]:
    """Generate Credit Spread Monitor & All-In Cost of Capital report.

    Returns yield curves, cost-of-capital grid, issuer fee comparisons,
    corpus-derived spread observations, and recent comparable deals.
    """
    _validate_sector(request.sector)
    return await sensing.get_credit_spread_monitor(
        sector=request.sector,
        par_amount=request.par_amount,
        out_of_state=request.out_of_state,
    )


@router.get("/questionnaire")
async def get_questionnaire(
    sector: str = Query(default="waste", description="Sector (waste, healthcare)"),
) -> list[dict[str, Any]]:
    """Get the readiness self-assessment questionnaire for a sector."""
    return await sensing.get_questionnaire(sector=sector)


@router.post("/readiness")
async def readiness_assessment(request: ReadinessRequest) -> dict[str, Any]:
    """Score a Bond Readiness Self-Assessment."""
    _validate_sector(request.sector)
    return await sensing.get_readiness_assessment(
        sector=request.sector,
        project_name=request.project_name,
        responses=request.responses,
        evidence_ids=request.evidence_ids,
        dscr=request.dscr,
        revenue=request.revenue,
        coverage_ratio=request.coverage_ratio,
    )


# ---------------------------------------------------------------------------
# Lead Capture & Event Tracking
# ---------------------------------------------------------------------------

@router.post("/lead")
async def capture_lead(
    request: LeadCaptureRequest,
    db: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """Capture prospect lead when they request the combined report PDF.

    Stores contact info, deal context, and a snapshot of all report data
    for follow-up. Links anonymous session events to this lead.
    """
    from munipal.core.models.lead import SensingLead, SensingEvent

    lead = SensingLead(
        email=request.email,
        name=request.name,
        organization=request.organization,
        title=request.title,
        phone=request.phone,
        sector=request.sector,
        deal_size_estimate=request.deal_size_estimate,
        state=request.state,
        expected_rating=request.expected_rating,
        referral_source=request.referral_source,
        funnel_stage="report_requested",
        market_intel_json=request.market_intel_json,
        benchmark_json=request.benchmark_json,
        readiness_json=request.readiness_json,
    )
    db.add(lead)

    # Link prior anonymous events to this lead
    from sqlalchemy import update
    await db.execute(
        update(SensingEvent)
        .where(SensingEvent.session_id == request.session_id)
        .where(SensingEvent.lead_id.is_(None))
        .values(lead_id=lead.id)
    )

    # Record the lead capture event itself
    db.add(SensingEvent(
        lead_id=lead.id,
        session_id=request.session_id,
        event_type="report_requested",
        sector=request.sector,
        event_data=json.dumps({
            "has_market_intel": request.market_intel_json is not None,
            "has_benchmark": request.benchmark_json is not None,
            "has_readiness": request.readiness_json is not None,
        }),
    ))

    await db.commit()
    await db.refresh(lead)

    return {
        "lead_id": lead.id,
        "status": "captured",
        "funnel_stage": lead.funnel_stage,
    }


@router.post("/event")
async def track_event(
    request: EventRequest,
    db: AsyncSession = Depends(get_async_session),
) -> dict[str, str]:
    """Track a funnel interaction event.

    Events are linked to a session_id and optionally to a lead_id
    once the prospect completes the lead capture form.
    """
    from munipal.core.models.lead import SensingEvent

    event = SensingEvent(
        session_id=request.session_id,
        event_type=request.event_type,
        sector=request.sector,
        event_data=request.event_data,
    )
    db.add(event)
    await db.commit()
    return {"status": "tracked"}


@router.get("/leads")
async def list_leads(
    db: AsyncSession = Depends(get_async_session),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[dict[str, Any]]:
    """List captured sensing leads (admin view)."""
    from sqlalchemy import select, func
    from munipal.core.models.lead import SensingLead, SensingEvent

    # Get leads with event counts
    stmt = (
        select(SensingLead)
        .order_by(SensingLead.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(stmt)
    leads = result.scalars().all()

    output = []
    for lead in leads:
        # Count events for this lead
        count_stmt = (
            select(func.count())
            .select_from(SensingEvent)
            .where(SensingEvent.lead_id == lead.id)
        )
        count_result = await db.execute(count_stmt)
        event_count = count_result.scalar() or 0

        output.append({
            "id": lead.id,
            "email": lead.email,
            "name": lead.name,
            "organization": lead.organization,
            "title": lead.title,
            "sector": lead.sector,
            "deal_size_estimate": lead.deal_size_estimate,
            "state": lead.state,
            "expected_rating": lead.expected_rating,
            "funnel_stage": lead.funnel_stage,
            "referral_source": lead.referral_source,
            "has_market_intel": lead.market_intel_json is not None,
            "has_benchmark": lead.benchmark_json is not None,
            "has_readiness": lead.readiness_json is not None,
            "event_count": event_count,
            "created_at": lead.created_at.isoformat() if lead.created_at else None,
        })
    return output


# ---------------------------------------------------------------------------
# Lead Qualification & Project Conversion
# ---------------------------------------------------------------------------

VALID_FUNNEL_STAGES = [
    "report_requested",
    "report_downloaded",
    "contacted",
    "qualified",
    "engaged",
]


class LeadFunnelUpdate(BaseModel):
    """Update a lead's funnel stage."""
    funnel_stage: str = Field(
        ..., description="New funnel stage (report_downloaded, contacted, qualified, engaged)"
    )


class LeadConvertRequest(BaseModel):
    """Convert a sensing lead to a BFMS project."""
    project_name: str | None = Field(
        default=None,
        description="Override project name (defaults to '{org} Bond Advisory')",
    )
    owner_id: str = Field(..., description="User ID to own the new project")
    tenant_id: str = Field(default="default", description="Tenant ID")
    playbook_id: str | None = Field(default=None, description="Playbook ID (uses default if omitted)")


@router.get("/leads/{lead_id}")
async def get_lead(
    lead_id: str,
    db: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """Get a single sensing lead with full detail including report snapshots."""
    from munipal.core.models.lead import SensingLead

    lead = await db.get(SensingLead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail=f"Lead {lead_id} not found")

    return {
        "id": lead.id,
        "email": lead.email,
        "name": lead.name,
        "organization": lead.organization,
        "title": lead.title,
        "phone": lead.phone,
        "sector": lead.sector,
        "deal_size_estimate": lead.deal_size_estimate,
        "state": lead.state,
        "expected_rating": lead.expected_rating,
        "funnel_stage": lead.funnel_stage,
        "referral_source": lead.referral_source,
        "market_intel_json": lead.market_intel_json,
        "benchmark_json": lead.benchmark_json,
        "readiness_json": lead.readiness_json,
        "created_at": lead.created_at.isoformat() if lead.created_at else None,
    }


@router.patch("/leads/{lead_id}/funnel")
async def update_lead_funnel(
    lead_id: str,
    body: LeadFunnelUpdate,
    db: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """Advance a lead through the funnel stages.

    Stages: report_requested > report_downloaded > contacted > qualified > engaged
    """
    from munipal.core.models.lead import SensingLead, SensingEvent

    if body.funnel_stage not in VALID_FUNNEL_STAGES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid stage '{body.funnel_stage}'. Valid: {VALID_FUNNEL_STAGES}",
        )

    lead = await db.get(SensingLead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail=f"Lead {lead_id} not found")

    old_stage = lead.funnel_stage
    lead.funnel_stage = body.funnel_stage

    # Record the funnel transition as an event
    db.add(SensingEvent(
        lead_id=lead.id,
        session_id=f"admin-{lead.id}",
        event_type=f"funnel_{body.funnel_stage}",
        sector=lead.sector,
        event_data=json.dumps({"from_stage": old_stage, "to_stage": body.funnel_stage}),
    ))

    await db.commit()
    await db.refresh(lead)

    return {
        "lead_id": lead.id,
        "previous_stage": old_stage,
        "funnel_stage": lead.funnel_stage,
    }


@router.post("/leads/{lead_id}/convert-to-project")
async def convert_lead_to_project(
    lead_id: str,
    body: LeadConvertRequest,
    db: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """Convert a sensing lead into a BFMS project.

    This is the critical handoff from top-of-funnel sensing to the advisory
    engagement workflow. It:
    1. Creates a new Project pre-populated from lead data
    2. Advances the lead funnel stage to 'engaged'
    3. Records a conversion event
    4. Returns the new project ID for immediate use

    The project is created with:
    - name: derived from organization + sector
    - issuer_name: from lead organization
    - target_bond_amount: from lead deal_size_estimate
    - project_location: from lead state
    """
    from munipal.core.models.lead import SensingLead, SensingEvent

    lead = await db.get(SensingLead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail=f"Lead {lead_id} not found")

    if lead.funnel_stage == "engaged":
        raise HTTPException(
            status_code=409,
            detail="Lead already converted to a project",
        )

    # Build project name
    project_name = body.project_name or f"{lead.organization} Bond Advisory"

    # Create the project via the service
    from munipal.core.schemas.project import ProjectCreate
    from munipal.services.project_service import ProjectService

    project_data = ProjectCreate(
        name=project_name,
        description=(
            f"Advisory engagement originated from sensing lead. "
            f"Sector: {lead.sector}. Contact: {lead.name} ({lead.email}). "
            f"Rating expectation: {lead.expected_rating or 'TBD'}."
        ),
        issuer_name=lead.organization,
        project_location=lead.state,
        target_bond_amount=lead.deal_size_estimate,
        playbook_id=body.playbook_id,
    )

    service = ProjectService(db)
    project = await service.create(
        project_data,
        owner_id=body.owner_id,
        tenant_id=body.tenant_id,
    )

    # Advance lead funnel to engaged
    old_stage = lead.funnel_stage
    lead.funnel_stage = "engaged"

    # Record conversion event
    db.add(SensingEvent(
        lead_id=lead.id,
        session_id=f"conversion-{lead.id}",
        event_type="converted_to_project",
        sector=lead.sector,
        event_data=json.dumps({
            "project_id": str(project.id),
            "project_name": project_name,
            "from_stage": old_stage,
        }),
    ))

    await db.commit()

    return {
        "lead_id": lead.id,
        "project_id": str(project.id),
        "project_name": project_name,
        "funnel_stage": "engaged",
        "status": "converted",
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _validate_sector(sector: str) -> None:
    """Raise 404 if sector doesn't have a corpus."""
    available = [s["id"] for s in sensing.get_available_sectors()]
    if sector not in available:
        raise HTTPException(
            status_code=404,
            detail=f"Sector '{sector}' not found. Available: {available}",
        )
