"""Data Transfer Objects for use case inputs and outputs."""

from dataclasses import dataclass
from datetime import datetime

from pydantic import BaseModel


# --- Auth ---


class RegisterInput(BaseModel):
    username: str
    password: str


class LoginInput(BaseModel):
    username: str
    password: str


class AuthResult(BaseModel):
    access_token: str
    token_type: str = "bearer"


# --- Chat ---


class ChatInput(BaseModel):
    message: str
    session_id: int | None = None
    user_id: int


class HistoryEntry(BaseModel):
    role: str
    content: str


# --- History ---


class SessionSummary(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime


class MessageDTO(BaseModel):
    role: str
    content: str
    citations: list[dict] = []
    created_at: datetime


class SessionDetail(BaseModel):
    id: int
    title: str
    messages: list[MessageDTO]
