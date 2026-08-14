from functools import lru_cache
from pathlib import Path

from app.core.config import settings
from app.core.exceptions import (
    DisposableEmailNotAllowedError,
    EmailDomainNotAllowedError,
)


@lru_cache(maxsize=1)
def _disposable_domains() -> frozenset[str]:
    path = Path(__file__).with_name(
        "disposable_domains.txt"
    )

    domains: set[str] = set()

    if path.exists():
        for line in path.read_text(
            encoding="utf-8"
        ).splitlines():
            cleaned = line.strip().casefold()

            if (
                cleaned
                and not cleaned.startswith("#")
            ):
                domains.add(cleaned)

    return frozenset(domains)


def _configured_allowed_domains() -> set[str]:
    return {
        item.strip().casefold().strip(".")
        for item in (
            settings.allowed_email_domains
            or ""
        ).split(",")
        if item.strip()
    }


def _domain_matches(
    domain: str,
    candidate: str,
) -> bool:
    return (
        domain == candidate
        or domain.endswith(
            f".{candidate}"
        )
    )


def validate_registration_email(
    email: str,
) -> str:
    normalized = email.strip().casefold()

    if "@" not in normalized:
        raise EmailDomainNotAllowedError()

    domain = normalized.rsplit(
        "@",
        1,
    )[1].strip(".")

    mode = (
        settings.email_domain_mode
        .strip()
        .casefold()
    )

    if settings.block_disposable_emails:
        if any(
            _domain_matches(
                domain,
                disposable,
            )
            for disposable
            in _disposable_domains()
        ):
            raise DisposableEmailNotAllowedError()

    if mode == "allowlist":
        allowed = _configured_allowed_domains()

        if not allowed:
            raise EmailDomainNotAllowedError(
                "Email registration is restricted, "
                "but no allowed domains are configured."
            )

        if not any(
            _domain_matches(
                domain,
                candidate,
            )
            for candidate in allowed
        ):
            raise EmailDomainNotAllowedError()

    elif mode not in {
        "deny_disposable",
        "any",
    }:
        raise EmailDomainNotAllowedError(
            "The server email-domain policy "
            "is configured incorrectly."
        )

    return normalized
