"""API request/response schemas for FastAPI routes."""

from datetime import datetime

from pydantic import BaseModel


# --- Auth ---


class AuthRequest(BaseModel):
    username: str
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# --- Chat ---


class ChatRequest(BaseModel):
    message: str
    session_id: int | None = None


class ChatStreamEvent(BaseModel):
    """Shape of each SSE data payload."""

    text: str | None = None
    done: bool = False
    session_id: int | None = None


# --- Sessions / History ---


class MessageResponse(BaseModel):
    role: str
    content: str
    citations: list[dict] = []
    created_at: datetime


class SessionResponse(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime


class SessionDetailResponse(BaseModel):
    id: int
    title: str
    messages: list[MessageResponse]
