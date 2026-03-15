from abc import ABC, abstractmethod

from backend.domain.models import ChatMessage, ChatSession, User


class IUserRepository(ABC):
    @abstractmethod
    def get_by_username(self, username: str) -> User | None: ...

    @abstractmethod
    def create(self, user: User) -> User: ...


class ISessionRepository(ABC):
    @abstractmethod
    def create(self, session: ChatSession) -> ChatSession: ...

    @abstractmethod
    def get_by_id(self, session_id: int, user_id: int) -> ChatSession | None: ...

    @abstractmethod
    def list_by_user(self, user_id: int) -> list[ChatSession]: ...

    @abstractmethod
    def update(self, session: ChatSession) -> ChatSession: ...


class IMessageRepository(ABC):
    @abstractmethod
    def create(self, message: ChatMessage) -> ChatMessage: ...

    @abstractmethod
    def list_by_session(self, session_id: int) -> list[ChatMessage]: ...
