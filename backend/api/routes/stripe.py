"""
Stripe subscription API routes: checkout, webhooks.
"""
import logging
from datetime import datetime
import os

import stripe
from fastapi import APIRouter, HTTPException, Depends, Request

from ...core.config import settings
from ...core.database import db
from ...core.security import get_current_user
from ...models.user import User, UserPlan, SubscriptionStatus

router = APIRouter(prefix="/subscription")

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


def create_stripe_checkout_session(customer_id: str, price_id: str, success_url: str, cancel_url: str):
    """Create Stripe checkout session."""
    if not stripe.api_key or stripe.api_key.startswith('sk_test_your'):
        raise HTTPException(status_code=503, detail="Payment system not configured. Please contact support.")
    
    if not customer_id:
        raise HTTPException(status_code=400, detail="No payment profile found. Please contact support.")
    
    try:
        session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={'customer_id': customer_id}
        )
        return session
    except Exception as e:
        logging.error(f"Failed to create checkout session: {e}")
        raise HTTPException(status_code=500, detail="Failed to create checkout session")


@router.post("/create-checkout-session")
async def create_checkout_session(current_user: User = Depends(get_current_user)):
    """Create Stripe checkout session for Pro subscription."""
    try:
        success_url = f"{settings.FRONTEND_URL}/dashboard?success=true"
        cancel_url = f"{settings.FRONTEND_URL}/pricing?canceled=true"
        
        session = create_stripe_checkout_session(
            customer_id=current_user.stripe_customer_id,
            price_id=settings.STRIPE_PRO_PRICE_ID,
            success_url=success_url,
            cancel_url=cancel_url
        )
        
        return {"checkout_url": session.url}
        
    except Exception as e:
        logging.error(f"Checkout session creation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to create checkout session")


@router.post("/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events."""
    try:
        payload = await request.body()
        sig_header = request.headers.get('stripe-signature')
        
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
        
        if event['type'] == 'customer.subscription.created':
            subscription = event['data']['object']
            await handle_subscription_created(subscription)
        elif event['type'] == 'customer.subscription.updated':
            subscription = event['data']['object']
            await handle_subscription_updated(subscription)
        elif event['type'] == 'customer.subscription.deleted':
            subscription = event['data']['object']
            await handle_subscription_canceled(subscription)
        elif event['type'] == 'invoice.payment_succeeded':
            invoice = event['data']['object']
            await handle_payment_succeeded(invoice)
        
        return {"status": "success"}
        
    except ValueError as e:
        logging.error(f"Invalid payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        logging.error(f"Invalid signature: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception as e:
        logging.error(f"Webhook error: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")


async def handle_subscription_created(subscription):
    """Handle subscription creation."""
    customer_id = subscription['customer']
    subscription_id = subscription['id']
    current_period_start = datetime.fromtimestamp(subscription['current_period_start'])
    current_period_end = datetime.fromtimestamp(subscription['current_period_end'])
    
    await db.users.update_one(
        {"stripe_customer_id": customer_id},
        {"$set": {
            "plan": UserPlan.pro,
            "subscription_status": SubscriptionStatus.active,
            "stripe_subscription_id": subscription_id,
            "current_period_start": current_period_start,
            "current_period_end": current_period_end,
            "scans_used_this_month": 0
        }}
    )


async def handle_subscription_updated(subscription):
    """Handle subscription updates."""
    customer_id = subscription['customer']
    status = subscription['status']
    current_period_start = datetime.fromtimestamp(subscription['current_period_start'])
    current_period_end = datetime.fromtimestamp(subscription['current_period_end'])
    
    sub_status = SubscriptionStatus.active
    if status == 'past_due':
        sub_status = SubscriptionStatus.past_due
    elif status in ['canceled', 'unpaid']:
        sub_status = SubscriptionStatus.canceled
    
    await db.users.update_one(
        {"stripe_customer_id": customer_id},
        {"$set": {
            "subscription_status": sub_status,
            "current_period_start": current_period_start,
            "current_period_end": current_period_end
        }}
    )


async def handle_subscription_canceled(subscription):
    """Handle subscription cancellation."""
    customer_id = subscription['customer']
    
    await db.users.update_one(
        {"stripe_customer_id": customer_id},
        {"$set": {
            "plan": UserPlan.free,
            "subscription_status": SubscriptionStatus.canceled,
            "stripe_subscription_id": None,
            "scans_used_this_month": 0
        }}
    )


async def handle_payment_succeeded(invoice):
    """Handle successful payment."""
    customer_id = invoice['customer']
    current_period_start = datetime.fromtimestamp(invoice['period_start'])
    current_period_end = datetime.fromtimestamp(invoice['period_end'])
    
    await db.users.update_one(
        {"stripe_customer_id": customer_id},
        {"$set": {
            "subscription_status": SubscriptionStatus.active,
            "current_period_start": current_period_start,
            "current_period_end": current_period_end,
            "scans_used_this_month": 0
        }}
    )
