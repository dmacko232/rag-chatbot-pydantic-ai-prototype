from sqlmodel import Session, select

from backend.domain.interfaces import IMessageRepository, ISessionRepository, IUserRepository
from backend.domain.models import ChatMessage, ChatSession, User


class UserRepository(IUserRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_username(self, username: str) -> User | None:
        return self._session.exec(select(User).where(User.username == username)).first()

    def create(self, user: User) -> User:
        self._session.add(user)
        self._session.commit()
        self._session.refresh(user)
        return user


class SessionRepository(ISessionRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, chat_session: ChatSession) -> ChatSession:
        self._session.add(chat_session)
        self._session.commit()
        self._session.refresh(chat_session)
        return chat_session

    def get_by_id(self, session_id: int, user_id: int) -> ChatSession | None:
        return self._session.exec(
            select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == user_id)
        ).first()

    def list_by_user(self, user_id: int) -> list[ChatSession]:
        return list(
            self._session.exec(
                select(ChatSession).where(ChatSession.user_id == user_id).order_by(ChatSession.updated_at.desc())
            ).all()
        )

    def update(self, chat_session: ChatSession) -> ChatSession:
        self._session.add(chat_session)
        self._session.commit()
        self._session.refresh(chat_session)
        return chat_session


class MessageRepository(IMessageRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, message: ChatMessage) -> ChatMessage:
        self._session.add(message)
        self._session.commit()
        self._session.refresh(message)
        return message

    def list_by_session(self, session_id: int) -> list[ChatMessage]:
        return list(
            self._session.exec(
                select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at)
            ).all()
        )
