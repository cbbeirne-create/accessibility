"""Stripe subscription API routes: checkout and retry-safe idempotent webhooks."""
import logging
from datetime import datetime, timedelta, timezone

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from ...core.config import settings
from ...core.database import db
from ...core.security import get_current_user
from ...models.user import SubscriptionStatus, User, UserPlan

router = APIRouter(prefix="/subscription")
logger = logging.getLogger(__name__)
stripe.api_key = settings.STRIPE_SECRET_KEY


def create_stripe_checkout_session(customer_id: str, price_id: str, success_url: str, cancel_url: str):
    if not stripe.api_key:
        raise HTTPException(status_code=503, detail="Payment system not configured")
    if not price_id:
        raise HTTPException(status_code=503, detail="Subscription price is not configured")
    if not customer_id:
        raise HTTPException(status_code=400, detail="No payment profile found")
    try:
        return stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={"customer_id": customer_id},
        )
    except stripe.error.StripeError as exc:
        logger.error("Stripe checkout error: %s", exc)
        raise HTTPException(status_code=502, detail="Payment provider rejected the checkout request") from exc


@router.post("/create-checkout-session")
async def create_checkout_session(current_user: User = Depends(get_current_user)):
    try:
        session = create_stripe_checkout_session(
            customer_id=current_user.stripe_customer_id,
            price_id=settings.STRIPE_PRO_PRICE_ID,
            success_url=f"{settings.FRONTEND_URL}/dashboard?success=true",
            cancel_url=f"{settings.FRONTEND_URL}/pricing?canceled=true",
        )
        return {"checkout_url": session.url}
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Unexpected checkout failure")
        raise HTTPException(status_code=500, detail="Failed to create checkout session") from exc


async def _claim_stripe_event(event: dict) -> bool:
    """Claim a new/failed/stale event while rejecting duplicate active or completed delivery."""
    now = datetime.now(timezone.utc)
    try:
        claimed = await db.stripe_events.find_one_and_update(
            {
                "event_id": event["id"],
                "$or": [
                    {"status": "failed"},
                    {"status": "processing", "lock_until": {"$lte": now}},
                    {"status": {"$exists": False}},
                ],
            },
            {
                "$setOnInsert": {
                    "event_id": event["id"],
                    "event_type": event["type"],
                    "received_at": now,
                },
                "$set": {
                    "status": "processing",
                    "lock_until": now + timedelta(minutes=5),
                    "last_attempt_at": now,
                    "error": None,
                },
                "$inc": {"attempts": 1},
            },
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        return claimed is not None
    except DuplicateKeyError:
        # Existing event is either completed or currently being processed under a live lease.
        return False


@router.post("/webhook")
async def stripe_webhook(request: Request):
    if not settings.STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=503, detail="Stripe webhook is not configured")
    payload = await request.body()
    signature = request.headers.get("stripe-signature")
    try:
        event = stripe.Webhook.construct_event(payload, signature, settings.STRIPE_WEBHOOK_SECRET)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid payload") from exc
    except stripe.error.SignatureVerificationError as exc:
        raise HTTPException(status_code=400, detail="Invalid signature") from exc

    if not await _claim_stripe_event(event):
        return {"status": "already_processed"}

    try:
        obj = event["data"]["object"]
        if event["type"] == "customer.subscription.created":
            await handle_subscription_created(obj)
        elif event["type"] == "customer.subscription.updated":
            await handle_subscription_updated(obj)
        elif event["type"] == "customer.subscription.deleted":
            await handle_subscription_canceled(obj)
        elif event["type"] == "invoice.payment_succeeded":
            await handle_payment_succeeded(obj)

        await db.stripe_events.update_one(
            {"event_id": event["id"]},
            {"$set": {
                "status": "processed",
                "processed_at": datetime.now(timezone.utc),
                "lock_until": None,
                "error": None,
            }},
        )
        return {"status": "success"}
    except Exception as exc:
        await db.stripe_events.update_one(
            {"event_id": event["id"]},
            {"$set": {"status": "failed", "error": str(exc), "lock_until": None}},
        )
        logger.exception("Stripe webhook processing failed")
        raise HTTPException(status_code=500, detail="Webhook processing failed") from exc


def _period(subscription, key: str):
    return datetime.fromtimestamp(subscription[key], tz=timezone.utc)


async def handle_subscription_created(subscription):
    await db.users.update_one(
        {"stripe_customer_id": subscription["customer"]},
        {"$set": {
            "plan": UserPlan.pro,
            "subscription_status": SubscriptionStatus.active,
            "stripe_subscription_id": subscription["id"],
            "current_period_start": _period(subscription, "current_period_start"),
            "current_period_end": _period(subscription, "current_period_end"),
            "scans_used_this_month": 0,
        }},
    )


async def handle_subscription_updated(subscription):
    status = subscription["status"]
    sub_status = SubscriptionStatus.active
    plan = UserPlan.pro
    if status == "past_due":
        sub_status = SubscriptionStatus.past_due
    elif status in {"canceled", "unpaid", "incomplete_expired"}:
        sub_status = SubscriptionStatus.canceled
        plan = UserPlan.free

    await db.users.update_one(
        {"stripe_customer_id": subscription["customer"]},
        {"$set": {
            "plan": plan,
            "subscription_status": sub_status,
            "current_period_start": _period(subscription, "current_period_start"),
            "current_period_end": _period(subscription, "current_period_end"),
        }},
    )


async def handle_subscription_canceled(subscription):
    await db.users.update_one(
        {"stripe_customer_id": subscription["customer"]},
        {"$set": {
            "plan": UserPlan.free,
            "subscription_status": SubscriptionStatus.canceled,
            "stripe_subscription_id": None,
            "scans_used_this_month": 0,
        }},
    )


async def handle_payment_succeeded(invoice):
    await db.users.update_one(
        {"stripe_customer_id": invoice["customer"]},
        {"$set": {"subscription_status": SubscriptionStatus.active, "scans_used_this_month": 0}},
    )
