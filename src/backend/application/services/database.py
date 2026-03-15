from sqlmodel import Session, SQLModel

from backend.domain.models import ChatMessage, ChatSession, User  # noqa: F401 — register tables
from shared.config import Settings
from shared.db import create_db_engine
from shared.models import Chunk, Document  # noqa: F401 — register tables


def get_engine(settings: Settings):
    engine = create_db_engine(settings)
    SQLModel.metadata.create_all(engine)
    return engine


def get_session(engine) -> Session:
    return Session(engine)
