"""
Groq AI Service — powers both the Travel Chatbot and Travel Planner assistant.
Falls back to a mock response when GROQ_API_KEY is not set (development mode).
"""
from __future__ import annotations
import json
import os
from typing import List, Dict, Optional

try:
    from groq import Groq
    _GROQ_AVAILABLE = True
except ImportError:
    _GROQ_AVAILABLE = False

from config import settings


# ─── Prompts ──────────────────────────────────────────────────────────────────

CHATBOT_SYSTEM = """You are TravelAI, an expert travel assistant with deep knowledge of destinations 
worldwide. You help travelers plan trips, discover places, find budget tips, and navigate travel 
logistics. Be friendly, specific, and always suggest concrete actionable advice. 
Format responses clearly — use bullet points and short paragraphs. Never exceed 300 words."""

PLANNER_SYSTEM = """You are TravelAI Planner, an expert at creating detailed, day-by-day travel 
itineraries. When given a destination, number of days, budget level, and preferences, you generate 
a complete structured itinerary in valid JSON format only.

Output ONLY a JSON object with this exact structure:
{
  "title": "Trip title",
  "destination": "City, Country",
  "summary": "2-sentence trip overview",
  "days": [
    {
      "day": 1,
      "theme": "Arrival & City Center",
      "morning": { "activity": "...", "description": "...", "cost": "$" },
      "afternoon": { "activity": "...", "description": "...", "cost": "$$" },
      "evening": { "activity": "...", "description": "...", "cost": "$$$" },
      "tips": "One practical tip for this day"
    }
  ],
  "budget_breakdown": {
    "accommodation": "...",
    "food": "...",
    "activities": "...",
    "transport": "...",
    "total_estimate": "..."
  },
  "essential_tips": ["tip1", "tip2", "tip3"],
  "best_time_to_visit": "...",
  "currency": "..."
}
Output ONLY the JSON. No preamble, no explanation."""


# ─── Client ───────────────────────────────────────────────────────────────────

def _get_client() -> Optional["Groq"]:
    if not _GROQ_AVAILABLE:
        return None
    api_key = settings.GROQ_API_KEY or os.getenv("GROQ_API_KEY", "")
    if not api_key:
        return None
    return Groq(api_key=api_key)


# ─── Chatbot ──────────────────────────────────────────────────────────────────

def chat(history: List[Dict[str, str]], user_message: str) -> str:
    """Send a message with conversation history and return assistant reply."""
    client = _get_client()
    if client is None:
        return _mock_chat(user_message)

    messages = [{"role": "system", "content": CHATBOT_SYSTEM}]
    # Only keep last 10 messages to avoid token limit
    for msg in history[-10:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_message})

    response = client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=messages,
        max_tokens=600,
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()


def generate_itinerary(
    destination: str,
    days: int,
    budget: str,
    trip_type: str,
    preferences: List[str],
) -> dict:
    """Generate a structured travel itinerary as a Python dict."""
    client = _get_client()
    pref_str = ", ".join(preferences) if preferences else "general sightseeing"
    prompt = (
        f"Create a {days}-day {budget}-budget {trip_type} travel itinerary for {destination}. "
        f"Traveler interests: {pref_str}. "
        f"Generate exactly {days} days in the schedule."
    )

    if client is None:
        return _mock_itinerary(destination, days, budget)

    response = client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[
            {"role": "system", "content": PLANNER_SYSTEM},
            {"role": "user",   "content": prompt},
        ],
        max_tokens=2000,
        temperature=0.6,
    )
    raw = response.choices[0].message.content.strip()
    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("```", 2)[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.rsplit("```", 1)[0]
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return _mock_itinerary(destination, days, budget)


# ─── Mock Fallbacks (no API key) ──────────────────────────────────────────────

def _mock_chat(message: str) -> str:
    msg_l = message.lower()
    if any(w in msg_l for w in ["paris", "france"]):
        return ("🗼 **Paris** is a wonderful choice! Here are some must-sees:\n\n"
                "- **Eiffel Tower** — Book timed entry in advance to skip queues\n"
                "- **Louvre Museum** — Arrive early; the Mona Lisa gets very crowded by 11am\n"
                "- **Montmartre** — Great for street art and panoramic city views\n\n"
                "💡 The Paris Museum Pass saves money if you plan 3+ museums. "
                "Metro day-passes are the best way to get around. Would you like a full itinerary?")
    if any(w in msg_l for w in ["budget", "cheap", "affordable"]):
        return ("Here are my top tips for budget travel:\n\n"
                "- Book flights **6–8 weeks** in advance for best prices\n"
                "- Use **hostels or guesthouses** instead of hotels\n"
                "- Eat where locals eat — avoid tourist-area restaurants\n"
                "- Use **public transport** over taxis\n"
                "- Visit **free attractions**: parks, markets, churches\n\n"
                "Which destination are you considering? I can give more specific advice!")
    if any(w in msg_l for w in ["visa", "passport"]):
        return ("Visa requirements vary by nationality and destination. "
                "My best advice:\n\n"
                "1. Check the official embassy website of your destination\n"
                "2. Use **IATA Travel Centre** for up-to-date requirements\n"
                "3. Apply **at least 6 weeks** before travel\n\n"
                "Which country are you travelling to and from?")
    return (f"Great question about travel! I'm TravelAI, your personal travel assistant. "
            f"I can help you with destination recommendations, itinerary planning, budget tips, "
            f"visa requirements, packing lists, and much more.\n\n"
            f"Could you tell me more about your trip? For example:\n"
            f"- Where are you thinking of going?\n"
            f"- How many days do you have?\n"
            f"- What's your budget range?")


def _mock_itinerary(destination: str, days: int, budget: str) -> dict:
    day_list = []
    themes = ["Arrival & Orientation", "Culture & History", "Nature & Outdoors",
              "Local Experiences", "Day Trip", "Relaxation", "Shopping & Departure"]
    for i in range(1, days + 1):
        theme = themes[(i - 1) % len(themes)]
        day_list.append({
            "day": i,
            "theme": theme,
            "morning":   {"activity": f"Morning exploration — Day {i}", "description": f"Start your {i}{'st' if i==1 else 'nd' if i==2 else 'rd' if i==3 else 'th'} day exploring {destination}'s highlights.", "cost": "$"},
            "afternoon": {"activity": f"Afternoon activity — {theme}", "description": f"Immerse yourself in the local culture and scenery.", "cost": "$$"},
            "evening":   {"activity": "Local dining experience", "description": "Enjoy authentic local cuisine at a recommended restaurant.", "cost": "$$"},
            "tips":       f"Day {i} tip: Ask locals for their favorite hidden gem.",
        })
    budget_map = {"low": "$30–60/day", "medium": "$60–150/day", "high": "$150–400/day"}
    return {
        "title": f"{days} Days in {destination}",
        "destination": destination,
        "summary": f"A carefully crafted {days}-day {budget}-budget journey through {destination}. This itinerary balances iconic highlights with authentic local experiences.",
        "days": day_list,
        "budget_breakdown": {
            "accommodation": budget_map.get(budget, "$60–100/night"),
            "food":          "$20–50/day",
            "activities":    "$10–40/day",
            "transport":     "$5–20/day",
            "total_estimate": budget_map.get(budget, "$100–200/day"),
        },
        "essential_tips": [
            "Book popular attractions in advance to avoid queues.",
            "Download offline maps before your trip.",
            "Always carry local currency for small vendors.",
        ],
        "best_time_to_visit": "Spring or autumn for mild weather and fewer crowds.",
        "currency": "Local currency — check current exchange rates.",
    }
