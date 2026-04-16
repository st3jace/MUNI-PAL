"""Integration tests for Stripe checkout and webhook routes."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy import select

from munipal.api.dependencies import DEV_FALLBACK_USER_ID
from munipal.core.models import User


@pytest.fixture
async def stripe_user(db_session):
    """Create a user for Stripe checkout tests."""
    user = User(
        id=DEV_FALLBACK_USER_ID,
        email="payer@example.com",
        hashed_password="unused",
        full_name="Payer",
        subscription_tier="free",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def stripe_user_with_customer(db_session):
    """Create a user who already has a Stripe customer ID."""
    user = User(
        id=DEV_FALLBACK_USER_ID,
        email="returning@example.com",
        hashed_password="unused",
        full_name="Returner",
        subscription_tier="free",
        stripe_customer_id="cus_existing123",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


class TestCreateCheckoutSession:
    """POST /api/v1/stripe/create-checkout-session"""

    @patch("munipal.api.routes.stripe.stripe.checkout.Session.create")
    async def test_checkout_success(self, mock_create, test_client, stripe_user):
        mock_session = MagicMock()
        mock_session.url = "https://checkout.stripe.com/pay/cs_test_123"
        mock_create.return_value = mock_session

        resp = await test_client.post(
            "/api/v1/stripe/create-checkout-session",
            json={"price_id": "price_abc"},
        )
        assert resp.status_code == 200
        assert resp.json()["url"] == "https://checkout.stripe.com/pay/cs_test_123"

        call_kwargs = mock_create.call_args[1]
        assert call_kwargs["customer_email"] == "payer@example.com"
        assert call_kwargs["mode"] == "subscription"

    @patch("munipal.api.routes.stripe.stripe.checkout.Session.create")
    async def test_checkout_existing_customer_uses_customer_id(
        self, mock_create, test_client, stripe_user_with_customer
    ):
        mock_session = MagicMock()
        mock_session.url = "https://checkout.stripe.com/pay/cs_test_456"
        mock_create.return_value = mock_session

        resp = await test_client.post(
            "/api/v1/stripe/create-checkout-session",
            json={"price_id": "price_xyz"},
        )
        assert resp.status_code == 200

        call_kwargs = mock_create.call_args[1]
        assert "customer_email" not in call_kwargs
        assert call_kwargs["customer"] == "cus_existing123"

    @patch("munipal.api.routes.stripe.stripe.checkout.Session.create")
    async def test_checkout_stripe_error(self, mock_create, test_client, stripe_user):
        import stripe as stripe_lib

        mock_create.side_effect = stripe_lib.InvalidRequestError(
            "No such price", param="price_id"
        )
        resp = await test_client.post(
            "/api/v1/stripe/create-checkout-session",
            json={"price_id": "price_bad"},
        )
        assert resp.status_code == 400

    @patch("munipal.api.routes.stripe.stripe.checkout.Session.create")
    async def test_checkout_no_url_returned(self, mock_create, test_client, stripe_user):
        mock_session = MagicMock()
        mock_session.url = None
        mock_create.return_value = mock_session

        resp = await test_client.post(
            "/api/v1/stripe/create-checkout-session",
            json={"price_id": "price_ok"},
        )
        assert resp.status_code == 502


class TestStripeWebhook:
    """POST /api/v1/stripe/webhook"""

    def _build_event(self, event_type: str, data_object: dict) -> dict:
        return {
            "type": event_type,
            "data": {"object": data_object},
        }

    @patch("munipal.api.routes.stripe.stripe.Webhook.construct_event")
    async def test_checkout_completed_provisions_subscription(
        self, mock_construct, test_client, db_session
    ):
        user = User(
            email="buyer@example.com",
            hashed_password="unused",
            subscription_tier="free",
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        event = self._build_event(
            "checkout.session.completed",
            {
                "customer_details": {"email": "buyer@example.com"},
                "customer": "cus_new",
                "subscription": "sub_new",
                "metadata": {"munipal_user_id": user.id},
            },
        )
        mock_construct.return_value = event

        resp = await test_client.post(
            "/api/v1/stripe/webhook",
            content=b"raw-body",
            headers={"stripe-signature": "sig"},
        )
        assert resp.status_code == 200

        await db_session.refresh(user)
        assert user.subscription_tier == "subscription"
        assert user.stripe_customer_id == "cus_new"
        assert user.stripe_subscription_id == "sub_new"

    @patch("munipal.api.routes.stripe.stripe.Webhook.construct_event")
    async def test_subscription_canceled_downgrades(
        self, mock_construct, test_client, db_session
    ):
        user = User(
            email="canceler@example.com",
            hashed_password="unused",
            subscription_tier="subscription",
            stripe_subscription_id="sub_cancel",
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        event = self._build_event(
            "customer.subscription.deleted",
            {"id": "sub_cancel", "status": "canceled"},
        )
        mock_construct.return_value = event

        resp = await test_client.post(
            "/api/v1/stripe/webhook",
            content=b"raw-body",
            headers={"stripe-signature": "sig"},
        )
        assert resp.status_code == 200

        await db_session.refresh(user)
        assert user.subscription_tier == "free"
        assert user.stripe_subscription_id is None

    @patch("munipal.api.routes.stripe.stripe.Webhook.construct_event")
    async def test_subscription_active_keeps_subscription(
        self, mock_construct, test_client, db_session
    ):
        user = User(
            email="active@example.com",
            hashed_password="unused",
            subscription_tier="subscription",
            stripe_subscription_id="sub_active",
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        event = self._build_event(
            "customer.subscription.updated",
            {"id": "sub_active", "status": "active"},
        )
        mock_construct.return_value = event

        resp = await test_client.post(
            "/api/v1/stripe/webhook",
            content=b"raw-body",
            headers={"stripe-signature": "sig"},
        )
        assert resp.status_code == 200

        await db_session.refresh(user)
        assert user.subscription_tier == "subscription"

    @patch("munipal.api.routes.stripe.stripe.Webhook.construct_event")
    async def test_webhook_invalid_signature(self, mock_construct, test_client):
        import stripe as stripe_lib

        mock_construct.side_effect = stripe_lib.SignatureVerificationError(
            "bad sig", sig_header="sig"
        )
        resp = await test_client.post(
            "/api/v1/stripe/webhook",
            content=b"body",
            headers={"stripe-signature": "bad"},
        )
        assert resp.status_code == 400

    @patch("munipal.api.routes.stripe.stripe.Webhook.construct_event")
    async def test_webhook_invalid_payload(self, mock_construct, test_client):
        mock_construct.side_effect = ValueError("bad json")
        resp = await test_client.post(
            "/api/v1/stripe/webhook",
            content=b"bad",
            headers={"stripe-signature": "sig"},
        )
        assert resp.status_code == 400

    @patch("munipal.api.routes.stripe.stripe.Webhook.construct_event")
    async def test_payment_failed_returns_ok(self, mock_construct, test_client):
        event = self._build_event(
            "invoice.payment_failed",
            {"customer_email": "fail@example.com"},
        )
        mock_construct.return_value = event

        resp = await test_client.post(
            "/api/v1/stripe/webhook",
            content=b"body",
            headers={"stripe-signature": "sig"},
        )
        assert resp.status_code == 200
