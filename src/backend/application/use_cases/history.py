import json

from backend.domain.interfaces import IMessageRepository, ISessionRepository
from backend.domain.models import ChatMessage, ChatMessageResponse, ChatSession, SessionDetailResponse, SessionResponse


class ListSessionsUseCase:
    def __init__(self, session_repo: ISessionRepository) -> None:
        self._session_repo = session_repo

    def execute(self, user_id: int) -> list[SessionResponse]:
        sessions = self._session_repo.list_by_user(user_id)
        return [
            SessionResponse(id=s.id, title=s.title, created_at=s.created_at, updated_at=s.updated_at) for s in sessions
        ]


class GetSessionUseCase:
    def __init__(self, session_repo: ISessionRepository, message_repo: IMessageRepository) -> None:
        self._session_repo = session_repo
        self._message_repo = message_repo

    def execute(self, session_id: int, user_id: int) -> SessionDetailResponse | None:
        session = self._session_repo.get_by_id(session_id, user_id)
        if not session:
            return None

        messages = self._message_repo.list_by_session(session_id)
        return SessionDetailResponse(
            id=session.id,
            title=session.title,
            messages=[
                ChatMessageResponse(
                    role=m.role,
                    content=m.content,
                    citations=json.loads(m.citations),
                    created_at=m.created_at,
                )
                for m in messages
            ],
        )
