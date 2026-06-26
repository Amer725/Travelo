from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # App
    APP_NAME: str = "TravelAI"
    DEBUG: bool = False
    API_VERSION: str = "v1"
    
    # Security
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Database
    DATABASE_URL: str = "sqlite:///./travelai.db"
    
    # Groq AI
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama3-8b-8192"
    
    # CORS
    ALLOWED_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "*"
    ]
    
    # Payment (Mock — replace with Stripe in production)
    PAYMENT_MOCK: bool = True
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    
    # Subscription Plans
    PRO_PRICE_USD: float = 9.99
    PRO_PRICE_ANNUAL_USD: float = 89.99
    
    # Free Plan Limits
    FREE_CHAT_LIMIT: int = 10
    FREE_PLAN_LIMIT: int = 3
    FREE_RECOMMEND_LIMIT: int = 5
    
    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
