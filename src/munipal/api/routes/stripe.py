"""Stripe Checkout routes for subscription billing."""

import os

import stripe
from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel

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
async def create_checkout_session(payload: CheckoutRequest):
    """Create a Stripe Checkout Session and return the hosted URL."""
    try:
        session = stripe.checkout.Session.create(
            mode="subscription",
            line_items=[{"price": payload.price_id, "quantity": 1}],
            success_url=f"{_FRONTEND_URL}/pricing?checkout=success",
            cancel_url=f"{_FRONTEND_URL}/pricing?checkout=cancel",
        )
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
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events (checkout.session.completed, etc.)."""
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

    if event["type"] == "checkout.session.completed":
        session_data = event["data"]["object"]
        # TODO: provision subscription access for customer
        customer_email = session_data.get("customer_details", {}).get("email")
        subscription_id = session_data.get("subscription")
        print(
            f"[stripe] checkout.session.completed — "
            f"email={customer_email} subscription={subscription_id}"
        )

    return {"status": "ok"}
