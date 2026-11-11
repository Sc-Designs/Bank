from fastapi import APIRouter, status

from ..controller.user_controller import (
    RegisterUserRequest,
    RegisteredUserResponse,
    register_user,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.post(
    "/register",
    response_model=RegisteredUserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user(payload: RegisterUserRequest) -> RegisteredUserResponse:
    return register_user(payload)
