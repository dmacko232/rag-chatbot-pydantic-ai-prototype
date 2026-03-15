from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from backend.application.use_cases.history import GetSessionUseCase, ListSessionsUseCase
from backend.domain.models import User
from backend.presentation.dependencies import get_current_user, get_list_sessions_use_case, get_session_detail_use_case
from backend.presentation.schemas import MessageResponse, SessionDetailResponse, SessionResponse

router = APIRouter(prefix="/sessions", tags=["history"])


@router.get("", response_model=list[SessionResponse])
def list_sessions(
    user: Annotated[User, Depends(get_current_user)],
    use_case: Annotated[ListSessionsUseCase, Depends(get_list_sessions_use_case)],
) -> list[SessionResponse]:
    summaries = use_case.execute(user.id)
    return [
        SessionResponse(
            id=s.id, title=s.title, created_at=s.created_at, updated_at=s.updated_at
        )
        for s in summaries
    ]


@router.get("/{session_id}", response_model=SessionDetailResponse)
def get_session(
    session_id: int,
    user: Annotated[User, Depends(get_current_user)],
    use_case: Annotated[GetSessionUseCase, Depends(get_session_detail_use_case)],
) -> SessionDetailResponse:
    detail = use_case.execute(session_id, user.id)
    if not detail:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    return SessionDetailResponse(
        id=detail.id,
        title=detail.title,
        messages=[
            MessageResponse(
                role=m.role,
                content=m.content,
                citations=m.citations,
                created_at=m.created_at,
            )
            for m in detail.messages
        ],
    )
