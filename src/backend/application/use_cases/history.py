import json

from backend.application.dto import MessageDTO, SessionDetail, SessionSummary
from backend.domain.interfaces import IMessageRepository, ISessionRepository


class ListSessionsUseCase:
    def __init__(self, session_repo: ISessionRepository) -> None:
        self._session_repo = session_repo

    def execute(self, user_id: int) -> list[SessionSummary]:
        sessions = self._session_repo.list_by_user(user_id)
        return [
            SessionSummary(
                id=s.id,
                title=s.title,
                created_at=s.created_at,
                updated_at=s.updated_at,
            )
            for s in sessions
        ]


class GetSessionUseCase:
    def __init__(self, session_repo: ISessionRepository, message_repo: IMessageRepository) -> None:
        self._session_repo = session_repo
        self._message_repo = message_repo

    def execute(self, session_id: int, user_id: int) -> SessionDetail | None:
        session = self._session_repo.get_by_id(session_id, user_id)
        if not session:
            return None

        messages = self._message_repo.list_by_session(session_id)
        return SessionDetail(
            id=session.id,
            title=session.title,
            messages=[
                MessageDTO(
                    role=m.role,
                    content=m.content,
                    citations=json.loads(m.citations),
                    created_at=m.created_at,
                )
                for m in messages
            ],
        )
