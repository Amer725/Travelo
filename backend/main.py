"""
TravelAI Backend — FastAPI Application
Run with: uvicorn main:app --reload --port 8000
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from config import settings
from database import init_db
from routes import auth, chatbot, planner, recommendations, subscription


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    print(f"✅ TravelAI API v{settings.API_VERSION} started")
    print(f"   Debug mode : {settings.DEBUG}")
    print(f"   Database   : {settings.DATABASE_URL}")
    yield


app = FastAPI(
    title       = "TravelAI API",
    description = "AI-powered travel planning platform",
    version     = settings.API_VERSION,
    lifespan    = lifespan,
)

# ─── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins     = settings.ALLOWED_ORIGINS,
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)

# ─── Routes ───────────────────────────────────────────────────────────────────
PREFIX = f"/api/{settings.API_VERSION}"

app.include_router(auth.router,            prefix=PREFIX)
app.include_router(chatbot.router,         prefix=PREFIX)
app.include_router(planner.router,         prefix=PREFIX)
app.include_router(recommendations.router, prefix=PREFIX)
app.include_router(subscription.router,    prefix=PREFIX)


# ─── Health ───────────────────────────────────────────────────────────────────
@app.get("/health", tags=["health"])
def health():
    return {"status": "ok", "version": settings.API_VERSION}


@app.get("/", include_in_schema=False)
def root():
    return JSONResponse({"message": "TravelAI API", "docs": "/docs"})
