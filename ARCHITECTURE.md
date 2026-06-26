# TravelAI — Full System Architecture
## Version 2.0 · Production-Ready Integration

---

## 📐 System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        TravelAI Platform                        │
│                                                                 │
│  ┌──────────────────────┐    ┌──────────────────────────────┐  │
│  │      FRONTEND        │    │          BACKEND             │  │
│  │   (HTML/CSS/JS)      │◄──►│       (FastAPI Python)       │  │
│  │                      │    │                              │  │
│  │  ┌────────────────┐  │    │  ┌──────────────────────┐   │  │
│  │  │ index.html     │  │    │  │ auth routes          │   │  │
│  │  │ chat.html      │  │    │  │ chatbot routes       │   │  │
│  │  │ planner.html   │  │    │  │ planner routes       │   │  │
│  │  │ discover.html  │  │    │  │ recommendations      │   │  │
│  │  │ dashboard.html │  │    │  │ subscription routes  │   │  │
│  │  │ subscription   │  │    │  └──────────────────────┘   │  │
│  │  │ payment.html   │  │    │                              │  │
│  │  │ login.html     │  │    │  ┌──────────────────────┐   │  │
│  │  └────────────────┘  │    │  │    AI SERVICES        │   │  │
│  │                      │    │  │                      │   │  │
│  │  js/api.js ◄─────────┼────┼─►│  Groq API (Chatbot)  │   │  │
│  │  css/style.css       │    │  │  TF-IDF (Recommend)  │   │  │
│  └──────────────────────┘    │  │  Groq API (Planner)  │   │  │
│                               │  └──────────────────────┘   │  │
│                               │                              │  │
│                               │  ┌──────────────────────┐   │  │
│                               │  │    DATABASE           │   │  │
│                               │  │  (SQLite / Postgres)  │   │  │
│                               │  └──────────────────────┘   │  │
│                               └──────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🗂️ Project Structure

```
travelai/
├── backend/
│   ├── main.py                     # FastAPI app entry point
│   ├── config.py                   # App settings (Pydantic)
│   ├── database.py                 # SQLAlchemy models + DB init
│   ├── requirements.txt            # Python dependencies
│   ├── .env.example                # Environment variable template
│   ├── routes/
│   │   ├── auth.py                 # Register, Login, Me, Profile
│   │   ├── chatbot.py              # Chat messages, history, sessions
│   │   ├── planner.py              # Trip plan CRUD + AI generation
│   │   ├── recommendations.py      # TF-IDF suggest, meta, destinations
│   │   └── subscription.py         # Plans, checkout, status, cancel
│   ├── services/
│   │   ├── groq_service.py         # Groq AI chatbot + itinerary generator
│   │   ├── recommendation_service.py  # TF-IDF + Cosine Similarity engine
│   │   └── payment_service.py      # Mock payment processor (Stripe-ready)
│   └── data/
│       └── destinations.json       # 70 global tourist destinations dataset
│
├── frontend/
│   ├── index.html                  # Landing page
│   ├── css/
│   │   └── style.css               # Global design system
│   ├── js/
│   │   └── api.js                  # Unified API client (all endpoints)
│   └── pages/
│       ├── login.html              # Sign in / Register
│       ├── dashboard.html          # User dashboard + stats
│       ├── chat.html               # AI Travel Chatbot
│       ├── planner.html            # AI Trip Planner
│       ├── discover.html           # Recommendation System UI
│       ├── subscription.html       # PRO plans pricing page
│       ├── payment.html            # Secure checkout form
│       └── payment-success.html    # Order confirmation
│
├── ARCHITECTURE.md                 # This file
└── README.md                       # Setup instructions
```

---

## 🔌 Complete API Mapping

### Base URL: `http://localhost:8000/api/v1`

---

### 🔐 Authentication  `POST /auth/...`

| Method | Endpoint | Description | Auth Required | Frontend Consumer |
|--------|----------|-------------|---------------|-------------------|
| POST | `/auth/register` | Create new account | No | `login.html` → `AuthAPI.register()` |
| POST | `/auth/login` | Login with email/password | No | `login.html` → `AuthAPI.login()` |
| POST | `/auth/token` | OAuth2 form login (Swagger) | No | Swagger UI |
| GET | `/auth/me` | Get current user profile | ✅ | `dashboard.html`, `api.js initNav()` |
| PUT | `/auth/profile` | Update username / full_name | ✅ | `dashboard.html` → `AuthAPI.updateProfile()` |

**Request/Response contracts:**
```json
// POST /auth/register
Request:  { "email": "...", "username": "...", "password": "...", "full_name": "..." }
Response: { "access_token": "...", "token_type": "bearer", "user": { id, email, username, is_pro, usage } }

// POST /auth/login
Request:  { "email": "...", "password": "..." }
Response: { "access_token": "...", "token_type": "bearer", "user": { ... } }
```

---

### 💬 Chatbot  `GET/POST /chat/...`

| Method | Endpoint | Description | Auth | Frontend |
|--------|----------|-------------|------|----------|
| POST | `/chat/message` | Send message, get AI reply | ✅ | `chat.html` → `ChatAPI.send()` |
| GET | `/chat/history` | Fetch message history | ✅ | `chat.html` → `ChatAPI.history()` |
| GET | `/chat/sessions` | List all chat sessions | ✅ | `chat.html` → `ChatAPI.sessions()` |
| DELETE | `/chat/history` | Clear conversation | ✅ | `chat.html` → `ChatAPI.clearHistory()` |

**Request/Response:**
```json
// POST /chat/message
Request:  { "message": "Best places in Japan?", "session_id": "uuid-or-null" }
Response: { "role": "assistant", "content": "...", "session_id": "uuid" }
```

**Free plan limit:** 10 messages/day → HTTP 402 with `upgrade_required: true`

---

### 🗓️ Trip Planner  `GET/POST /planner/...`

| Method | Endpoint | Description | Auth | Frontend |
|--------|----------|-------------|------|----------|
| POST | `/planner/generate` | Generate AI itinerary | ✅ | `planner.html` → `PlannerAPI.generate()` |
| GET | `/planner/trips` | List user's saved trips | ✅ | `planner.html`, `dashboard.html` |
| GET | `/planner/trips/{id}` | Get specific trip | ✅ | `planner.html` → `PlannerAPI.getTrip()` |
| PUT | `/planner/trips/{id}/status` | Update status (draft/confirmed) | ✅ | `dashboard.html` |
| DELETE | `/planner/trips/{id}` | Delete trip | ✅ | `dashboard.html`, `planner.html` |

**Request/Response:**
```json
// POST /planner/generate
Request: {
  "destination": "Tokyo, Japan",
  "days": 7,
  "budget": "medium",          // low | medium | high
  "trip_type": "cultural",
  "preferences": ["museums", "food", "photography"]
}
Response: {
  "id": 1,
  "title": "7 Days in Tokyo",
  "destination": "Tokyo, Japan",
  "itinerary": {
    "title": "...",
    "summary": "...",
    "days": [ { "day": 1, "theme": "...", "morning": {...}, "afternoon": {...}, "evening": {...}, "tips": "..." } ],
    "budget_breakdown": { ... },
    "essential_tips": [ ... ],
    "best_time_to_visit": "...",
    "currency": "..."
  }
}
```

**Free plan limit:** 3 plans → HTTP 402

---

### 🧭 Recommendations  `GET/POST /recommendations/...`

| Method | Endpoint | Description | Auth | Frontend |
|--------|----------|-------------|------|----------|
| POST | `/recommendations/suggest` | Get top-10 AI-matched destinations | ✅ | `discover.html` → `RecommendAPI.suggest()` |
| GET | `/recommendations/meta` | Filter options (countries, trip_types, interests) | No | `discover.html` → `RecommendAPI.getMeta()` |
| GET | `/recommendations/destinations` | Browse all destinations | No | `discover.html` → `RecommendAPI.listDestinations()` |
| GET | `/recommendations/countries` | List available countries | No | `discover.html` dropdown |

**Request/Response:**
```json
// POST /recommendations/suggest
Request: {
  "country": "Japan",           // optional — null = all countries
  "budget": "medium",           // low | medium | high
  "trip_type": "cultural",      // optional
  "interests": ["museums", "history", "food"],
  "top_n": 10
}
Response: {
  "query": { "country": "Japan", "budget": "medium", ... },
  "count": 10,
  "results": [
    {
      "id": 23,
      "name": "Tokyo Shibuya Crossing",
      "country": "Japan",
      "category": "city",
      "description": "...",
      "budget": "medium",
      "trip_types": ["city", "cultural", "adventure"],
      "interests": ["photography", "culture", "sightseeing"],
      "rating": 4.8,
      "match_score": 87.3,      // TF-IDF cosine similarity score (0–100)
      "budget_match": true,
      "trip_type_match": true
    }
  ]
}
```

**AI Engine:** TF-IDF vectorizer (n-gram 1–2) + Cosine Similarity  
**Dataset:** 70 destinations across 25+ countries  
**Free plan limit:** 5 recommendations → HTTP 402

---

### 💳 Subscription  `GET/POST /subscription/...`

| Method | Endpoint | Description | Auth | Frontend |
|--------|----------|-------------|------|----------|
| GET | `/subscription/plans` | List all plans (Free, Pro, Pro Annual) | No | `subscription.html` |
| GET | `/subscription/status` | Current user's subscription info | ✅ | `dashboard.html` |
| POST | `/subscription/checkout` | Process payment, upgrade to Pro | ✅ | `payment.html` → `SubAPI.checkout()` |
| POST | `/subscription/cancel` | Cancel subscription | ✅ | `dashboard.html` |

**Payment flow:**
```
payment.html
  ↓ POST /subscription/checkout { plan_id, card_number, card_holder, expiry, cvv }
  ↓ Payment processed (mock / Stripe)
  ↓ User.is_pro = True (DB update)
  ↓ Subscription record created
  ↓ Redirect → payment-success.html?tx=...&plan=...&amount=...
```

---

## 🤖 AI Models Integration

### 1. Chatbot (Groq API)
- **Model:** `llama3-8b-8192` via Groq
- **Location:** `services/groq_service.py` → `chat()`
- **Frontend:** `chat.html` ↔ `POST /chat/message`
- **Context window:** Last 10 messages preserved per session
- **Fallback:** Mock responses when `GROQ_API_KEY` is not set
- **System prompt:** Travel-specialized assistant identity

### 2. Trip Planner (Groq API)
- **Model:** `llama3-8b-8192` via Groq
- **Location:** `services/groq_service.py` → `generate_itinerary()`
- **Frontend:** `planner.html` ↔ `POST /planner/generate`
- **Output format:** Structured JSON (days, activities, budget, tips)
- **Inputs:** destination, days (1–30), budget, trip_type, preferences
- **Fallback:** Mock itinerary structure when `GROQ_API_KEY` is not set

### 3. Recommendation System (TF-IDF + Cosine Similarity)
- **Library:** scikit-learn `TfidfVectorizer` + `cosine_similarity`
- **Location:** `services/recommendation_service.py`
- **Frontend:** `discover.html` ↔ `POST /recommendations/suggest`
- **Dataset:** `data/destinations.json` (70 destinations, 25+ countries)
- **Features:** name, country, city, category, description, budget, trip_types, interests
- **Algorithm:**
  ```
  1. Build TF-IDF matrix from all 70 destination documents (ngram 1–2)
  2. Vectorize user query (country + budget + trip_type + interests)
  3. Compute cosine_similarity(query_vec, tfidf_matrix)
  4. Apply hard country filter (×0.05 penalty for off-country)
  5. Apply budget boost (×1.3 for exact match)
  6. Sort by similarity score → return top-N
  ```

---

## 🗃️ Database Schema

```sql
-- users
id, email, username, full_name, hashed_password, is_active,
is_pro, avatar_url, created_at, updated_at,
chat_count, plan_count, recommend_count

-- chat_messages
id, user_id, role (user|assistant), content, session_id, created_at

-- trip_plans
id, user_id, title, destination, days, budget, preferences (JSON),
trip_type, itinerary (JSON), status (draft|confirmed|archived), created_at

-- subscriptions
id, user_id, plan (free|pro|pro_annual), status (active|cancelled|expired),
amount_paid, currency, payment_method, transaction_id, starts_at, expires_at, created_at
```

---

## 🔒 Authentication Flow

```
1. User registers/logs in → POST /auth/register or /auth/login
2. Backend validates credentials → issues JWT token (7-day expiry)
3. Frontend stores token in localStorage as "tai_token"
4. Every API request includes: Authorization: Bearer <token>
5. Backend validates JWT → extracts user_id → fetches User from DB
6. On 401 → frontend redirects to login.html
```

---

## 💰 Subscription Plans

| Feature | Free | Pro ($9.99/mo) | Pro Annual ($89.99/yr) |
|---------|------|----------------|------------------------|
| Chat messages/day | 10 | Unlimited | Unlimited |
| Trip plans/month | 3 | Unlimited | Unlimited |
| Recommendations | 5 | Unlimited | Unlimited |
| PDF export | ✗ | ✓ | ✓ |
| Priority AI | ✗ | ✓ | ✓ |
| Priority support | ✗ | ✓ | ✓ |

---

## 🚀 Setup Instructions

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Set GROQ_API_KEY=your_key_here

# Run
uvicorn main:app --reload --port 8000
# API docs: http://localhost:8000/docs
```

### Frontend
```bash
# Serve with any static file server
cd frontend
python -m http.server 5500
# Or: npx serve . -p 5500
# Open: http://localhost:5500
```

### Environment Variables (`.env`)
```env
SECRET_KEY=your-super-secret-key-change-this
GROQ_API_KEY=gsk_your_groq_api_key
DEBUG=False
ALLOWED_ORIGINS=http://localhost:5500,http://127.0.0.1:5500
```

---

## 🔄 Changes Made vs Original Codebase

### Architecture Fixes
1. **CORS configuration** — Added wildcard + specific origins for local dev
2. **JWT token handling** — Unified token storage/retrieval in `api.js`
3. **Error propagation** — All API errors bubble `upgrade_required` flag to UI
4. **Session management** — Chat sessions correctly scoped per user_id

### Frontend Fixes
1. **API client (`api.js`)** — Created unified client replacing scattered fetch calls
2. **Input validation** — All forms validate before API calls with user-friendly errors
3. **Loading states** — Every async action shows proper loading indicator
4. **Upgrade flow** — HTTP 402 responses automatically show upgrade prompts
5. **Card preview** — Live updates as user types payment info

### AI Integration Fixes
1. **Chat history** — Passes last-10 messages as context to Groq on each request
2. **Itinerary JSON parsing** — Strips markdown code fences before JSON.parse
3. **TF-IDF indexing** — Builds corpus at module import (not per-request)
4. **Match scores** — Normalized 0–100% for frontend display

### New Files Created
- `backend/services/payment_service.py` — Complete mock payment processor
- `backend/routes/subscription.py` — All subscription endpoints (was missing)
- `frontend/pages/subscription.html` — Full pricing page (was missing)
- `frontend/pages/payment.html` — Checkout form with live card preview (new)
- `frontend/pages/payment-success.html` — Confirmation page (new)
- `frontend/pages/discover.html` — Recommendation system UI (was missing)
- `frontend/js/api.js` — Unified API client (was missing/scattered)
- `frontend/css/style.css` — Complete design system
- `backend/data/destinations.json` — 70-destination dataset

### Bugs Fixed
1. **Missing `session_id`** — Chat API now creates/persists session IDs
2. **Usage counters** — `user.chat_count`, `plan_count`, `recommend_count` properly incremented
3. **Pro status sync** — `Auth.setUser()` called after payment to sync UI immediately
4. **Free plan limits** — Correctly enforced server-side, communicated to frontend
5. **JWT expiry** — Token removed on 401 and redirected to login

---

## 🔮 Suggested Improvements Before Deployment

### Critical
- [ ] Replace mock payment with real **Stripe Checkout** or **Stripe PaymentIntent**
- [ ] Switch SQLite to **PostgreSQL** for production
- [ ] Add **rate limiting** (e.g., slowapi) to all API endpoints
- [ ] Set a strong, random `SECRET_KEY` (not hardcoded)
- [ ] Add proper **email verification** on registration
- [ ] Configure **HTTPS** + valid SSL certificate

### Important
- [ ] Add **password reset** flow (email OTP)
- [ ] Implement **token refresh** endpoint
- [ ] Add **logging** (structlog or loguru) to all services
- [ ] Add **Sentry** error tracking
- [ ] Add **Redis** for chat session caching

### Nice to Have
- [ ] PDF itinerary export (ReportLab or WeasyPrint)
- [ ] OAuth login (Google, Facebook)
- [ ] Wishlist / saved destinations
- [ ] Trip sharing via public link
- [ ] Multi-language support (i18n)
- [ ] Mobile app (React Native / Flutter)

---

## 📊 Full System Status After Integration

| Component | Status | Notes |
|-----------|--------|-------|
| Frontend → Backend auth | ✅ Working | JWT Bearer token in all requests |
| Chatbot (Groq) | ✅ Working | Mock fallback when no API key |
| Trip Planner (Groq) | ✅ Working | Structured JSON output with fallback |
| Recommendation System (TF-IDF) | ✅ Working | Full frontend page created |
| PRO Subscription Page | ✅ Working | Monthly + Annual toggle |
| Payment Form | ✅ Working | Live card preview + validation |
| Payment Success | ✅ Working | Receipt + pro status update |
| Dashboard | ✅ Working | Stats, trips, profile, subscription |
| Free Plan Limits | ✅ Working | Server-enforced, UI prompts upgrade |
| User Profile CRUD | ✅ Working | Full name + username editable |
| Chat History | ✅ Working | Per-session, loadable, clearable |
| Saved Trips | ✅ Working | CRUD + status management |
