"""Stripe Checkout routes for subscription billing."""

import os

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from munipal.api.dependencies import CurrentUserId, DbSession
from munipal.core.models import User
from munipal.db.session import get_async_session

router = APIRouter()

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")
_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")

# Allowed origin for redirect URLs
_FRONTEND_URL = os.environ.get("FRONTEND_URL", "https://muni-pal.io")


class CheckoutRequest(BaseModel):
    price_id: str


class CheckoutResponse(BaseModel):
    url: str


@router.post("/create-checkout-session", response_model=CheckoutResponse)
async def create_checkout_session(
    payload: CheckoutRequest,
    user_id: CurrentUserId,
    db: DbSession,
):
    """Create a Stripe Checkout Session for an authenticated user."""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found.")

    try:
        session_params: dict = {
            "mode": "subscription",
            "line_items": [{"price": payload.price_id, "quantity": 1}],
            "success_url": f"{_FRONTEND_URL}/pricing?checkout=success",
            "cancel_url": f"{_FRONTEND_URL}/pricing?checkout=cancel",
            "customer_email": user.email,
            "metadata": {"munipal_user_id": user.id},
        }
        if user.stripe_customer_id:
            session_params.pop("customer_email")
            session_params["customer"] = user.stripe_customer_id

        session = stripe.checkout.Session.create(**session_params)
    except stripe.InvalidRequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    if not session.url:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Stripe did not return a checkout URL.",
        )

    return CheckoutResponse(url=session.url)


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_async_session),
):
    """Handle Stripe webhook events."""
    body = await request.body()
    sig = request.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(body, sig, _WEBHOOK_SECRET)
    except stripe.SignatureVerificationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook signature.",
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payload.",
        )

    event_type = event["type"]
    data = event["data"]["object"]

    if event_type == "checkout.session.completed":
        await _provision_subscription(db, data)
    elif event_type in (
        "customer.subscription.updated",
        "customer.subscription.deleted",
    ):
        await _sync_subscription_status(db, data)
    elif event_type == "invoice.payment_failed":
        customer_email = data.get("customer_email")
        print(f"[stripe] payment failed for {customer_email}")

    return {"status": "ok"}


async def _provision_subscription(db: AsyncSession, session_data: dict) -> None:
    """Provision subscription access after successful checkout."""
    customer_email = session_data.get("customer_details", {}).get("email")
    customer_id = session_data.get("customer")
    subscription_id = session_data.get("subscription")
    munipal_user_id = session_data.get("metadata", {}).get("munipal_user_id")

    # Find user by metadata user ID or email
    user = None
    if munipal_user_id:
        user = await db.get(User, munipal_user_id)
    if not user and customer_email:
        result = await db.execute(select(User).where(User.email == customer_email))
        user = result.scalar_one_or_none()

    if not user:
        print(f"[stripe] checkout completed but user not found: email={customer_email}")
        return

    user.subscription_tier = "subscription"
    user.stripe_customer_id = customer_id
    user.stripe_subscription_id = subscription_id
    await db.commit()
    print(f"[stripe] provisioned subscription for user={user.id} email={user.email}")


async def _sync_subscription_status(db: AsyncSession, sub_data: dict) -> None:
    """Sync subscription status from Stripe events."""
    subscription_id = sub_data.get("id")
    sub_status = sub_data.get("status")

    result = await db.execute(
        select(User).where(User.stripe_subscription_id == subscription_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        print(f"[stripe] subscription event for unknown subscription={subscription_id}")
        return

    if sub_status in ("active", "trialing"):
        user.subscription_tier = "subscription"
    elif sub_status in ("canceled", "unpaid", "past_due"):
        user.subscription_tier = "free"
        if sub_status == "canceled":
            user.stripe_subscription_id = None

    await db.commit()
    print(f"[stripe] synced subscription status={sub_status} for user={user.id}")
