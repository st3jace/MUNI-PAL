"""Integration tests for notification_service — notify_new_lead, email, and Telegram."""

import json
from unittest.mock import AsyncMock, patch

import pytest

from munipal.services.notification_service import (
    _send_lead_email,
    _send_telegram,
    notify_new_lead,
)


SAMPLE_LEAD = {
    "id": "lead-001",
    "name": "John CFO",
    "email": "john@hospital.org",
    "organization": "Metro Health System",
    "title": "Chief Financial Officer",
    "sector": "healthcare",
    "state": "TX",
    "expected_rating": "A",
    "deal_size_estimate": 50_000_000,
    "readiness_json": json.dumps(
        {
            "overall_score": 74,
            "tier": "moderate",
            "dimensions": [
                {"dimension": "Financial", "score": 82},
                {"dimension": "Governance", "score": 58},
            ],
        }
    ),
}


class TestNotifyNewLead:
    @patch("munipal.services.notification_service._send_telegram", new_callable=AsyncMock)
    @patch("munipal.services.notification_service._send_lead_email", new_callable=AsyncMock)
    @patch("munipal.services.notification_service.settings")
    async def test_sends_both_when_configured(
        self, mock_settings, mock_email, mock_telegram
    ):
        mock_settings.lead_notify_email = "ops@muni-pal.io"
        mock_settings.resend_api_key = "re_test"
        mock_settings.telegram_bot_token = "bot123"
        mock_settings.telegram_chat_id = "-100123"

        await notify_new_lead(SAMPLE_LEAD)

        mock_email.assert_awaited_once_with(SAMPLE_LEAD)
        mock_telegram.assert_awaited_once_with(SAMPLE_LEAD)

    @patch("munipal.services.notification_service._send_telegram", new_callable=AsyncMock)
    @patch("munipal.services.notification_service._send_lead_email", new_callable=AsyncMock)
    @patch("munipal.services.notification_service.settings")
    async def test_skips_email_when_not_configured(
        self, mock_settings, mock_email, mock_telegram
    ):
        mock_settings.lead_notify_email = ""
        mock_settings.resend_api_key = ""
        mock_settings.telegram_bot_token = "bot123"
        mock_settings.telegram_chat_id = "-100123"

        await notify_new_lead(SAMPLE_LEAD)

        mock_email.assert_not_awaited()
        mock_telegram.assert_awaited_once()

    @patch("munipal.services.notification_service._send_telegram", new_callable=AsyncMock)
    @patch("munipal.services.notification_service._send_lead_email", new_callable=AsyncMock)
    @patch("munipal.services.notification_service.settings")
    async def test_skips_telegram_when_not_configured(
        self, mock_settings, mock_email, mock_telegram
    ):
        mock_settings.lead_notify_email = "ops@test.com"
        mock_settings.resend_api_key = "re_key"
        mock_settings.telegram_bot_token = ""
        mock_settings.telegram_chat_id = ""

        await notify_new_lead(SAMPLE_LEAD)

        mock_email.assert_awaited_once()
        mock_telegram.assert_not_awaited()

    @patch("munipal.services.notification_service._send_telegram", new_callable=AsyncMock)
    @patch("munipal.services.notification_service._send_lead_email", new_callable=AsyncMock)
    @patch("munipal.services.notification_service.settings")
    async def test_continues_after_email_failure(
        self, mock_settings, mock_email, mock_telegram
    ):
        mock_settings.lead_notify_email = "ops@test.com"
        mock_settings.resend_api_key = "re_key"
        mock_settings.telegram_bot_token = "bot"
        mock_settings.telegram_chat_id = "-1"
        mock_email.side_effect = Exception("Resend down")

        await notify_new_lead(SAMPLE_LEAD)

        mock_telegram.assert_awaited_once()


class TestSendLeadEmail:
    @patch("munipal.services.notification_service.send_email", new_callable=AsyncMock)
    async def test_email_contains_lead_details(self, mock_send):
        mock_send.return_value = {"id": "msg_1"}

        await _send_lead_email(SAMPLE_LEAD)

        mock_send.assert_awaited_once()
        call_kwargs = mock_send.call_args[1]
        assert "John CFO" in call_kwargs["subject"]
        assert "Metro Health System" in call_kwargs["subject"]
        assert "john@hospital.org" in call_kwargs["html"]
        assert "$50.0M" in call_kwargs["html"]
        assert "74%" in call_kwargs["html"]

    @patch("munipal.services.notification_service.send_email", new_callable=AsyncMock)
    async def test_email_with_no_readiness(self, mock_send):
        mock_send.return_value = {"id": "msg_2"}
        lead = {**SAMPLE_LEAD, "readiness_json": None}

        await _send_lead_email(lead)

        html = mock_send.call_args[1]["html"]
        assert "N/A" in html


class TestSendTelegram:
    @patch("munipal.services.notification_service.httpx.AsyncClient")
    async def test_telegram_posts_message(self, mock_client_cls):
        from unittest.mock import MagicMock

        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_resp
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        await _send_telegram(SAMPLE_LEAD)

        call_kwargs = mock_client.post.call_args
        payload = call_kwargs[1]["json"]
        assert "John CFO" in payload["text"]
        assert "Metro Health System" in payload["text"]
        assert payload["parse_mode"] == "Markdown"

    @patch("munipal.services.notification_service.httpx.AsyncClient")
    async def test_telegram_with_missing_optional_fields(self, mock_client_cls):
        from unittest.mock import MagicMock

        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_resp
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        lead = {
            "id": "lead-002",
            "name": "Simple Lead",
            "email": "s@x.com",
            "organization": "Small Clinic",
            "deal_size_estimate": None,
            "readiness_json": None,
        }

        await _send_telegram(lead)

        payload = mock_client.post.call_args[1]["json"]
        assert "Simple Lead" in payload["text"]
        assert "TBD" in payload["text"]
