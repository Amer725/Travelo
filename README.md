# TravelAI 🌍 — AI-Powered Travel Planning Platform

A full-stack travel platform with three AI modules:
- 💬 **Chatbot** — Groq-powered travel assistant
- 🗓️ **Trip Planner** — AI day-by-day itinerary generator
- 🧭 **Discover** — TF-IDF + Cosine Similarity recommendation engine

## Quick Start

### Backend (Python 3.10+)
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Set your Groq API key (optional — mock mode works without it)
echo "GROQ_API_KEY=gsk_your_key" > .env

uvicorn main:app --reload --port 8000
# → http://localhost:8000/docs (interactive API docs)
```

### Frontend
```bash
cd frontend
python -m http.server 5500
# → http://localhost:5500
```

## Pages
| Page | URL | Description |
|------|-----|-------------|
| Landing | `/` | Marketing homepage |
| Login | `/pages/login.html` | Sign in / Register |
| Chatbot | `/pages/chat.html` | AI travel assistant |
| Planner | `/pages/planner.html` | Trip itinerary generator |
| Discover | `/pages/discover.html` | Destination recommendations |
| Dashboard | `/pages/dashboard.html` | User account + trips |
| Pro Plans | `/pages/subscription.html` | Pricing page |
| Checkout | `/pages/payment.html` | Payment form |
| Confirmation | `/pages/payment-success.html` | Order confirmed |

## Environment Variables
```
SECRET_KEY=change-this-in-production
GROQ_API_KEY=gsk_your_groq_api_key
DEBUG=False
DATABASE_URL=sqlite:///./travelai.db
```

## Test Payment
Use card `4242 4242 4242 4242` with any future expiry and any 3-digit CVV.

## See Full Architecture
See [ARCHITECTURE.md](./ARCHITECTURE.md) for complete system docs, API mapping, and deployment guide.
