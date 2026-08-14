import hashlib
import logging
import secrets
import smtplib
from datetime import (
    datetime,
    timedelta,
    timezone,
)
from email.message import EmailMessage
from urllib.parse import urlencode

from app.core.auth import hash_password
from app.core.config import settings
from app.core.exceptions import (
    InvalidPasswordResetTokenError,
)
from app.core.user_store import (
    create_password_reset_token,
    get_password_reset_context,
    get_user_by_email,
    invalidate_password_reset_tokens,
    latest_password_reset_created_at,
    reset_password_with_token,
)
from app.security.password_policy import (
    validate_password_policy,
)

logger = logging.getLogger(__name__)

_GENERIC_MESSAGE = (
    "If an account exists for that email, "
    "a password-reset link has been sent."
)


def _token_hash(token: str) -> str:
    return hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()


def _reset_url(token: str) -> str:
    base = (
        settings
        .password_reset_frontend_url
        .rstrip("/")
    )

    query = urlencode(
        {
            "reset_token": token,
        }
    )

    return f"{base}/?{query}"


def _send_reset_email(
    *,
    recipient: str,
    reset_url: str,
) -> None:
    """
    Deliver the reset token only through the user's email account.

    SMTP credentials live exclusively in the backend environment.
    The reset token is never returned to the browser by the
    forgot-password endpoint.
    """

    if not settings.smtp_host:
        raise RuntimeError(
            "SMTP_HOST is not configured."
        )

    if not settings.smtp_from_email:
        raise RuntimeError(
            "SMTP_FROM_EMAIL is not configured."
        )

    message = EmailMessage()

    message["Subject"] = (
        "Reset your AI Workplace password"
    )

    message["From"] = (
        settings.smtp_from_email
    )

    message["To"] = recipient

    message.set_content(
        "A password reset was requested for your "
        "AI Workplace account.\n\n"
        "Use the secure link below to choose a new password:\n\n"
        f"{reset_url}\n\n"
        "This link expires in "
        f"{settings.password_reset_expire_minutes} minutes "
        "and can be used only once.\n\n"
        "If you did not request a password reset, "
        "you can safely ignore this email."
    )

    with smtplib.SMTP(
        settings.smtp_host,
        settings.smtp_port,
        timeout=15,
    ) as smtp:
        smtp.ehlo()

        if settings.smtp_use_tls:
            smtp.starttls()
            smtp.ehlo()

        if (
            settings.smtp_username
            and settings.smtp_password
        ):
            smtp.login(
                settings.smtp_username,
                settings.smtp_password,
            )

        smtp.send_message(
            message
        )


def request_password_reset(
    email: str,
) -> dict[str, str]:
    """
    Create and email a reset token when the account exists.

    The public response is intentionally identical for existing and
    non-existing accounts so the endpoint cannot be used to enumerate
    registered email addresses.

    The raw token is never returned to the caller and is never logged.
    """

    normalized_email = (
        email.strip().casefold()
    )

    user = get_user_by_email(
        normalized_email
    )

    if user is None:
        return {
            "message": _GENERIC_MESSAGE,
        }

    now = datetime.now(
        timezone.utc
    )

    latest = (
        latest_password_reset_created_at(
            user["user_id"]
        )
    )

    cooldown = timedelta(
        seconds=max(
            0,
            settings
            .password_reset_cooldown_seconds,
        )
    )

    # Preserve the generic public response during cooldown.
    if (
        latest is not None
        and now - latest < cooldown
    ):
        return {
            "message": _GENERIC_MESSAGE,
        }

    raw_token = secrets.token_urlsafe(
        32
    )

    token_hash = _token_hash(
        raw_token
    )

    expires_at = now + timedelta(
        minutes=(
            settings
            .password_reset_expire_minutes
        )
    )

    # Only one live reset request per account.
    invalidate_password_reset_tokens(
        user["user_id"]
    )

    create_password_reset_token(
        user_id=user["user_id"],
        token_hash=token_hash,
        created_at=now,
        expires_at=expires_at,
    )

    try:
        _send_reset_email(
            recipient=user["email"],
            reset_url=_reset_url(
                raw_token
            ),
        )

    except Exception:
        # Do not leak account existence or SMTP details to the client.
        # Invalidate the token because delivery did not complete.
        invalidate_password_reset_tokens(
            user["user_id"]
        )

        logger.exception(
            "Password reset email delivery failed "
            "for user_id=%s",
            user["user_id"],
        )

    return {
        "message": _GENERIC_MESSAGE,
    }


def reset_password(
    *,
    token: str,
    new_password: str,
) -> None:
    token_hash = _token_hash(
        token
    )

    context = (
        get_password_reset_context(
            token_hash
        )
    )

    if context is None:
        raise InvalidPasswordResetTokenError()

    if context["used_at"] is not None:
        raise InvalidPasswordResetTokenError()

    expires_at = datetime.fromisoformat(
        context["expires_at"]
    )

    if expires_at <= datetime.now(
        timezone.utc
    ):
        raise InvalidPasswordResetTokenError()

    validate_password_policy(
        new_password,
        name=context["name"],
        email=context["email"],
    )

    changed = (
        reset_password_with_token(
            token_hash=token_hash,
            password_hash=hash_password(
                new_password
            ),
        )
    )

    if not changed:
        raise InvalidPasswordResetTokenError()
