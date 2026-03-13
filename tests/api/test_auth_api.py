import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from backend.domain.models import ChatMessage, ChatSession, User  # noqa: F401 — register tables
from backend.main import app
from backend.presentation.dependencies import get_db_session
from shared.config import Settings, get_settings
from shared.models import Chunk, Document  # noqa: F401 — register tables


@pytest.fixture
def test_settings():
    return Settings(jwt_secret_key="test-secret", database_path=":memory:")


@pytest.fixture
def client(test_settings):
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    def override_session():
        with Session(engine) as session:
            yield session

    def override_settings():
        return test_settings

    app.dependency_overrides[get_db_session] = override_session
    app.dependency_overrides[get_settings] = override_settings

    with TestClient(app, raise_server_exceptions=False) as c:
        yield c

    app.dependency_overrides.clear()


def test_register_and_login(client: TestClient):
    resp = client.post("/api/auth/register", json={"username": "testuser", "password": "pass123"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()

    resp = client.post("/api/auth/login", json={"username": "testuser", "password": "pass123"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_register_duplicate(client: TestClient):
    client.post("/api/auth/register", json={"username": "dupe", "password": "pass"})
    resp = client.post("/api/auth/register", json={"username": "dupe", "password": "pass"})
    assert resp.status_code == 409


def test_login_wrong_password(client: TestClient):
    client.post("/api/auth/register", json={"username": "user1", "password": "correct"})
    resp = client.post("/api/auth/login", json={"username": "user1", "password": "wrong"})
    assert resp.status_code == 401
