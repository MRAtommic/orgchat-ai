"""
OrgChat AI — Stripe Payment Integration
Handles subscription checkout, webhooks, and customer portal.
"""
import os
import stripe
from datetime import datetime, timedelta, timezone

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")
WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")

# Stripe Price IDs — set these in .env after creating products in Stripe Dashboard
PRICE_IDS = {
    "pro":      os.environ.get("STRIPE_PRICE_PRO", ""),
    "business": os.environ.get("STRIPE_PRICE_BUSINESS", ""),
}

# PromptPay uses one-time (mode=payment) prices — create separate prices in Stripe Dashboard
PROMPTPAY_PRICE_IDS = {
    "pro":      os.environ.get("STRIPE_PRICE_PRO_PROMPTPAY", ""),
    "business": os.environ.get("STRIPE_PRICE_BUSINESS_PROMPTPAY", ""),
    "test":     os.environ.get("STRIPE_PRICE_TEST_1THB", ""),  # 1 THB for testing
}


def is_configured() -> bool:
    """Returns True if Stripe API key is set and looks valid."""
    key = stripe.api_key or ""
    return key.startswith("sk_live_") or key.startswith("sk_test_")


def create_checkout_session(org_id: int, plan: str, customer_id: str | None,
                             success_url: str, cancel_url: str):
    price_id = PRICE_IDS.get(plan)
    if not price_id:
        raise ValueError(
            f"ยังไม่ได้ตั้งค่า STRIPE_PRICE_{plan.upper()} ใน .env — "
            f"สร้าง Product ใน Stripe Dashboard แล้วนำ Price ID มาใส่"
        )

    params = {
        "mode": "subscription",
        "line_items": [{"price": price_id, "quantity": 1}],
        "success_url": success_url,
        "cancel_url": cancel_url,
        "metadata": {"org_id": str(org_id), "plan": plan},
        "subscription_data": {
            "metadata": {"org_id": str(org_id), "plan": plan}
        },
        "allow_promotion_codes": True,
        "billing_address_collection": "auto",
        "locale": "th",
    }

    if customer_id:
        params["customer"] = customer_id

    return stripe.checkout.Session.create(**params)


def create_promptpay_checkout(org_id: int, plan: str, customer_id: str | None,
                              success_url: str, cancel_url: str):
    """Create Stripe Checkout Session for PromptPay (one-time, 30-day access)."""
    price_id = PROMPTPAY_PRICE_IDS.get(plan)
    if not price_id:
        env_key = "STRIPE_PRICE_TEST_1THB" if plan == "test" else f"STRIPE_PRICE_{plan.upper()}_PROMPTPAY"
        raise ValueError(
            f"ยังไม่ได้ตั้งค่า {env_key} ใน .env — "
            f"สร้าง Price แบบ one-time (THB) ใน Stripe Dashboard แล้วนำ ID มาใส่"
        )

    # test plan → ให้ Pro access 30 วัน
    actual_plan = "pro" if plan == "test" else plan

    params = {
        "mode": "payment",
        "payment_method_types": ["promptpay"],
        "line_items": [{"price": price_id, "quantity": 1}],
        "success_url": success_url,
        "cancel_url": cancel_url,
        "metadata": {
            "org_id": str(org_id),
            "plan": actual_plan,
            "payment_type": "promptpay",
            "days": "30",
        },
        "locale": "th",
        "expires_at": int((datetime.now(timezone.utc) + timedelta(hours=24)).timestamp()),
    }

    if customer_id:
        params["customer"] = customer_id

    return stripe.checkout.Session.create(**params)


def create_portal_session(customer_id: str, return_url: str):
    return stripe.billing_portal.Session.create(
        customer=customer_id,
        return_url=return_url,
    )


def construct_webhook_event(payload: bytes, sig_header: str):
    if not WEBHOOK_SECRET:
        raise ValueError("STRIPE_WEBHOOK_SECRET ยังไม่ได้ตั้งค่า")
    return stripe.Webhook.construct_event(payload, sig_header, WEBHOOK_SECRET)


def get_subscription_period_end(subscription_id: str) -> str | None:
    """Returns ISO 8601 datetime string of current_period_end."""
    try:
        sub = stripe.Subscription.retrieve(subscription_id)
        end_ts = sub.get("current_period_end")
        if end_ts:
            return datetime.fromtimestamp(end_ts, tz=timezone.utc).isoformat()
    except Exception:
        pass
    return None
