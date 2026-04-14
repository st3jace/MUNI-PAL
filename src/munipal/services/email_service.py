"""
Email service using Resend for transactional email delivery.

Handles the 4-email drip sequence for sensing leads and internal
lead notifications. All emails include CAN-SPAM compliant unsubscribe links.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from munipal.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

RESEND_API_URL = "https://api.resend.com/emails"


async def send_email(
    to: str,
    subject: str,
    html: str,
    reply_to: str | None = None,
) -> dict[str, Any]:
    """Send an email via Resend API."""
    payload: dict[str, Any] = {
        "from": f"{settings.email_from_name} <{settings.email_from_address}>",
        "to": [to],
        "subject": subject,
        "html": html,
    }
    if reply_to:
        payload["reply_to"] = reply_to

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            RESEND_API_URL,
            headers={
                "Authorization": f"Bearer {settings.resend_api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=15.0,
        )
        resp.raise_for_status()
        return resp.json()


def _unsubscribe_url(token: str) -> str:
    return f"{settings.app_base_url}/api/v1/sensing/unsubscribe?token={token}"


def _format_currency(amount: float | None) -> str:
    if amount is None:
        return "TBD"
    if amount >= 1_000_000:
        return f"${amount / 1_000_000:.1f}M"
    return f"${amount:,.0f}"


def _parse_readiness(readiness_json: str | None) -> dict[str, Any]:
    """Extract score, tier, and top gaps from readiness JSON snapshot."""
    if not readiness_json:
        return {"score": None, "tier": "Unknown", "gaps": []}
    try:
        data = json.loads(readiness_json)
        score = data.get("overall_score") or data.get("score")
        tier = data.get("tier") or data.get("tier_label") or "Unknown"
        # Extract top gaps from dimension scores
        gaps = []
        for dim in data.get("dimensions", data.get("dimension_scores", [])):
            if isinstance(dim, dict):
                name = dim.get("dimension") or dim.get("name", "")
                dim_score = dim.get("score", 100)
                if dim_score < 70:
                    gaps.append({"name": name, "score": dim_score})
        gaps.sort(key=lambda g: g["score"])
        return {"score": score, "tier": tier, "gaps": gaps[:3]}
    except (json.JSONDecodeError, TypeError):
        return {"score": None, "tier": "Unknown", "gaps": []}


def _footer(unsubscribe_token: str) -> str:
    unsub_url = _unsubscribe_url(unsubscribe_token)
    return f"""
    <hr style="border:none;border-top:1px solid #e0e0e0;margin:32px 0 16px"/>
    <p style="font-size:12px;color:#888;line-height:1.5">
      Muni-Pal &middot; Bond readiness insights for municipal issuers<br/>
      <a href="{unsub_url}" style="color:#888">Unsubscribe</a> from this email sequence.
    </p>
    """


# ─── Email Templates ─────────────────────────────────────────────────────


def render_email_1(lead: dict[str, Any], unsub_token: str) -> tuple[str, str]:
    """Email 1 (immediate): Score recap + top gaps."""
    r = _parse_readiness(lead.get("readiness_json"))
    score = r["score"]
    tier = r["tier"]
    gaps = r["gaps"]

    score_display = f"{score}%" if score is not None else "Pending"
    tier_label = tier.replace("_", " ").title()

    gap_rows = ""
    for g in gaps:
        gap_rows += f"<li><strong>{g['name']}</strong> — {g['score']}%</li>\n"
    if not gap_rows:
        gap_rows = "<li>No critical gaps identified</li>"

    subject = f"Your Bond Readiness Score: {score_display} — {tier_label}"
    html = f"""
    <div style="font-family:system-ui,sans-serif;max-width:600px;margin:0 auto;color:#1a1a1a">
      <h2 style="color:#1e3a5f">Your Bond Readiness Assessment</h2>
      <p>Hi {lead['name']},</p>
      <p>Thank you for completing the readiness assessment for <strong>{lead['organization']}</strong>.
      Here's a summary of your results:</p>

      <div style="background:#f0f4f8;border-radius:8px;padding:20px;margin:16px 0;text-align:center">
        <p style="font-size:14px;color:#666;margin:0">Overall Score</p>
        <p style="font-size:48px;font-weight:700;color:#1e3a5f;margin:8px 0">{score_display}</p>
        <p style="font-size:16px;color:#4a7c59;margin:0">Tier: {tier_label}</p>
      </div>

      <h3>Top Readiness Gaps</h3>
      <ul>{gap_rows}</ul>

      <p>These gaps have the highest impact on your cost of issuance and credit positioning.
      Addressing them before engaging an advisor can meaningfully improve your deal economics.</p>

      <p>
        <a href="{settings.app_base_url}/sensing/readiness"
           style="display:inline-block;padding:12px 24px;background:#1e3a5f;color:#fff;
                  text-decoration:none;border-radius:6px;font-weight:600">
          View Full Results
        </a>
      </p>

      {_footer(unsub_token)}
    </div>
    """
    return subject, html


def render_email_2(lead: dict[str, Any], unsub_token: str) -> tuple[str, str]:
    """Email 2 (day 3): Peer benchmarks."""
    sector = (lead.get("sector") or "municipal").replace("_", " ").title()

    subject = f"How your facility compares to {sector} peers"
    html = f"""
    <div style="font-family:system-ui,sans-serif;max-width:600px;margin:0 auto;color:#1a1a1a">
      <h2 style="color:#1e3a5f">Peer Benchmark Context</h2>
      <p>Hi {lead['name']},</p>
      <p>We analyzed EMMA data across {sector.lower()} issuers at similar readiness tiers.
      Here's what stands out:</p>

      <ul>
        <li><strong>DSCR benchmarks</strong> — Issuers in your tier typically maintain 1.15–1.35x
            debt service coverage. Where you fall in this range affects spread pricing.</li>
        <li><strong>COI positioning</strong> — {sector} issuers that improved readiness scores
            by 15+ points before going to market saw 8–22 bps tighter spreads on average.</li>
        <li><strong>What upgraded credits did differently</strong> — Early advisor engagement,
            structured evidence packages, and proactive disclosure.</li>
      </ul>

      <p>
        <a href="{settings.app_base_url}/sensing/benchmark"
           style="display:inline-block;padding:12px 24px;background:#1e3a5f;color:#fff;
                  text-decoration:none;border-radius:6px;font-weight:600">
          Run Your COI Benchmark
        </a>
      </p>
      <p>
        <a href="{settings.app_base_url}/sensing/market-intelligence"
           style="color:#1e3a5f;font-weight:600">
          Get Your Market Intelligence Report →
        </a>
      </p>

      {_footer(unsub_token)}
    </div>
    """
    return subject, html


def render_email_3(lead: dict[str, Any], unsub_token: str) -> tuple[str, str]:
    """Email 3 (day 7): Cost of inaction."""
    deal_size = _format_currency(lead.get("deal_size_estimate"))

    subject = "The $27M question: A vs. BBB on a $75M healthcare bond"
    html = f"""
    <div style="font-family:system-ui,sans-serif;max-width:600px;margin:0 auto;color:#1a1a1a">
      <h2 style="color:#1e3a5f">The Cost of Waiting</h2>
      <p>Hi {lead['name']},</p>
      <p>For a typical {deal_size} issuance, the spread differential between an A-rated
      and BBB-rated credit can translate to <strong>$1.5–4.2M in additional interest cost</strong>
      over the life of the bond.</p>

      <p>Our research across 866 EMMA transactions shows:</p>
      <ul>
        <li>Average spread differential: 45–85 bps between rating tiers</li>
        <li>Issuers who engaged readiness advisory 6+ months before pricing saw
            2x higher likelihood of rating uplift</li>
        <li>Evidence-ready issuers closed 3 weeks faster on average</li>
      </ul>

      <p>The gaps in your readiness assessment are addressable — most can be closed
      in 60–90 days with structured support.</p>

      <p>
        <a href="{settings.calendly_url or settings.app_base_url + '/contact'}"
           style="display:inline-block;padding:12px 24px;background:#1e3a5f;color:#fff;
                  text-decoration:none;border-radius:6px;font-weight:600">
          Talk to a Bond Readiness Advisor
        </a>
      </p>

      {_footer(unsub_token)}
    </div>
    """
    return subject, html


def render_email_4(lead: dict[str, Any], unsub_token: str) -> tuple[str, str]:
    """Email 4 (day 14): Advisory path CTA."""
    r = _parse_readiness(lead.get("readiness_json"))
    score = r["score"]
    score_display = f"{score}%" if score is not None else "your current score"

    subject = "From readiness score to deal-ready: your next step"
    html = f"""
    <div style="font-family:system-ui,sans-serif;max-width:600px;margin:0 auto;color:#1a1a1a">
      <h2 style="color:#1e3a5f">Your Path Forward</h2>
      <p>Hi {lead['name']},</p>
      <p>Based on your score of <strong>{score_display}</strong>, here's how Muni-Pal can
      help {lead['organization']} get deal-ready:</p>

      <table style="width:100%;border-collapse:collapse;margin:16px 0">
        <tr style="background:#f0f4f8">
          <td style="padding:12px;border:1px solid #ddd"><strong>Free</strong></td>
          <td style="padding:12px;border:1px solid #ddd">
            Self-service readiness tools, market intelligence, and benchmark reports.
            <em>You're already here.</em>
          </td>
        </tr>
        <tr>
          <td style="padding:12px;border:1px solid #ddd"><strong>Diagnostic</strong><br><span style="color:#4a7c59;font-size:13px">$15K–$25K</span></td>
          <td style="padding:12px;border:1px solid #ddd">
            Comprehensive readiness assessment, credit memo, gap analysis,
            and comparable deal structures with actionable timeline.
          </td>
        </tr>
        <tr style="background:#f0f4f8">
          <td style="padding:12px;border:1px solid #ddd"><strong>Standard Engagement</strong><br><span style="color:#4a7c59;font-size:13px">$40K–$50K</span></td>
          <td style="padding:12px;border:1px solid #ddd">
            Diagnostic + active deal coordination, COI benchmarking,
            milestone tracking, and dedicated point of contact.
          </td>
        </tr>
        <tr>
          <td style="padding:12px;border:1px solid #ddd"><strong>Accelerator</strong><br><span style="color:#4a7c59;font-size:13px">$75K+</span></td>
          <td style="padding:12px;border:1px solid #ddd">
            Full pre-issuance support — gap remediation, benchmarking,
            timeline optimization, and extended post-deal analysis.
          </td>
        </tr>
      </table>

      <p>Our research draws on 866 real transactions and 1,200+ EMMA filings.
      We've seen what works.</p>

      <p>
        <a href="{settings.calendly_url or settings.app_base_url + '/contact'}"
           style="display:inline-block;padding:12px 24px;background:#1e3a5f;color:#fff;
                  text-decoration:none;border-radius:6px;font-weight:600">
          Schedule a 20-Minute Readiness Review
        </a>
      </p>

      {_footer(unsub_token)}
    </div>
    """
    return subject, html


# ─── Email Renderer Map ──────────────────────────────────────────────────

EMAIL_RENDERERS = {
    1: render_email_1,
    2: render_email_2,
    3: render_email_3,
    4: render_email_4,
}

# Schedule: step → days after lead capture
EMAIL_SCHEDULE_DAYS = {
    1: 0,   # immediate
    2: 3,   # day 3
    3: 7,   # day 7
    4: 14,  # day 14
}
