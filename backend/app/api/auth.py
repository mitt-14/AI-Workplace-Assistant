import sqlite3

from fastapi import (
    APIRouter,
    Depends,
    status,
)

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
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from app.security.email_security import (
    validate_registration_email,
)
from app.security.password_policy import (
    validate_password_policy,
)
from app.services.password_reset_service import (
    request_password_reset,
    reset_password,
)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


def _user_response(
    user: dict,
) -> UserResponse:
    return UserResponse(
        user_id=user["user_id"],
        name=user["name"],
        email=user["email"],
        created_at=user["created_at"],
    )


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=(
        status.HTTP_201_CREATED
    ),
)
def register_user(
    payload: UserRegisterRequest,
) -> AuthResponse:
    normalized_email = (
        validate_registration_email(
            str(payload.email)
        )
    )

    validate_password_policy(
        payload.password,
        name=payload.name,
        email=normalized_email,
    )

    if (
        get_user_by_email(
            normalized_email
        )
        is not None
    ):
        raise EmailAlreadyRegisteredError()

    try:
        user = create_user(
            name=payload.name,
            email=normalized_email,
            password_hash=hash_password(
                payload.password
            ),
        )
    except sqlite3.IntegrityError as exc:
        raise EmailAlreadyRegisteredError() from exc

    token = create_access_token(
        user["user_id"],
        user.get(
            "token_version",
            0,
        ),
    )

    return AuthResponse(
        access_token=token,
        expires_in_seconds=(
            settings
            .jwt_access_token_expire_minutes
            * 60
        ),
        user=_user_response(
            user
        ),
    )


@router.post(
    "/login",
    response_model=AuthResponse,
)
def login_user(
    payload: UserLoginRequest,
) -> AuthResponse:
    user = get_user_by_email(
        str(payload.email)
    )

    if (
        user is None
        or not verify_password(
            payload.password,
            user["password_hash"],
        )
    ):
        raise AuthenticationError(
            "Invalid email or password."
        )

    token = create_access_token(
        user["user_id"],
        user.get(
            "token_version",
            0,
        ),
    )

    return AuthResponse(
        access_token=token,
        expires_in_seconds=(
            settings
            .jwt_access_token_expire_minutes
            * 60
        ),
        user=_user_response(
            user
        ),
    )


@router.post(
    "/forgot-password",
    response_model=ForgotPasswordResponse,
)
def forgot_password(
    payload: ForgotPasswordRequest,
) -> ForgotPasswordResponse:
    return ForgotPasswordResponse(
        **request_password_reset(
            str(payload.email)
        )
    )


@router.post(
    "/reset-password",
    response_model=ResetPasswordResponse,
)
def reset_user_password(
    payload: ResetPasswordRequest,
) -> ResetPasswordResponse:
    reset_password(
        token=payload.token,
        new_password=payload.new_password,
    )

    return ResetPasswordResponse(
        message=(
            "Password changed successfully. "
            "Please sign in with your new password."
        )
    )


@router.get(
    "/me",
    response_model=UserResponse,
)
def current_user(
    user: dict = Depends(
        get_current_user
    ),
) -> UserResponse:
    return _user_response(
        user
    )
