from typing import Annotated

import cohere
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session

from backend.application.tools.retrieval import (
    CohereRerankStep,
    KeywordSearchStep,
    RetrievalPipeline,
    ThresholdStep,
    VectorSearchStep,
)
from backend.application.tools.sql_query import SQLQueryTool
from backend.application.use_cases.chat import ChatUseCase
from backend.application.use_cases.history import GetSessionUseCase, ListSessionsUseCase
from backend.domain.models import User
from backend.infrastructure.auth import AuthService
from backend.infrastructure.database import get_engine, get_session
from backend.infrastructure.repositories import MessageRepository, SessionRepository, UserRepository
from shared.config import Settings, get_settings

security = HTTPBearer()


def get_db_session(settings: Annotated[Settings, Depends(get_settings)]) -> Session:
    engine = get_engine(settings)
    with get_session(engine) as session:
        yield session


def get_auth_service(settings: Annotated[Settings, Depends(get_settings)]) -> AuthService:
    return AuthService(settings)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    db_session: Annotated[Session, Depends(get_db_session)],
) -> User:
    username = auth_service.decode_token(credentials.credentials)
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user_repo = UserRepository(db_session)
    user = user_repo.get_by_username(username)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def get_chat_use_case(
    db_session: Annotated[Session, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> ChatUseCase:
    cohere_client = cohere.Client(api_key=settings.cohere_api_key)

    pipeline = RetrievalPipeline(
        steps=[
            VectorSearchStep(db_session, cohere_client, settings.cohere_embed_model),
            KeywordSearchStep(db_session),
            CohereRerankStep(cohere_client, settings.cohere_rerank_model),
            ThresholdStep(settings.reranker_threshold),
        ]
    )
    sql_tool = SQLQueryTool(db_session)
    return ChatUseCase(retrieval_pipeline=pipeline, sql_tool=sql_tool)


def get_list_sessions_use_case(db_session: Annotated[Session, Depends(get_db_session)]) -> ListSessionsUseCase:
    return ListSessionsUseCase(SessionRepository(db_session))


def get_session_detail_use_case(db_session: Annotated[Session, Depends(get_db_session)]) -> GetSessionUseCase:
    return GetSessionUseCase(SessionRepository(db_session), MessageRepository(db_session))
