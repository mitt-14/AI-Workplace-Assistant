import sqlite3

from fastapi import APIRouter, Depends, status

from app.core.auth import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.core.config import settings
from app.core.exceptions import (
    AuthenticationError,
    EmailAlreadyRegisteredError,
)
from app.core.user_store import (
    create_user,
    get_user_by_email,
)
from app.schemas.auth import (
    AuthResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


def _user_response(user: dict) -> UserResponse:
    return UserResponse(
        user_id=user["user_id"],
        name=user["name"],
        email=user["email"],
        created_at=user["created_at"],
    )


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_user(
    payload: UserRegisterRequest,
) -> AuthResponse:
    if get_user_by_email(payload.email) is not None:
        raise EmailAlreadyRegisteredError()

    try:
        user = create_user(
            name=payload.name,
            email=payload.email,
            password_hash=hash_password(payload.password),
        )
    except sqlite3.IntegrityError as exc:
        raise EmailAlreadyRegisteredError() from exc

    token = create_access_token(user["user_id"])

    return AuthResponse(
        access_token=token,
        expires_in_seconds=(
            settings.jwt_access_token_expire_minutes * 60
        ),
        user=_user_response(user),
    )


@router.post(
    "/login",
    response_model=AuthResponse,
)
def login_user(
    payload: UserLoginRequest,
) -> AuthResponse:
    user = get_user_by_email(payload.email)

    if user is None or not verify_password(
        payload.password,
        user["password_hash"],
    ):
        raise AuthenticationError(
            "Invalid email or password."
        )

    token = create_access_token(user["user_id"])

    return AuthResponse(
        access_token=token,
        expires_in_seconds=(
            settings.jwt_access_token_expire_minutes * 60
        ),
        user=_user_response(user),
    )


@router.get(
    "/me",
    response_model=UserResponse,
)
def current_user(
    user: dict = Depends(get_current_user),
) -> UserResponse:
    return _user_response(user)
