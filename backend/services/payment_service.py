"""
Payment Service — mock implementation.
Replace the mock logic with real Stripe calls in production.
"""
from __future__ import annotations
import uuid
import random
from datetime import datetime, timedelta
from config import settings


PLANS = {
    "free": {
        "id":          "free",
        "name":        "Explorer",
        "price":       0.0,
        "price_label": "Free forever",
        "billing":     "monthly",
        "features": [
            "10 AI chat messages / day",
            "3 trip plans / month",
            "5 destination recommendations",
            "Basic itinerary generator",
            "Community support",
        ],
        "limits": {
            "chat_per_day":      10,
            "plans_per_month":   3,
            "recommendations":   5,
        },
    },
    "pro": {
        "id":          "pro",
        "name":        "Pro",
        "price":       9.99,
        "price_label": "$9.99 / month",
        "billing":     "monthly",
        "features": [
            "Unlimited AI chat messages",
            "Unlimited trip plans",
            "Unlimited recommendations",
            "Advanced itinerary with day-by-day breakdown",
            "Priority AI responses",
            "PDF export of itineraries",
            "Offline access",
            "Priority support",
        ],
        "limits": {
            "chat_per_day":      -1,
            "plans_per_month":   -1,
            "recommendations":   -1,
        },
        "badge": "Most Popular",
    },
    "pro_annual": {
        "id":           "pro_annual",
        "name":         "Pro Annual",
        "price":        89.99,
        "price_label":  "$89.99 / year",
        "monthly_equiv": "$7.50 / month",
        "billing":      "annual",
        "features": [
            "Everything in Pro",
            "Save 25% vs monthly",
            "Dedicated travel concierge (email)",
            "Early access to new features",
        ],
        "limits": {
            "chat_per_day":      -1,
            "plans_per_month":   -1,
            "recommendations":   -1,
        },
        "badge": "Best Value",
    },
}


class PaymentError(Exception):
    pass


def get_plans() -> list[dict]:
    return list(PLANS.values())


def get_plan(plan_id: str) -> dict | None:
    return PLANS.get(plan_id)


def process_payment(
    user_id: int,
    plan_id: str,
    card_number: str,
    card_holder: str,
    expiry: str,
    cvv: str,
) -> dict:
    """
    Mock payment processor.
    In production, replace this with Stripe PaymentIntent creation.
    """
    plan = get_plan(plan_id)
    if not plan:
        raise PaymentError(f"Unknown plan: {plan_id}")
    if plan["price"] == 0:
        raise PaymentError("Cannot process payment for free plan.")

    # Mock validation
    digits = card_number.replace(" ", "").replace("-", "")
    if len(digits) < 16:
        raise PaymentError("Invalid card number.")
    if len(cvv) < 3:
        raise PaymentError("Invalid CVV.")

    # Simulate 95% success rate
    if random.random() < 0.05:
        raise PaymentError("Payment declined by issuer. Please try a different card.")

    transaction_id = f"txn_{uuid.uuid4().hex[:16].upper()}"
    now = datetime.utcnow()
    expires_at = now + timedelta(days=365 if "annual" in plan_id else 30)

    return {
        "success":        True,
        "transaction_id": transaction_id,
        "plan_id":        plan_id,
        "plan_name":      plan["name"],
        "amount":         plan["price"],
        "currency":       "USD",
        "starts_at":      now.isoformat(),
        "expires_at":     expires_at.isoformat(),
        "card_last4":     digits[-4:],
        "card_holder":    card_holder,
    }
