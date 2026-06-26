from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from config import settings
from database import User, get_db
from routes.auth import get_current_user
from services.recommendation_service import (
    RecommendationRequest,
    get_recommendations,
    get_all_countries,
    get_all_categories,
    get_all_trip_types,
    get_all_interests,
)

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


# ─── Schemas ──────────────────────────────────────────────────────────────────

class RecommendRequest(BaseModel):
    country:    Optional[str]       = None
    budget:     str                  = "medium"   # low | medium | high
    trip_type:  Optional[str]        = None
    interests:  Optional[List[str]]  = []
    top_n:      int                  = 10


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _check_limit(user: User):
    if not user.is_pro and user.recommend_count >= settings.FREE_RECOMMEND_LIMIT:
        raise HTTPException(
            status_code=402,
            detail={
                "message": f"Free recommendation limit ({settings.FREE_RECOMMEND_LIMIT}) reached. Upgrade to Pro for unlimited recommendations.",
                "upgrade_required": True,
            },
        )


# ─── Routes ───────────────────────────────────────────────────────────────────

@router.post("/suggest")
def suggest(
    body: RecommendRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _check_limit(current_user)

    req = RecommendationRequest(
        country   = body.country,
        budget    = body.budget,
        trip_type = body.trip_type,
        interests = body.interests or [],
        top_n     = min(body.top_n, 10),
    )
    results = get_recommendations(req)

    current_user.recommend_count += 1
    db.commit()

    return {
        "query": {
            "country":   body.country,
            "budget":    body.budget,
            "trip_type": body.trip_type,
            "interests": body.interests,
        },
        "count":   len(results),
        "results": results,
    }


@router.get("/meta")
def get_meta():
    """Return available filter values for frontend dropdowns."""
    return {
        "countries":  get_all_countries(),
        "categories": get_all_categories(),
        "trip_types": get_all_trip_types(),
        "interests":  get_all_interests(),
    }


@router.get("/destinations")
def list_destinations(
    country:    Optional[str] = None,
    category:   Optional[str] = None,
    budget:     Optional[str] = None,
    limit:      int = 20,
    offset:     int = 0,
):
    """Browse the full destinations catalogue with optional filtering."""
    from services.recommendation_service import DESTINATIONS
    filtered = DESTINATIONS
    if country:
        filtered = [d for d in filtered if d["country"].lower() == country.lower()]
    if category:
        filtered = [d for d in filtered if d["category"].lower() == category.lower()]
    if budget:
        filtered = [d for d in filtered if d.get("budget", "").lower() == budget.lower()]
    total = len(filtered)
    page  = filtered[offset: offset + limit]
    return {"total": total, "limit": limit, "offset": offset, "results": page}


@router.get("/countries")
def list_countries():
    return get_all_countries()
