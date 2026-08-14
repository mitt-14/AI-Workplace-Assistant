import pytest

from app.core.exceptions import (
    PasswordPolicyError,
)
from app.security.password_policy import (
    validate_password_policy,
)


def test_strong_password_is_allowed():
    validate_password_policy(
        "Orbit#Falcon82!River",
        name="Miten Gabani",
        email="miten.gabani@example.com",
    )


@pytest.mark.parametrize(
    "password",
    [
        "Miten#Falcon82!River",
        "SecureGaba#82!River",
        "miten.gabani#X82!River",
        "password123!",
        "NoSpecialCharacter82",
        "NOLOWERCASE#82!",
    ],
)
def test_weak_or_identity_password_is_rejected(
    password,
):
    with pytest.raises(
        PasswordPolicyError
    ):
        validate_password_policy(
            password,
            name="Miten Gabani",
            email=(
                "miten.gabani@example.com"
            ),
        )
