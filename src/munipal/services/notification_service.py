"""
Internal lead notification service.

Sends notifications to the team when a new lead is captured:
- Email to operations@muni-pal.io (via Resend)
- Telegram message to the Muni-Pal bot channel
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from munipal.config import get_settings
from munipal.services.email_service import send_email, _format_currency, _parse_readiness

logger = logging.getLogger(__name__)
settings = get_settings()


async def notify_new_lead(lead_data: dict[str, Any]) -> None:
    """Send internal notifications for a newly captured lead."""
    errors: list[str] = []

    # Email notification
    if settings.lead_notify_email and settings.resend_api_key:
        try:
            await _send_lead_email(lead_data)
        except Exception as e:
            logger.error("Lead email notification failed: %s", e)
            errors.append(f"email: {e}")

    # Telegram notification
    if settings.telegram_bot_token and settings.telegram_chat_id:
        try:
            await _send_telegram(lead_data)
        except Exception as e:
            logger.error("Telegram notification failed: %s", e)
            errors.append(f"telegram: {e}")

    if errors:
        logger.warning("Some notifications failed for lead %s: %s", lead_data.get("id"), errors)


async def _send_lead_email(lead: dict[str, Any]) -> None:
    """Send lead notification email to the team."""
    r = _parse_readiness(lead.get("readiness_json"))
    score_display = f"{r['score']}%" if r["score"] is not None else "N/A"
    deal_size = _format_currency(lead.get("deal_size_estimate"))

    gap_list = ""
    for g in r["gaps"]:
        gap_list += f"<li>{g['name']} — {g['score']}%</li>"
    if not gap_list:
        gap_list = "<li>None identified</li>"

    subject = f"🔔 New Lead: {lead['name']} ({lead['organization']})"
    html = f"""
    <div style="font-family:system-ui,sans-serif;max-width:600px;color:#1a1a1a">
      <h2>New Sensing Lead Captured</h2>
      <table style="border-collapse:collapse;width:100%">
        <tr><td style="padding:6px 12px;font-weight:600">Name</td>
            <td style="padding:6px 12px">{lead['name']}</td></tr>
        <tr style="background:#f5f5f5">
            <td style="padding:6px 12px;font-weight:600">Organization</td>
            <td style="padding:6px 12px">{lead['organization']}</td></tr>
        <tr><td style="padding:6px 12px;font-weight:600">Email</td>
            <td style="padding:6px 12px"><a href="mailto:{lead['email']}">{lead['email']}</a></td></tr>
        <tr style="background:#f5f5f5">
            <td style="padding:6px 12px;font-weight:600">Title</td>
            <td style="padding:6px 12px">{lead.get('title') or '—'}</td></tr>
        <tr><td style="padding:6px 12px;font-weight:600">Sector</td>
            <td style="padding:6px 12px">{lead.get('sector', '—')}</td></tr>
        <tr style="background:#f5f5f5">
            <td style="padding:6px 12px;font-weight:600">Deal Size</td>
            <td style="padding:6px 12px">{deal_size}</td></tr>
        <tr><td style="padding:6px 12px;font-weight:600">State</td>
            <td style="padding:6px 12px">{lead.get('state') or '—'}</td></tr>
        <tr style="background:#f5f5f5">
            <td style="padding:6px 12px;font-weight:600">Expected Rating</td>
            <td style="padding:6px 12px">{lead.get('expected_rating') or '—'}</td></tr>
        <tr><td style="padding:6px 12px;font-weight:600">Readiness Score</td>
            <td style="padding:6px 12px">{score_display} ({r['tier']})</td></tr>
      </table>

      <h3>Top Gaps</h3>
      <ul>{gap_list}</ul>

      <p><a href="{settings.app_base_url}/admin/leads/{lead.get('id', '')}"
            style="color:#1e3a5f;font-weight:600">View Lead Detail →</a></p>
    </div>
    """
    await send_email(
        to=settings.lead_notify_email,
        subject=subject,
        html=html,
    )


async def _send_telegram(lead: dict[str, Any]) -> None:
    """Send lead notification to Telegram channel."""
    r = _parse_readiness(lead.get("readiness_json"))
    score_display = f"{r['score']}%" if r["score"] is not None else "N/A"
    deal_size = _format_currency(lead.get("deal_size_estimate"))

    gaps_text = ""
    for g in r["gaps"]:
        gaps_text += f"\n  • {g['name']} ({g['score']}%)"
    if not gaps_text:
        gaps_text = "\n  • None identified"

    text = (
        f"🔔 *New Lead Captured*\n\n"
        f"*{lead['name']}* — {lead['organization']}\n"
        f"📧 {lead['email']}\n"
        f"📊 Score: {score_display} ({r['tier']})\n"
        f"💰 Deal: {deal_size}\n"
        f"📍 {lead.get('state') or '—'} · {lead.get('sector', '—')}\n"
        f"\n*Top Gaps:*{gaps_text}"
    )

    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            url,
            json={
                "chat_id": settings.telegram_chat_id,
                "text": text,
                "parse_mode": "Markdown",
            },
            timeout=10.0,
        )
        resp.raise_for_status()
