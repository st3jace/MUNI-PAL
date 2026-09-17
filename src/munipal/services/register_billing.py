"""Verified, idempotent per-deal fulfillment; never grants a subscription."""

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from munipal.core.models.register import RegisterDeal, RegisterPaymentReversal


async def payment_lock(db, payment_intent):
    # Serialize refund/completion even before the deal stores the payment intent.
    if db.get_bind().dialect.name == "postgresql":
        await db.execute(
            text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"), {"key": payment_intent}
        )


async def fulfill_register_checkout(db: AsyncSession, data: dict) -> None:
    metadata = data.get("metadata") or {}
    if data.get("payment_intent"):
        await payment_lock(db, data["payment_intent"])
    deal = await db.scalar(
        select(RegisterDeal)
        .where(
            RegisterDeal.id == metadata.get("register_deal_id"),
        )
        .with_for_update()
    )
    if not deal or deal.payment_status != "awaiting_payment":
        return
    if (
        data.get("mode") != "payment"
        or data.get("payment_status") != "paid"
        or data.get("id") != deal.checkout_session_id
        or metadata.get("munipal_user_id") != deal.owner_id
        or metadata.get("register_quote_version") != str(deal.quote_version)
        or data.get("amount_total") != deal.amount_cents
        or data.get("currency") != deal.currency
        or not data.get("payment_intent")
    ):
        return
    revoked = await db.get(RegisterPaymentReversal, data["payment_intent"])
    deal.payment_status = "refunded" if revoked else "paid"
    deal.payment_intent_id = data["payment_intent"]
    await db.commit()


async def expire_register_checkout(db: AsyncSession, data: dict) -> None:
    if not data.get("id"):
        return
    deal = await db.scalar(
        select(RegisterDeal)
        .where(
            RegisterDeal.checkout_session_id == data["id"],
        )
        .with_for_update()
    )
    if deal and deal.payment_status == "awaiting_payment":
        deal.checkout_session_id = None
        deal.checkout_url = None
        deal.quote_version += 1  # New idempotency key for a fresh checkout.
        await db.commit()


async def refund_register_payment(db: AsyncSession, data: dict) -> None:
    if not data.get("payment_intent") or not data.get("refunded"):
        return
    await payment_lock(db, data["payment_intent"])
    if not await db.get(RegisterPaymentReversal, data["payment_intent"]):
        db.add(RegisterPaymentReversal(payment_intent_id=data["payment_intent"]))
    deal = await db.scalar(
        select(RegisterDeal)
        .where(
            RegisterDeal.payment_intent_id == data["payment_intent"],
        )
        .with_for_update()
    )
    if deal:
        deal.payment_status = "refunded"
    await db.commit()
