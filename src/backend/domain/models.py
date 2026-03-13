from datetime import datetime

from pydantic import BaseModel
from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ChatSession(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    title: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ChatMessage(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="chatsession.id", index=True)
    role: str  # "user" | "assistant"
    content: str
    citations: str = "[]"
    created_at: datetime = Field(default_factory=datetime.utcnow)


# --- API Schemas ---


class UserCreate(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ChatRequest(BaseModel):
    message: str
    session_id: int | None = None


class ChatMessageResponse(BaseModel):
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
    messages: list[ChatMessageResponse]
