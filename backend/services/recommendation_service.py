"""
Recommendation Service — TF-IDF + Cosine Similarity
Matches user preferences (destination, budget, trip_type, interests)
against a dataset of 70 global tourist places and returns top-10 matches.
"""
from __future__ import annotations
import json
import os
import re
from typing import List, Optional

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# ─── Load Data ────────────────────────────────────────────────────────────────

_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "destinations.json")

def _load_destinations() -> list[dict]:
    with open(os.path.realpath(_DATA_PATH), encoding="utf-8") as f:
        return json.load(f)

DESTINATIONS = _load_destinations()


# ─── Build TF-IDF corpus ──────────────────────────────────────────────────────

def _build_document(dest: dict) -> str:
    """Combine all relevant fields into one searchable text document."""
    parts = [
        dest.get("name", ""),
        dest.get("country", ""),
        dest.get("city", ""),
        dest.get("category", ""),
        dest.get("description", ""),
        dest.get("budget", ""),
        " ".join(dest.get("trip_types", [])),
        " ".join(dest.get("interests", [])),
    ]
    return " ".join(p for p in parts if p).lower()


_DOCUMENTS = [_build_document(d) for d in DESTINATIONS]

_VECTORIZER = TfidfVectorizer(
    ngram_range=(1, 2),
    stop_words="english",
    max_features=5_000,
    sublinear_tf=True,
)
_TFIDF_MATRIX = _VECTORIZER.fit_transform(_DOCUMENTS)


# ─── Public API ───────────────────────────────────────────────────────────────

class RecommendationRequest:
    def __init__(
        self,
        country: Optional[str] = None,
        budget: str = "medium",           # low | medium | high
        trip_type: Optional[str] = None,  # adventure | cultural | beach | …
        interests: Optional[List[str]] = None,
        top_n: int = 10,
    ):
        self.country    = country
        self.budget     = budget
        self.trip_type  = trip_type
        self.interests  = interests or []
        self.top_n      = min(max(top_n, 1), 20)


def get_recommendations(req: RecommendationRequest) -> list[dict]:
    """Return top-N destination recommendations for the given request."""

    # 1. Build a query document from user inputs
    query_parts = [req.budget]
    if req.country:
        query_parts.append(req.country)
    if req.trip_type:
        query_parts.append(req.trip_type)
    query_parts.extend(req.interests)
    query_text = " ".join(query_parts).lower()

    # 2. Compute cosine similarity
    query_vec    = _VECTORIZER.transform([query_text])
    similarities = cosine_similarity(query_vec, _TFIDF_MATRIX).flatten()

    # 3. Country filter (hard filter when a destination country is provided)
    if req.country:
        country_lower = req.country.lower()
        for i, dest in enumerate(DESTINATIONS):
            if dest["country"].lower() != country_lower:
                similarities[i] *= 0.05   # heavily down-weight off-country

    # 4. Budget soft boost: exact match gets a boost
    for i, dest in enumerate(DESTINATIONS):
        if dest.get("budget", "").lower() == req.budget.lower():
            similarities[i] *= 1.3

    # 5. Sort and pick top-N
    ranked_indices = np.argsort(similarities)[::-1][: req.top_n * 2]  # extra buffer

    results = []
    seen_names = set()
    for idx in ranked_indices:
        dest = DESTINATIONS[idx]
        if dest["name"] in seen_names:
            continue
        seen_names.add(dest["name"])
        score = float(similarities[idx])
        results.append({
            **dest,
            "match_score":      round(score * 100, 1),
            "budget_match":     dest.get("budget", "") == req.budget,
            "trip_type_match":  req.trip_type in dest.get("trip_types", []) if req.trip_type else False,
        })
        if len(results) >= req.top_n:
            break

    return results


def get_all_countries() -> list[str]:
    """Distinct countries in the dataset."""
    return sorted({d["country"] for d in DESTINATIONS})


def get_all_categories() -> list[str]:
    return sorted({d["category"] for d in DESTINATIONS})


def get_all_trip_types() -> list[str]:
    seen, out = set(), []
    for d in DESTINATIONS:
        for t in d.get("trip_types", []):
            if t not in seen:
                seen.add(t)
                out.append(t)
    return sorted(out)


def get_all_interests() -> list[str]:
    seen, out = set(), []
    for d in DESTINATIONS:
        for i in d.get("interests", []):
            if i not in seen:
                seen.add(i)
                out.append(i)
    return sorted(out)
