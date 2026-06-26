from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import Subscription, User, get_db
from routes.auth import get_current_user
from services.payment_service import get_plans, get_plan, process_payment, PaymentError

router = APIRouter(prefix="/subscription", tags=["subscription"])


# ─── Schemas ──────────────────────────────────────────────────────────────────

class PaymentRequest(BaseModel):
    plan_id:     str
    card_number: str
    card_holder: str
    expiry:      str
    cvv:         str

class CancelRequest(BaseModel):
    reason: Optional[str] = None


# ─── Routes ───────────────────────────────────────────────────────────────────

@router.get("/plans")
def list_plans():
    return get_plans()


@router.get("/status")
def get_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sub = (
        db.query(Subscription)
        .filter(
            Subscription.user_id == current_user.id,
            Subscription.status  == "active",
        )
        .order_by(Subscription.created_at.desc())
        .first()
    )
    plan = get_plan("pro" if current_user.is_pro else "free")
    return {
        "is_pro":       current_user.is_pro,
        "plan":         plan,
        "subscription": {
            "id":             sub.id,
            "plan":           sub.plan,
            "status":         sub.status,
            "amount_paid":    sub.amount_paid,
            "transaction_id": sub.transaction_id,
            "starts_at":      sub.starts_at.isoformat()  if sub.starts_at  else None,
            "expires_at":     sub.expires_at.isoformat() if sub.expires_at else None,
        } if sub else None,
    }


@router.post("/checkout")
def checkout(
    body: PaymentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Process payment and upgrade user to PRO."""
    if current_user.is_pro:
        raise HTTPException(status_code=409, detail="You are already on a Pro plan.")

    try:
        result = process_payment(
            user_id     = current_user.id,
            plan_id     = body.plan_id,
            card_number = body.card_number,
            card_holder = body.card_holder,
            expiry      = body.expiry,
            cvv         = body.cvv,
        )
    except PaymentError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Update user
    current_user.is_pro = True

    # Create subscription record
    sub = Subscription(
        user_id        = current_user.id,
        plan           = result["plan_id"],
        status         = "active",
        amount_paid    = result["amount"],
        currency       = result["currency"],
        payment_method = f"**** **** **** {result['card_last4']}",
        transaction_id = result["transaction_id"],
        expires_at     = datetime.fromisoformat(result["expires_at"]),
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)

    return {
        "success":        True,
        "transaction_id": result["transaction_id"],
        "plan_name":      result["plan_name"],
        "amount":         result["amount"],
        "currency":       result["currency"],
        "card_last4":     result["card_last4"],
        "expires_at":     result["expires_at"],
        "message":        f"🎉 Welcome to TravelAI {result['plan_name']}! Your account has been upgraded.",
    }


@router.post("/cancel")
def cancel_subscription(
    body: CancelRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sub = (
        db.query(Subscription)
        .filter(
            Subscription.user_id == current_user.id,
            Subscription.status  == "active",
        )
        .order_by(Subscription.created_at.desc())
        .first()
    )
    if not sub:
        raise HTTPException(status_code=404, detail="No active subscription found.")

    sub.status = "cancelled"
    current_user.is_pro = False
    db.commit()

    return {"message": "Subscription cancelled. Your Pro access will remain until the end of the billing period."}
