from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from backend.domain.models import TokenResponse, User, UserCreate
from backend.infrastructure.auth import AuthService
from backend.infrastructure.repositories import UserRepository
from backend.presentation.dependencies import get_auth_service, get_db_session

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
def register(
    body: UserCreate,
    db_session: Annotated[Session, Depends(get_db_session)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    user_repo = UserRepository(db_session)

    if user_repo.get_by_username(body.username):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")

    user = User(username=body.username, hashed_password=auth_service.hash_password(body.password))
    user_repo.create(user)

    token = auth_service.create_token(user.username)
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
def login(
    body: UserCreate,
    db_session: Annotated[Session, Depends(get_db_session)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    user_repo = UserRepository(db_session)
    user = user_repo.get_by_username(body.username)

    if not user or not auth_service.verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = auth_service.create_token(user.username)
    return TokenResponse(access_token=token)
