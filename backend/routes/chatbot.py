from typing import List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from config import settings
from database import ChatMessage, User, get_db
from routes.auth import get_current_user
from services.groq_service import chat

router = APIRouter(prefix="/chat", tags=["chatbot"])


class MessageRequest(BaseModel):
    message:    str
    session_id: Optional[str] = None


class MessageResponse(BaseModel):
    role:       str
    content:    str
    session_id: str


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _check_limit(user: User):
    if not user.is_pro and user.chat_count >= settings.FREE_CHAT_LIMIT:
        raise HTTPException(
            status_code=402,
            detail={
                "message": "Daily chat limit reached. Upgrade to Pro for unlimited chats.",
                "upgrade_required": True,
            },
        )


# ─── Routes ───────────────────────────────────────────────────────────────────

@router.post("/message", response_model=MessageResponse)
def send_message(
    body: MessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _check_limit(current_user)

    session_id = body.session_id or str(uuid.uuid4())

    # Load conversation history for this session
    history_rows = (
        db.query(ChatMessage)
        .filter(
            ChatMessage.user_id    == current_user.id,
            ChatMessage.session_id == session_id,
        )
        .order_by(ChatMessage.created_at)
        .all()
    )
    history = [{"role": r.role, "content": r.content} for r in history_rows]

    # Call AI
    reply = chat(history, body.message)

    # Persist both messages
    db.add(ChatMessage(user_id=current_user.id, role="user",      content=body.message, session_id=session_id))
    db.add(ChatMessage(user_id=current_user.id, role="assistant", content=reply,         session_id=session_id))
    current_user.chat_count += 1
    db.commit()

    return {"role": "assistant", "content": reply, "session_id": session_id}


@router.get("/history")
def get_history(
    session_id: Optional[str] = None,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(ChatMessage).filter(ChatMessage.user_id == current_user.id)
    if session_id:
        q = q.filter(ChatMessage.session_id == session_id)
    messages = q.order_by(ChatMessage.created_at.desc()).limit(limit).all()
    return [
        {
            "id":         m.id,
            "role":       m.role,
            "content":    m.content,
            "session_id": m.session_id,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
        for m in reversed(messages)
    ]


@router.get("/sessions")
def get_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from sqlalchemy import distinct, func
    rows = (
        db.query(
            ChatMessage.session_id,
            func.count(ChatMessage.id).label("count"),
            func.max(ChatMessage.created_at).label("last_at"),
        )
        .filter(ChatMessage.user_id == current_user.id)
        .group_by(ChatMessage.session_id)
        .order_by(func.max(ChatMessage.created_at).desc())
        .limit(20)
        .all()
    )
    return [{"session_id": r.session_id, "message_count": r.count, "last_at": r.last_at.isoformat() if r.last_at else None} for r in rows]


@router.delete("/history")
def clear_history(
    session_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(ChatMessage).filter(ChatMessage.user_id == current_user.id)
    if session_id:
        q = q.filter(ChatMessage.session_id == session_id)
    q.delete()
    db.commit()
    return {"message": "History cleared."}
