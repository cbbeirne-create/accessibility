"""Stripe subscription routes with signed, idempotent webhook processing."""
import logging
from datetime import datetime, timezone

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from pymongo.errors import DuplicateKeyError

from ...core.config import settings
from ...core.database import db
from ...core.security import get_current_user
from ...models.user import SubscriptionStatus, User, UserPlan

router = APIRouter(prefix='/subscription')
logger = logging.getLogger(__name__)
stripe.api_key = settings.STRIPE_SECRET_KEY


def _from_ts(value):
    return datetime.fromtimestamp(value, tz=timezone.utc) if value else None


def create_stripe_checkout_session(customer_id: str, price_id: str, success_url: str, cancel_url: str):
    if not stripe.api_key:
        raise HTTPException(status_code=503, detail='Payment system not configured.')
    if not price_id:
        raise HTTPException(status_code=503, detail='Subscription price is not configured.')
    if not customer_id:
        raise HTTPException(status_code=400, detail='No payment profile found. Please contact support.')
    try:
        return stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=['card'],
            line_items=[{'price': price_id, 'quantity': 1}],
            mode='subscription',
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={'customer_id': customer_id},
            subscription_data={'metadata': {'customer_id': customer_id}},
        )
    except stripe.error.StripeError as exc:
        logger.exception('Stripe checkout session creation failed')
        raise HTTPException(status_code=502, detail='Payment provider could not create a checkout session.') from exc


@router.post('/create-checkout-session')
async def create_checkout_session(current_user: User = Depends(get_current_user)):
    if current_user.plan == UserPlan.pro and current_user.subscription_status == SubscriptionStatus.active:
        raise HTTPException(status_code=409, detail='You already have an active Pro subscription.')
    session = create_stripe_checkout_session(
        customer_id=current_user.stripe_customer_id,
        price_id=settings.STRIPE_PRO_PRICE_ID,
        success_url=f'{settings.FRONTEND_URL}/dashboard?success=true',
        cancel_url=f'{settings.FRONTEND_URL}/pricing?canceled=true',
    )
    return {'checkout_url': session.url}


@router.post('/webhook')
async def stripe_webhook(request: Request):
    if not settings.STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=503, detail='Stripe webhook is not configured.')
    payload = await request.body()
    signature = request.headers.get('stripe-signature')
    try:
        event = stripe.Webhook.construct_event(payload, signature, settings.STRIPE_WEBHOOK_SECRET)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail='Invalid payload') from exc
    except stripe.error.SignatureVerificationError as exc:
        raise HTTPException(status_code=400, detail='Invalid signature') from exc

    try:
        await db.stripe_events.insert_one({'event_id': event['id'], 'type': event['type'], 'received_at': datetime.now(timezone.utc)})
    except DuplicateKeyError:
        return {'status': 'already_processed'}

    try:
        obj = event['data']['object']
        if event['type'] == 'customer.subscription.created':
            await handle_subscription_created(obj)
        elif event['type'] == 'customer.subscription.updated':
            await handle_subscription_updated(obj)
        elif event['type'] == 'customer.subscription.deleted':
            await handle_subscription_canceled(obj)
        elif event['type'] == 'invoice.payment_succeeded':
            await handle_payment_succeeded(obj)
        await db.stripe_events.update_one({'event_id': event['id']}, {'$set': {'processed_at': datetime.now(timezone.utc)}})
        return {'status': 'success'}
    except Exception:
        await db.stripe_events.delete_one({'event_id': event['id']})
        logger.exception('Stripe webhook processing failed: %s', event.get('id'))
        raise HTTPException(status_code=500, detail='Webhook processing failed')


async def handle_subscription_created(subscription):
    await db.users.update_one({'stripe_customer_id': subscription['customer']}, {'$set': {
        'plan': UserPlan.pro.value,
        'subscription_status': SubscriptionStatus.active.value,
        'stripe_subscription_id': subscription['id'],
        'current_period_start': _from_ts(subscription.get('current_period_start')),
        'current_period_end': _from_ts(subscription.get('current_period_end')),
        'scans_used_this_month': 0,
    }})


async def handle_subscription_updated(subscription):
    status = subscription.get('status')
    mapped = SubscriptionStatus.active
    plan = UserPlan.pro
    if status == 'past_due':
        mapped = SubscriptionStatus.past_due
    elif status in {'canceled', 'unpaid', 'incomplete_expired'}:
        mapped = SubscriptionStatus.canceled
        plan = UserPlan.free
    await db.users.update_one({'stripe_customer_id': subscription['customer']}, {'$set': {
        'plan': plan.value,
        'subscription_status': mapped.value,
        'stripe_subscription_id': subscription.get('id') if plan == UserPlan.pro else None,
        'current_period_start': _from_ts(subscription.get('current_period_start')),
        'current_period_end': _from_ts(subscription.get('current_period_end')),
    }})


async def handle_subscription_canceled(subscription):
    await db.users.update_one({'stripe_customer_id': subscription['customer']}, {'$set': {
        'plan': UserPlan.free.value,
        'subscription_status': SubscriptionStatus.canceled.value,
        'stripe_subscription_id': None,
        'scans_used_this_month': 0,
    }})


async def handle_payment_succeeded(invoice):
    await db.users.update_one({'stripe_customer_id': invoice['customer']}, {'$set': {
        'subscription_status': SubscriptionStatus.active.value,
        'current_period_start': _from_ts(invoice.get('period_start')),
        'current_period_end': _from_ts(invoice.get('period_end')),
        'scans_used_this_month': 0,
    }})
