from pathlib import Path

from fastapi.testclient import TestClient

from app.core import user_store
from app.core.config import settings
from app.main import app


def test_register_login_and_me(tmp_path: Path, monkeypatch) -> None:
    database = tmp_path / "users.db"
    monkeypatch.setattr(
        settings,
        "user_database_path",
        str(database),
    )
    monkeypatch.setattr(
        settings,
        "jwt_secret_key",
        "test-secret-key-that-is-long-enough",
    )

    user_store.initialize_user_database()

    with TestClient(app) as client:
        register = client.post(
            "/api/auth/register",
            json={
                "name": "Test User",
                "email": "test@example.com",
                "password": "SecurePass123!",
            },
        )

        assert register.status_code == 201
        register_payload = register.json()
        assert register_payload["token_type"] == "bearer"
        assert register_payload["user"]["email"] == "test@example.com"

        duplicate = client.post(
            "/api/auth/register",
            json={
                "name": "Test User",
                "email": "test@example.com",
                "password": "SecurePass123!",
            },
        )
        assert duplicate.status_code == 409

        bad_login = client.post(
            "/api/auth/login",
            json={
                "email": "test@example.com",
                "password": "wrong-password",
            },
        )
        assert bad_login.status_code == 401

        login = client.post(
            "/api/auth/login",
            json={
                "email": "test@example.com",
                "password": "SecurePass123!",
            },
        )
        assert login.status_code == 200

        token = login.json()["access_token"]

        me = client.get(
            "/api/auth/me",
            headers={
                "Authorization": f"Bearer {token}",
            },
        )
        assert me.status_code == 200
        assert me.json()["name"] == "Test User"


def test_me_requires_authentication(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        settings,
        "user_database_path",
        str(tmp_path / "users.db"),
    )
    user_store.initialize_user_database()

    with TestClient(app) as client:
        response = client.get("/api/auth/me")

    assert response.status_code == 401
