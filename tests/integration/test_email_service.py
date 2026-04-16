"""Integration tests for email_service — send_email, helpers, and template renderers."""

import json
from unittest.mock import AsyncMock, patch

import pytest

from munipal.services.email_service import (
    EMAIL_RENDERERS,
    EMAIL_SCHEDULE_DAYS,
    _footer,
    _format_currency,
    _parse_readiness,
    _unsubscribe_url,
    render_email_1,
    render_email_2,
    render_email_3,
    render_email_4,
    send_email,
)


# ---------------------------------------------------------------------------
# Helper function tests
# ---------------------------------------------------------------------------


class TestFormatCurrency:
    def test_none(self):
        assert _format_currency(None) == "TBD"

    def test_millions(self):
        assert _format_currency(5_000_000) == "$5.0M"

    def test_below_million(self):
        assert _format_currency(750_000) == "$750,000"

    def test_zero(self):
        assert _format_currency(0) == "$0"


class TestParseReadiness:
    def test_none_input(self):
        result = _parse_readiness(None)
        assert result == {"score": None, "tier": "Unknown", "gaps": []}

    def test_empty_string(self):
        result = _parse_readiness("")
        assert result["score"] is None

    def test_invalid_json(self):
        result = _parse_readiness("{bad json")
        assert result["tier"] == "Unknown"

    def test_valid_readiness(self):
        data = {
            "overall_score": 72,
            "tier": "moderate",
            "dimensions": [
                {"dimension": "Financial", "score": 85},
                {"dimension": "Governance", "score": 55},
                {"dimension": "Legal", "score": 60},
                {"dimension": "Technical", "score": 90},
            ],
        }
        result = _parse_readiness(json.dumps(data))
        assert result["score"] == 72
        assert result["tier"] == "moderate"
        assert len(result["gaps"]) == 2
        # Gaps sorted by score ascending
        assert result["gaps"][0]["name"] == "Governance"
        assert result["gaps"][1]["name"] == "Legal"

    def test_top_3_gaps_only(self):
        data = {
            "score": 50,
            "tier": "low",
            "dimensions": [
                {"name": f"dim{i}", "score": 10 + i} for i in range(6)
            ],
        }
        result = _parse_readiness(json.dumps(data))
        assert len(result["gaps"]) == 3


class TestUnsubscribeUrl:
    def test_format(self):
        url = _unsubscribe_url("tok123")
        assert "unsubscribe" in url
        assert "tok123" in url


class TestFooter:
    def test_contains_unsubscribe_link(self):
        html = _footer("abc")
        assert "Unsubscribe" in html
        assert "abc" in html


# ---------------------------------------------------------------------------
# Template renderers
# ---------------------------------------------------------------------------


SAMPLE_LEAD = {
    "name": "Jane Doe",
    "email": "jane@hospital.org",
    "organization": "County General Hospital",
    "sector": "healthcare",
    "deal_size_estimate": 25_000_000,
    "readiness_json": json.dumps(
        {
            "overall_score": 68,
            "tier": "moderate",
            "dimensions": [
                {"dimension": "Financial", "score": 80},
                {"dimension": "Governance", "score": 45},
            ],
        }
    ),
}


class TestRenderEmail1:
    def test_subject_contains_score(self):
        subject, html = render_email_1(SAMPLE_LEAD, "tok")
        assert "68%" in subject
        assert "Moderate" in subject

    def test_html_contains_name_and_org(self):
        _, html = render_email_1(SAMPLE_LEAD, "tok")
        assert "Jane Doe" in html
        assert "County General Hospital" in html

    def test_html_shows_gaps(self):
        _, html = render_email_1(SAMPLE_LEAD, "tok")
        assert "Governance" in html

    def test_no_readiness_data(self):
        lead = {**SAMPLE_LEAD, "readiness_json": None}
        subject, html = render_email_1(lead, "tok")
        assert "Pending" in subject


class TestRenderEmail2:
    def test_subject_contains_sector(self):
        subject, _ = render_email_2(SAMPLE_LEAD, "tok")
        assert "Healthcare" in subject

    def test_html_has_benchmarks(self):
        _, html = render_email_2(SAMPLE_LEAD, "tok")
        assert "DSCR" in html
        assert "COI" in html


class TestRenderEmail3:
    def test_html_contains_deal_size(self):
        _, html = render_email_3(SAMPLE_LEAD, "tok")
        assert "$25.0M" in html

    def test_deal_size_none(self):
        lead = {**SAMPLE_LEAD, "deal_size_estimate": None}
        _, html = render_email_3(lead, "tok")
        assert "TBD" in html


class TestRenderEmail4:
    def test_html_contains_score(self):
        _, html = render_email_4(SAMPLE_LEAD, "tok")
        assert "68%" in html

    def test_pricing_tiers_shown(self):
        _, html = render_email_4(SAMPLE_LEAD, "tok")
        assert "Diagnostic" in html
        assert "Standard Engagement" in html
        assert "Accelerator" in html


class TestEmailRendererMap:
    def test_all_steps_mapped(self):
        assert set(EMAIL_RENDERERS.keys()) == {1, 2, 3, 4}

    def test_schedule_days(self):
        assert EMAIL_SCHEDULE_DAYS[1] == 0
        assert EMAIL_SCHEDULE_DAYS[4] == 14


# ---------------------------------------------------------------------------
# send_email (mocking httpx)
# ---------------------------------------------------------------------------


class TestSendEmail:
    @patch("munipal.services.email_service.httpx.AsyncClient")
    async def test_send_email_posts_to_resend(self, mock_client_cls):
        from unittest.mock import MagicMock

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"id": "email_123"}
        mock_resp.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_resp
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        result = await send_email(
            to="test@example.com",
            subject="Test Subject",
            html="<p>Hello</p>",
            reply_to="reply@example.com",
        )

        assert result == {"id": "email_123"}
        call_kwargs = mock_client.post.call_args
        payload = call_kwargs[1]["json"]
        assert payload["to"] == ["test@example.com"]
        assert payload["subject"] == "Test Subject"
        assert payload["reply_to"] == "reply@example.com"

    @patch("munipal.services.email_service.httpx.AsyncClient")
    async def test_send_email_without_reply_to(self, mock_client_cls):
        from unittest.mock import MagicMock

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"id": "email_456"}
        mock_resp.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_resp
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        await send_email(to="t@x.com", subject="S", html="<p>H</p>")

        payload = mock_client.post.call_args[1]["json"]
        assert "reply_to" not in payload
