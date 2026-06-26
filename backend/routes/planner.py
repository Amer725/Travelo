from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from config import settings
from database import TripPlan, User, get_db
from routes.auth import get_current_user
from services.groq_service import generate_itinerary

router = APIRouter(prefix="/planner", tags=["planner"])


# ─── Schemas ──────────────────────────────────────────────────────────────────

class PlanRequest(BaseModel):
    destination:  str
    days:         int                  # 1–30
    budget:       str = "medium"       # low | medium | high
    trip_type:    str = "cultural"
    preferences:  List[str] = []
    title:        Optional[str] = None


class PlanStatus(BaseModel):
    status: str   # draft | confirmed | archived


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _check_limit(user: User):
    if not user.is_pro and user.plan_count >= settings.FREE_PLAN_LIMIT:
        raise HTTPException(
            status_code=402,
            detail={
                "message": f"Free plan limit ({settings.FREE_PLAN_LIMIT} trips) reached. Upgrade to Pro.",
                "upgrade_required": True,
            },
        )


def _plan_to_dict(plan: TripPlan) -> dict:
    return {
        "id":          plan.id,
        "title":       plan.title,
        "destination": plan.destination,
        "days":        plan.days,
        "budget":      plan.budget,
        "trip_type":   plan.trip_type,
        "preferences": plan.preferences,
        "itinerary":   plan.itinerary,
        "status":      plan.status,
        "created_at":  plan.created_at.isoformat() if plan.created_at else None,
    }


# ─── Routes ───────────────────────────────────────────────────────────────────

@router.post("/generate")
def generate_plan(
    body: PlanRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _check_limit(current_user)
    if not (1 <= body.days <= 30):
        raise HTTPException(status_code=422, detail="Days must be between 1 and 30.")

    itinerary = generate_itinerary(
        destination  = body.destination,
        days         = body.days,
        budget       = body.budget,
        trip_type    = body.trip_type,
        preferences  = body.preferences,
    )

    plan = TripPlan(
        user_id     = current_user.id,
        title       = body.title or itinerary.get("title", f"{body.days} Days in {body.destination}"),
        destination = body.destination,
        days        = body.days,
        budget      = body.budget,
        trip_type   = body.trip_type,
        preferences = body.preferences,
        itinerary   = itinerary,
    )
    db.add(plan)
    current_user.plan_count += 1
    db.commit()
    db.refresh(plan)

    return _plan_to_dict(plan)


@router.get("/trips")
def list_trips(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    plans = (
        db.query(TripPlan)
        .filter(TripPlan.user_id == current_user.id)
        .order_by(TripPlan.created_at.desc())
        .all()
    )
    return [_plan_to_dict(p) for p in plans]


@router.get("/trips/{plan_id}")
def get_trip(
    plan_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    plan = db.query(TripPlan).filter(TripPlan.id == plan_id, TripPlan.user_id == current_user.id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Trip not found.")
    return _plan_to_dict(plan)


@router.put("/trips/{plan_id}/status")
def update_status(
    plan_id: int,
    body: PlanStatus,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    plan = db.query(TripPlan).filter(TripPlan.id == plan_id, TripPlan.user_id == current_user.id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Trip not found.")
    plan.status = body.status
    db.commit()
    return _plan_to_dict(plan)


@router.delete("/trips/{plan_id}", status_code=204)
def delete_trip(
    plan_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    plan = db.query(TripPlan).filter(TripPlan.id == plan_id, TripPlan.user_id == current_user.id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Trip not found.")
    db.delete(plan)
    db.commit()
