from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from backend.application.use_cases.history import GetSessionUseCase, ListSessionsUseCase
from backend.domain.models import SessionDetailResponse, SessionResponse, User
from backend.presentation.dependencies import get_current_user, get_list_sessions_use_case, get_session_detail_use_case

router = APIRouter(prefix="/sessions", tags=["history"])


@router.get("", response_model=list[SessionResponse])
def list_sessions(
    user: Annotated[User, Depends(get_current_user)],
    use_case: Annotated[ListSessionsUseCase, Depends(get_list_sessions_use_case)],
) -> list[SessionResponse]:
    return use_case.execute(user.id)


@router.get("/{session_id}", response_model=SessionDetailResponse)
def get_session(
    session_id: int,
    user: Annotated[User, Depends(get_current_user)],
    use_case: Annotated[GetSessionUseCase, Depends(get_session_detail_use_case)],
) -> SessionDetailResponse:
    result = use_case.execute(session_id, user.id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return result
