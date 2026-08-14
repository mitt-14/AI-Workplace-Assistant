import re
import unicodedata

from app.core.exceptions import PasswordPolicyError


_MIN_LENGTH = 12
_MAX_LENGTH = 128

_COMMON_PASSWORDS = {
    "123456789012",
    "admin123456!",
    "changeme123!",
    "letmein12345!",
    "password123!",
    "password1234!",
    "password@123",
    "qwerty12345!",
    "welcome12345!",
    "welcome@123",
}

_KEYBOARD_OR_SEQUENCE_PATTERNS = (
    "1234",
    "4321",
    "abcd",
    "dcba",
    "qwerty",
    "asdf",
    "zxcv",
)


def _normalize_identity(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(
        character.casefold()
        for character in normalized
        if character.isalnum()
    )


def _identity_tokens(
    name: str | None,
    email: str | None,
) -> set[str]:
    """
    Build meaningful identity fragments.

    We deliberately do NOT ban every individual letter in a person's name.
    That would make strong passwords impractical. Instead, full name/email
    tokens and consecutive four-character identity fragments are rejected.
    """

    raw_tokens: list[str] = []

    if name:
        raw_tokens.extend(
            re.findall(
                r"[A-Za-zÀ-ÖØ-öø-ÿ0-9]+",
                name,
            )
        )

    if email and "@" in email:
        local_part = email.split("@", 1)[0]
        raw_tokens.extend(
            part
            for part in re.split(
                r"[._+\-]+",
                local_part,
            )
            if part
        )

    fragments: set[str] = set()

    for token in raw_tokens:
        normalized = _normalize_identity(token)

        if len(normalized) < 3:
            continue

        fragments.add(normalized)

        # Reject meaningful consecutive fragments such as "mite" from
        # "Miten" or "gaba" from "Gabani", without banning single letters.
        if len(normalized) >= 4:
            for index in range(
                len(normalized) - 3
            ):
                fragments.add(
                    normalized[index:index + 4]
                )

    return fragments


def password_policy_checks(
    password: str,
    *,
    name: str | None = None,
    email: str | None = None,
) -> dict[str, bool]:
    normalized_password = _normalize_identity(
        password
    )

    identity_fragments = _identity_tokens(
        name,
        email,
    )

    contains_identity = any(
        fragment in normalized_password
        for fragment in identity_fragments
    )

    lowered = password.casefold()

    return {
        "minimum_length": len(password) >= _MIN_LENGTH,
        "maximum_length": len(password) <= _MAX_LENGTH,
        "uppercase": bool(
            re.search(r"[A-Z]", password)
        ),
        "lowercase": bool(
            re.search(r"[a-z]", password)
        ),
        "number": bool(
            re.search(r"\d", password)
        ),
        "special_character": bool(
            re.search(r"[^A-Za-z0-9\s]", password)
        ),
        "no_whitespace": not bool(
            re.search(r"\s", password)
        ),
        "no_identity_fragment": (
            not contains_identity
        ),
        "not_common": (
            lowered not in _COMMON_PASSWORDS
        ),
        "no_obvious_sequence": not any(
            pattern in lowered
            for pattern
            in _KEYBOARD_OR_SEQUENCE_PATTERNS
        ),
        "no_repeated_character_run": (
            re.search(
                r"(.)\1{3,}",
                lowered,
            )
            is None
        ),
    }


def validate_password_policy(
    password: str,
    *,
    name: str | None = None,
    email: str | None = None,
) -> None:
    checks = password_policy_checks(
        password,
        name=name,
        email=email,
    )

    messages = {
        "minimum_length": (
            "Password must contain at least "
            f"{_MIN_LENGTH} characters."
        ),
        "maximum_length": (
            "Password must contain no more than "
            f"{_MAX_LENGTH} characters."
        ),
        "uppercase": (
            "Password must contain an uppercase letter."
        ),
        "lowercase": (
            "Password must contain a lowercase letter."
        ),
        "number": (
            "Password must contain a number."
        ),
        "special_character": (
            "Password must contain a special character."
        ),
        "no_whitespace": (
            "Password must not contain whitespace."
        ),
        "no_identity_fragment": (
            "Password must not contain your name, "
            "email username, or a meaningful fragment "
            "of either."
        ),
        "not_common": (
            "This password is too common."
        ),
        "no_obvious_sequence": (
            "Password must not contain an obvious "
            "keyboard or number sequence."
        ),
        "no_repeated_character_run": (
            "Password must not contain four or more "
            "identical characters in a row."
        ),
    }

    failures = [
        messages[key]
        for key, passed in checks.items()
        if not passed
    ]

    if failures:
        raise PasswordPolicyError(
            " ".join(failures)
        )
