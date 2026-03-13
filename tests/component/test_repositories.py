import pytest
from sqlmodel import Session, SQLModel, create_engine

from backend.domain.models import ChatMessage, ChatSession, User
from backend.infrastructure.repositories import MessageRepository, SessionRepository, UserRepository


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def test_user_create_and_get(db_session: Session):
    repo = UserRepository(db_session)
    user = repo.create(User(username="alice", hashed_password="hash123"))
    assert user.id is not None

    found = repo.get_by_username("alice")
    assert found is not None
    assert found.id == user.id


def test_user_not_found(db_session: Session):
    repo = UserRepository(db_session)
    assert repo.get_by_username("nonexistent") is None


def test_session_crud(db_session: Session):
    user_repo = UserRepository(db_session)
    user = user_repo.create(User(username="bob", hashed_password="hash"))

    session_repo = SessionRepository(db_session)
    chat_session = session_repo.create(ChatSession(user_id=user.id, title="Test Chat"))
    assert chat_session.id is not None

    found = session_repo.get_by_id(chat_session.id, user.id)
    assert found is not None
    assert found.title == "Test Chat"

    sessions = session_repo.list_by_user(user.id)
    assert len(sessions) == 1


def test_message_crud(db_session: Session):
    user_repo = UserRepository(db_session)
    user = user_repo.create(User(username="carol", hashed_password="hash"))

    session_repo = SessionRepository(db_session)
    chat_session = session_repo.create(ChatSession(user_id=user.id, title="Chat"))

    msg_repo = MessageRepository(db_session)
    msg_repo.create(ChatMessage(session_id=chat_session.id, role="user", content="Hello"))
    msg_repo.create(ChatMessage(session_id=chat_session.id, role="assistant", content="Hi there"))

    messages = msg_repo.list_by_session(chat_session.id)
    assert len(messages) == 2
    assert messages[0].role == "user"
    assert messages[1].role == "assistant"
