import hashlib
from datetime import (
    datetime,
    timedelta,
    timezone,
)

import bcrypt
import jwt
from fastapi import Depends
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from jwt import InvalidTokenError

from app.core.config import settings
from app.core.exceptions import (
    AuthenticationError,
)
from app.core.user_store import (
    get_user_by_id,
)

bearer_scheme = HTTPBearer(
    auto_error=False
)


def _password_bytes(
    password: str,
) -> bytes:
    # SHA-256 preserves the full password before
    # bcrypt's adaptive work factor and avoids
    # bcrypt's 72-byte raw-input limit.
    return hashlib.sha256(
        password.encode("utf-8")
    ).digest()


def hash_password(
    password: str,
) -> str:
    return bcrypt.hashpw(
        _password_bytes(password),
        bcrypt.gensalt(
            rounds=12
        ),
    ).decode("utf-8")


def verify_password(
    password: str,
    password_hash: str,
) -> bool:
    try:
        return bcrypt.checkpw(
            _password_bytes(password),
            password_hash.encode(
                "utf-8"
            ),
        )
    except (
        ValueError,
        TypeError,
    ):
        return False


def create_access_token(
    user_id: str,
    token_version: int = 0,
) -> str:
    now = datetime.now(
        timezone.utc
    )

    expires_at = now + timedelta(
        minutes=(
            settings
            .jwt_access_token_expire_minutes
        )
    )

    payload = {
        "sub": user_id,
        "ver": int(
            token_version
        ),
        "iat": now,
        "exp": expires_at,
        "type": "access",
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=(
            settings.jwt_algorithm
        ),
    )


def decode_access_token(
    token: str,
) -> tuple[str, int]:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[
                settings.jwt_algorithm
            ],
        )
    except InvalidTokenError as exc:
        raise AuthenticationError(
            "The access token is invalid "
            "or has expired."
        ) from exc

    if payload.get("type") != "access":
        raise AuthenticationError(
            "Invalid token type."
        )

    user_id = payload.get("sub")

    if not user_id:
        raise AuthenticationError(
            "The access token has "
            "no user identity."
        )

    return (
        str(user_id),
        int(
            payload.get(
                "ver",
                0,
            )
        ),
    )


def get_current_user(
    credentials: (
        HTTPAuthorizationCredentials
        | None
    ) = Depends(
        bearer_scheme
    ),
) -> dict:
    if credentials is None:
        raise AuthenticationError(
            "Authentication is required."
        )

    (
        user_id,
        token_version,
    ) = decode_access_token(
        credentials.credentials
    )

    user = get_user_by_id(
        user_id
    )

    if user is None:
        raise AuthenticationError(
            "The authenticated user "
            "no longer exists."
        )

    if int(
        user.get(
            "token_version",
            0,
        )
    ) != token_version:
        raise AuthenticationError(
            "This session is no longer valid. "
            "Please sign in again."
        )

    return user
