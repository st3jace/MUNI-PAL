"""Obligation Register intake — public endpoint behind the muni-pal.io landing page.

Product: 10-Day Obligation Register (LS-A2-POST). Post-close only.

The endpoint enforces the two hard gates from the intake spec (Hermosillo 2026-09-10,
Arthur letter 2026-09-09) on the server, not just in the browser:

  1. bonds_already_closed must be true. We do not do pre-issuance work on this product.
  2. entity_type must not be a municipal entity. We have no path for them today.

It stores the intake as a SensingLead (sector = "obligation-register") so it lands in the
same admin views as every other lead, and emails the team when Resend is configured.
Nothing here quotes a price, files anything, or says "compliant".
"""
from __future__ import annotations

import json
import logging
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from munipal.config import get_settings
from munipal.db.session import get_async_session

logger = logging.getLogger(__name__)
router = APIRouter()

INTAKE_PRIVACY_CONTRACT: dict[str, Any] = {
    "consent_version": "obligation-intake-v1",
    "consent_copy": (
        "I consent to Muni-Pal collecting my contact details, entity type, instrument "
        "list and professional contacts to confirm eligibility and reply with a fixed-fee quote."
    ),
}

PRE_ISSUANCE_STOP = (
    "This offer is for post-close obligated persons only. We do not build registers for "
    "deals that have not closed."
)
MUNICIPAL_STOP = "We have no path for municipal entities or public authorities today."


class ObligationRegisterIntake(BaseModel):
    """Intake form behind /obligation-register. Facts and contacts only. No judgment fields."""

    # Gate
    bonds_already_closed: bool = Field(..., description="Have the bonds already closed?")
    # Entity
    legal_name: str = Field(..., min_length=2, max_length=255)
    entity_type: Literal["private_obligated_person", "municipal_entity", "unclear"]
    state: str | None = Field(default=None, max_length=5)
    # Contact
    contact_name: str = Field(..., min_length=2, max_length=255)
    contact_title: str | None = Field(default=None, max_length=255)
    contact_email: EmailStr
    contact_phone: str | None = Field(default=None, max_length=50)
    # Professionals (they approve the list; judgment calls route here)
    bond_counsel_contact: str | None = Field(default=None, max_length=500)
    municipal_advisor_contact: str | None = Field(default=None, max_length=500)
    dissemination_agent_contact: str | None = Field(default=None, max_length=500)
    # Financings
    instrument_list: str = Field(..., min_length=3, max_length=4000)
    instrument_count: int | None = Field(default=None, ge=1, le=500)
    cda_present: Literal["yes", "no", "not_sure"] | None = None
    documents_on_hand: str | None = Field(default=None, max_length=4000)
    concurrent_preissuance: bool = Field(
        ..., description="Asking us to work a new or contemplated issuance at the same time?"
    )
    # Consent + session
    privacy_consent: bool = False
    consent_version: str = INTAKE_PRIVACY_CONTRACT["consent_version"]
    session_id: str | None = Field(default=None, max_length=100)


@router.get("/privacy")
async def intake_privacy_contract() -> dict[str, Any]:
    return INTAKE_PRIVACY_CONTRACT


@router.post("/intake")
async def submit_intake(
    request: ObligationRegisterIntake,
    db: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    from munipal.core.models.lead import SensingEvent, SensingLead

    if not request.bonds_already_closed:
        raise HTTPException(status_code=422, detail=PRE_ISSUANCE_STOP)
    if request.entity_type == "municipal_entity":
        raise HTTPException(status_code=422, detail=MUNICIPAL_STOP)
    if not request.privacy_consent:
        raise HTTPException(
            status_code=422,
            detail="Consent is required before we collect contact details and instrument information.",
        )

    intake = request.model_dump(exclude={"privacy_consent", "consent_version", "session_id"})
    intake["consent_version"] = request.consent_version
    # Two facts the team must see first. Neither is a judgment; both are the client's own answers.
    intake["flags"] = {
        "entity_unclear": request.entity_type == "unclear",
        "concurrent_preissuance": request.concurrent_preissuance,
        "no_professional_named": not any(
            [request.bond_counsel_contact, request.municipal_advisor_contact, request.dissemination_agent_contact]
        ),
    }

    lead = SensingLead(
        email=str(request.contact_email),
        name=request.contact_name,
        organization=request.legal_name,
        title=request.contact_title,
        phone=request.contact_phone,
        sector="obligation-register",
        state=request.state,
        referral_source="obligation-register-page",
        funnel_stage="intake_submitted",
        market_intel_json=json.dumps(intake),
    )
    db.add(lead)
    db.add(
        SensingEvent(
            lead_id=lead.id,
            session_id=request.session_id or f"intake-{lead.id}",
            event_type="obligation_register_intake",
            sector="obligation-register",
            event_data=json.dumps(intake["flags"]),
        )
    )
    await db.commit()
    await db.refresh(lead)

    await _notify_team(lead.id, intake)

    return {
        "lead_id": lead.id,
        "status": "received",
        "next": (
            "We will confirm eligibility and reply with a fixed-fee quote after we review "
            "instrument count and the CDA pack."
        ),
        "flags": intake["flags"],
    }


async def _notify_team(lead_id: str, intake: dict[str, Any]) -> None:
    """Email the team. Failure is logged, never surfaced to the prospect."""
    settings = get_settings()
    if not (settings.resend_api_key and settings.lead_notify_email):
        logger.info("Obligation Register intake %s stored; email notification not configured", lead_id)
        return
    try:
        from munipal.services.email_service import send_email

        flags = intake["flags"]
        rows = "".join(
            f"<tr><td style='padding:2px 8px;color:#555'>{k}</td><td style='padding:2px 8px'>{v}</td></tr>"
            for k, v in intake.items()
            if k != "flags" and v not in (None, "")
        )
        flag_line = ", ".join(k for k, v in flags.items() if v) or "none"
        html = (
            f"<h2>Obligation Register intake: {intake['legal_name']}</h2>"
            f"<p><b>Flags:</b> {flag_line}</p>"
            f"<table>{rows}</table>"
            f"<p style='color:#777;font-size:12px'>Lead {lead_id}. Quote after instrument count + CDA pack. "
            f"Never quote from this email alone.</p>"
        )
        await send_email(
            to=settings.lead_notify_email,
            subject=f"Obligation Register intake: {intake['legal_name']}",
            html=html,
            reply_to=intake.get("contact_email"),
        )
    except Exception as exc:  # noqa: BLE001 - notification must never break intake
        logger.error("Obligation Register intake %s: notification failed: %s", lead_id, exc)
