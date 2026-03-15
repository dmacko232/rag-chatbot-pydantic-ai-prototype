from typing import Annotated

import cohere
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session

from backend.application.repositories import MessageRepository, SessionRepository, UserRepository
from backend.application.services.auth import AuthService
from backend.application.services.database import get_engine, get_session
from backend.application.tools.retrieval import CohereReranker, HybridSearch, RetrievalService, ScoreFilter
from backend.application.tools.sql_query import SQLQueryTool
from backend.application.use_cases.chat import ChatUseCase
from backend.application.use_cases.history import GetSessionUseCase, ListSessionsUseCase
from backend.domain.models import User
from shared.config import Settings, get_settings
from shared.prompts import get_config_section

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
    retrieval_cfg = get_config_section("retrieval")
    cohere_client = cohere.Client(api_key=settings.cohere_api_key)

    retrieval = RetrievalService(
        hybrid_search=HybridSearch(
            db_session,
            cohere_client,
            settings.cohere_embed_model,
            vector_top_k=retrieval_cfg["vector_top_k"],
            bm25_top_k=retrieval_cfg["bm25_top_k"],
            rrf_k=retrieval_cfg["rrf_k"],
            rrf_alpha=retrieval_cfg["rrf_alpha"],
            rrf_top_n=retrieval_cfg["rrf_top_n"],
        ),
        reranker=CohereReranker(
            cohere_client,
            settings.cohere_rerank_model,
            top_n=retrieval_cfg["rerank_top_n"],
        ),
        score_filter=ScoreFilter(threshold=retrieval_cfg["score_threshold"]),
    )
    sql_tool = SQLQueryTool(db_session)
    return ChatUseCase(retrieval_service=retrieval, sql_tool=sql_tool)


def get_list_sessions_use_case(db_session: Annotated[Session, Depends(get_db_session)]) -> ListSessionsUseCase:
    return ListSessionsUseCase(SessionRepository(db_session))


def get_session_detail_use_case(db_session: Annotated[Session, Depends(get_db_session)]) -> GetSessionUseCase:
    return GetSessionUseCase(SessionRepository(db_session), MessageRepository(db_session))
