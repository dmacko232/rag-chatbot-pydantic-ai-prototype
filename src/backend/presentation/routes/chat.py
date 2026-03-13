import json
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlmodel import Session

from backend.application.use_cases.chat import ChatUseCase
from backend.domain.models import ChatMessage, ChatRequest, ChatSession, User
from backend.infrastructure.repositories import MessageRepository, SessionRepository
from backend.presentation.dependencies import get_chat_use_case, get_current_user, get_db_session

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("")
async def chat(
    body: ChatRequest,
    user: Annotated[User, Depends(get_current_user)],
    chat_use_case: Annotated[ChatUseCase, Depends(get_chat_use_case)],
    db_session: Annotated[Session, Depends(get_db_session)],
) -> dict:
    session_repo = SessionRepository(db_session)
    message_repo = MessageRepository(db_session)

    if body.session_id:
        chat_session = session_repo.get_by_id(body.session_id, user.id)
    else:
        chat_session = None

    if not chat_session:
        chat_session = session_repo.create(
            ChatSession(user_id=user.id, title=body.message[:50])
        )

    history = _build_history(message_repo, chat_session.id)

    message_repo.create(ChatMessage(session_id=chat_session.id, role="user", content=body.message))

    response_text, citations = await chat_use_case.execute(body.message, history)

    message_repo.create(
        ChatMessage(
            session_id=chat_session.id,
            role="assistant",
            content=response_text,
            citations=json.dumps(citations),
        )
    )

    chat_session.updated_at = datetime.utcnow()
    session_repo.update(chat_session)

    return {
        "session_id": chat_session.id,
        "response": response_text,
        "citations": citations,
    }


@router.post("/stream")
async def chat_stream(
    body: ChatRequest,
    user: Annotated[User, Depends(get_current_user)],
    chat_use_case: Annotated[ChatUseCase, Depends(get_chat_use_case)],
    db_session: Annotated[Session, Depends(get_db_session)],
) -> StreamingResponse:
    session_repo = SessionRepository(db_session)
    message_repo = MessageRepository(db_session)

    if body.session_id:
        chat_session = session_repo.get_by_id(body.session_id, user.id)
    else:
        chat_session = None

    if not chat_session:
        chat_session = session_repo.create(
            ChatSession(user_id=user.id, title=body.message[:50])
        )

    history = _build_history(message_repo, chat_session.id)
    message_repo.create(ChatMessage(session_id=chat_session.id, role="user", content=body.message))

    async def event_stream():
        full_response = ""
        async for chunk in chat_use_case.execute_stream(body.message, history):
            full_response += chunk
            yield f"data: {json.dumps({'text': chunk})}\n\n"

        message_repo.create(
            ChatMessage(session_id=chat_session.id, role="assistant", content=full_response)
        )
        chat_session.updated_at = datetime.utcnow()
        session_repo.update(chat_session)

        yield f"data: {json.dumps({'done': True, 'session_id': chat_session.id})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


def _build_history(message_repo: MessageRepository, session_id: int) -> list[dict]:
    messages = message_repo.list_by_session(session_id)
    return [{"role": m.role, "content": m.content} for m in messages]
