from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from shared.config import Settings


class AuthService:
    def __init__(self, settings: Settings) -> None:
        self._secret = settings.jwt_secret_key
        self._algorithm = settings.jwt_algorithm
        self._expire_minutes = settings.jwt_expire_minutes

    def hash_password(self, password: str) -> str:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    def verify_password(self, plain: str, hashed: str) -> bool:
        return bcrypt.checkpw(plain.encode(), hashed.encode())

    def create_token(self, username: str) -> str:
        expire = datetime.now(timezone.utc) + timedelta(minutes=self._expire_minutes)
        return jwt.encode({"sub": username, "exp": expire}, self._secret, algorithm=self._algorithm)

    def decode_token(self, token: str) -> str | None:
        try:
            payload = jwt.decode(token, self._secret, algorithms=[self._algorithm])
            return payload.get("sub")
        except JWTError:
            return None
