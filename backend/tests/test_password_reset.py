from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.core import user_store
from app.core.config import settings
from app.main import app


def test_password_reset_is_delivered_by_email_only(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        settings,
        "user_database_path",
        str(
            tmp_path / "users.db"
        ),
    )

    monkeypatch.setattr(
        settings,
        "jwt_secret_key",
        "test-secret-for-password-reset",
    )

    monkeypatch.setattr(
        settings,
        "password_reset_cooldown_seconds",
        0,
    )

    monkeypatch.setattr(
        settings,
        "password_reset_frontend_url",
        "http://localhost:8080",
    )

    user_store.initialize_user_database()

    with TestClient(app) as client:
        registration = client.post(
            "/api/auth/register",
            json={
                "name": "Security User",
                "email": "security@example.com",
                "password": "Orbit#Falcon82!River",
            },
        )

        assert registration.status_code == 201

        old_token = (
            registration.json()[
                "access_token"
            ]
        )

        captured: dict[str, str] = {}

        def fake_send_reset_email(
            *,
            recipient: str,
            reset_url: str,
        ) -> None:
            captured["recipient"] = recipient
            captured["reset_url"] = reset_url

        with patch(
            "app.services.password_reset_service._send_reset_email",
            side_effect=fake_send_reset_email,
        ):
            forgot = client.post(
                "/api/auth/forgot-password",
                json={
                    "email": "security@example.com",
                },
            )

        assert forgot.status_code == 200

        forgot_payload = forgot.json()

        assert list(
            forgot_payload.keys()
        ) == ["message"]

        assert "reset_token" not in forgot_payload
        assert "reset_url" not in forgot_payload

        assert (
            captured["recipient"]
            == "security@example.com"
        )

        assert (
            "reset_token="
            in captured["reset_url"]
        )

        reset_token = (
            captured["reset_url"]
            .split(
                "reset_token=",
                1,
            )[1]
        )

        reset = client.post(
            "/api/auth/reset-password",
            json={
                "token": reset_token,
                "new_password": "Nova#Cipher97!Cloud",
            },
        )

        assert reset.status_code == 200

        old_login = client.post(
            "/api/auth/login",
            json={
                "email": "security@example.com",
                "password": "Orbit#Falcon82!River",
            },
        )

        assert old_login.status_code == 401

        new_login = client.post(
            "/api/auth/login",
            json={
                "email": "security@example.com",
                "password": "Nova#Cipher97!Cloud",
            },
        )

        assert new_login.status_code == 200

        # Password reset invalidates JWTs issued before reset.
        old_session = client.get(
            "/api/auth/me",
            headers={
                "Authorization": (
                    f"Bearer {old_token}"
                )
            },
        )

        assert old_session.status_code == 401

        # Token is single-use.
        reuse = client.post(
            "/api/auth/reset-password",
            json={
                "token": reset_token,
                "new_password": "Another#Cipher71!Sky",
            },
        )

        assert reuse.status_code == 400


def test_unknown_account_has_same_public_response(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        settings,
        "user_database_path",
        str(
            tmp_path / "users.db"
        ),
    )

    user_store.initialize_user_database()

    with TestClient(app) as client:
        response = client.post(
            "/api/auth/forgot-password",
            json={
                "email": "missing@example.com",
            },
        )

    assert response.status_code == 200

    assert list(
        response.json().keys()
    ) == ["message"]

    assert (
        "If an account exists"
        in response.json()["message"]
    )
