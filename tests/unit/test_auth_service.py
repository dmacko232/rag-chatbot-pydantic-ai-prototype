from backend.infrastructure.auth import AuthService
from shared.config import Settings


def _make_auth_service() -> AuthService:
    settings = Settings(jwt_secret_key="test-secret", jwt_expire_minutes=30)
    return AuthService(settings)


def test_hash_and_verify_password():
    auth = _make_auth_service()
    hashed = auth.hash_password("mypassword")
    assert auth.verify_password("mypassword", hashed)
    assert not auth.verify_password("wrong", hashed)


def test_create_and_decode_token():
    auth = _make_auth_service()
    token = auth.create_token("testuser")
    assert auth.decode_token(token) == "testuser"


def test_decode_invalid_token():
    auth = _make_auth_service()
    assert auth.decode_token("invalid.token.here") is None
