import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.core.config import settings


def _database_path() -> Path:
    path = Path(settings.user_database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _connect() -> sqlite3.Connection:
    connection = sqlite3.connect(_database_path())
    connection.row_factory = sqlite3.Row
    return connection


def initialize_user_database() -> None:
    with _connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.commit()


def create_user(
    *,
    name: str,
    email: str,
    password_hash: str,
) -> dict:
    user_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()
    normalized_email = email.strip().lower()

    with _connect() as connection:
        connection.execute(
            """
            INSERT INTO users (
                user_id,
                name,
                email,
                password_hash,
                created_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                user_id,
                name.strip(),
                normalized_email,
                password_hash,
                created_at,
            ),
        )
        connection.commit()

    return {
        "user_id": user_id,
        "name": name.strip(),
        "email": normalized_email,
        "created_at": created_at,
    }


def get_user_by_email(email: str) -> dict | None:
    with _connect() as connection:
        row = connection.execute(
            """
            SELECT user_id, name, email, password_hash, created_at
            FROM users
            WHERE email = ? COLLATE NOCASE
            """,
            (email.strip().lower(),),
        ).fetchone()

    return dict(row) if row else None


def get_user_by_id(user_id: str) -> dict | None:
    with _connect() as connection:
        row = connection.execute(
            """
            SELECT user_id, name, email, created_at
            FROM users
            WHERE user_id = ?
            """,
            (user_id,),
        ).fetchone()

    return dict(row) if row else None
