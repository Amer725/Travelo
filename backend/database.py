from sqlalchemy import create_engine, Column, Integer, String, Boolean, Float, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.sql import func
from config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ─── Models ───────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id        = Column(Integer, primary_key=True, index=True)
    email     = Column(String, unique=True, index=True, nullable=False)
    username  = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_pro    = Column(Boolean, default=False)
    avatar_url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Usage counters
    chat_count      = Column(Integer, default=0)
    plan_count      = Column(Integer, default=0)
    recommend_count = Column(Integer, default=0)

    # Relations
    chats         = relationship("ChatMessage", back_populates="user", cascade="all, delete")
    trips         = relationship("TripPlan", back_populates="user", cascade="all, delete")
    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role       = Column(String, nullable=False)   # "user" | "assistant"
    content    = Column(Text, nullable=False)
    session_id = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="chats")


class TripPlan(Base):
    __tablename__ = "trip_plans"

    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title       = Column(String, nullable=False)
    destination = Column(String, nullable=False)
    days        = Column(Integer, nullable=False)
    budget      = Column(String, nullable=False)   # low / medium / high
    preferences = Column(JSON, nullable=True)      # list of interests
    trip_type   = Column(String, nullable=True)    # adventure / cultural / relaxing …
    itinerary   = Column(JSON, nullable=True)      # structured plan from AI
    status      = Column(String, default="draft")  # draft / confirmed / archived
    created_at  = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="trips")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id             = Column(Integer, primary_key=True, index=True)
    user_id        = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    plan           = Column(String, nullable=False)     # "free" | "pro" | "pro_annual"
    status         = Column(String, default="active")   # active | cancelled | expired
    amount_paid    = Column(Float, nullable=True)
    currency       = Column(String, default="USD")
    payment_method = Column(String, nullable=True)
    transaction_id = Column(String, nullable=True, unique=True)
    starts_at      = Column(DateTime(timezone=True), server_default=func.now())
    expires_at     = Column(DateTime(timezone=True), nullable=True)
    created_at     = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="subscriptions")


# ─── DB Helpers ───────────────────────────────────────────────────────────────

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
