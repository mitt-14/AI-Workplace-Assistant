import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.core.config import settings


def _database_path() -> Path:
    path = Path(
        settings.user_database_path
    )
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    return path


def _connect() -> sqlite3.Connection:
    connection = sqlite3.connect(
        _database_path()
    )
    connection.row_factory = sqlite3.Row
    return connection


def _ensure_column(
    connection: sqlite3.Connection,
    table: str,
    column: str,
    declaration: str,
) -> None:
    columns = {
        row["name"]
        for row in connection.execute(
            f"PRAGMA table_info({table})"
        ).fetchall()
    }

    if column not in columns:
        connection.execute(
            f"ALTER TABLE {table} "
            f"ADD COLUMN {column} {declaration}"
        )


def initialize_user_database() -> None:
    with _connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL
                    UNIQUE COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL,
                token_version INTEGER NOT NULL DEFAULT 0,
                password_changed_at TEXT
            )
            """
        )

        _ensure_column(
            connection,
            "users",
            "token_version",
            "INTEGER NOT NULL DEFAULT 0",
        )

        _ensure_column(
            connection,
            "users",
            "password_changed_at",
            "TEXT",
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS
            password_reset_tokens (
                token_hash TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                used_at TEXT,
                FOREIGN KEY(user_id)
                    REFERENCES users(user_id)
                    ON DELETE CASCADE
            )
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_password_reset_user
            ON password_reset_tokens(user_id)
            """
        )

        connection.commit()


def create_user(
    *,
    name: str,
    email: str,
    password_hash: str,
) -> dict:
    user_id = str(
        uuid.uuid4()
    )
    created_at = datetime.now(
        timezone.utc
    ).isoformat()

    normalized_email = (
        email.strip().lower()
    )

    with _connect() as connection:
        connection.execute(
            """
            INSERT INTO users (
                user_id,
                name,
                email,
                password_hash,
                created_at,
                token_version
            )
            VALUES (?, ?, ?, ?, ?, 0)
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
        "token_version": 0,
    }


def get_user_by_email(
    email: str,
) -> dict | None:
    with _connect() as connection:
        row = connection.execute(
            """
            SELECT
                user_id,
                name,
                email,
                password_hash,
                created_at,
                token_version,
                password_changed_at
            FROM users
            WHERE email = ? COLLATE NOCASE
            """,
            (
                email.strip().lower(),
            ),
        ).fetchone()

    return (
        dict(row)
        if row
        else None
    )


def get_user_by_id(
    user_id: str,
) -> dict | None:
    with _connect() as connection:
        row = connection.execute(
            """
            SELECT
                user_id,
                name,
                email,
                created_at,
                token_version,
                password_changed_at
            FROM users
            WHERE user_id = ?
            """,
            (user_id,),
        ).fetchone()

    return (
        dict(row)
        if row
        else None
    )


def invalidate_password_reset_tokens(
    user_id: str,
) -> None:
    now = datetime.now(
        timezone.utc
    ).isoformat()

    with _connect() as connection:
        connection.execute(
            """
            UPDATE password_reset_tokens
            SET used_at = ?
            WHERE user_id = ?
              AND used_at IS NULL
            """,
            (
                now,
                user_id,
            ),
        )
        connection.commit()


def create_password_reset_token(
    *,
    user_id: str,
    token_hash: str,
    created_at: datetime,
    expires_at: datetime,
) -> None:
    with _connect() as connection:
        connection.execute(
            """
            INSERT INTO password_reset_tokens (
                token_hash,
                user_id,
                created_at,
                expires_at,
                used_at
            )
            VALUES (?, ?, ?, ?, NULL)
            """,
            (
                token_hash,
                user_id,
                created_at.isoformat(),
                expires_at.isoformat(),
            ),
        )
        connection.commit()


def latest_password_reset_created_at(
    user_id: str,
) -> datetime | None:
    with _connect() as connection:
        row = connection.execute(
            """
            SELECT created_at
            FROM password_reset_tokens
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (user_id,),
        ).fetchone()

    if not row:
        return None

    return datetime.fromisoformat(
        row["created_at"]
    )


def get_password_reset_context(
    token_hash: str,
) -> dict | None:
    with _connect() as connection:
        row = connection.execute(
            """
            SELECT
                prt.token_hash,
                prt.user_id,
                prt.expires_at,
                prt.used_at,
                u.name,
                u.email,
                u.token_version
            FROM password_reset_tokens prt
            JOIN users u
              ON u.user_id = prt.user_id
            WHERE prt.token_hash = ?
            """,
            (token_hash,),
        ).fetchone()

    return (
        dict(row)
        if row
        else None
    )


def reset_password_with_token(
    *,
    token_hash: str,
    password_hash: str,
) -> bool:
    now = datetime.now(
        timezone.utc
    )
    now_text = now.isoformat()

    with _connect() as connection:
        connection.execute(
            "BEGIN IMMEDIATE"
        )

        row = connection.execute(
            """
            SELECT
                user_id,
                expires_at,
                used_at
            FROM password_reset_tokens
            WHERE token_hash = ?
            """,
            (token_hash,),
        ).fetchone()

        if not row:
            connection.rollback()
            return False

        expires_at = datetime.fromisoformat(
            row["expires_at"]
        )

        if (
            row["used_at"] is not None
            or expires_at <= now
        ):
            connection.rollback()
            return False

        user_id = row["user_id"]

        connection.execute(
            """
            UPDATE users
            SET password_hash = ?,
                password_changed_at = ?,
                token_version =
                    COALESCE(token_version, 0) + 1
            WHERE user_id = ?
            """,
            (
                password_hash,
                now_text,
                user_id,
            ),
        )

        connection.execute(
            """
            UPDATE password_reset_tokens
            SET used_at = ?
            WHERE user_id = ?
              AND used_at IS NULL
            """,
            (
                now_text,
                user_id,
            ),
        )

        connection.commit()

    return True
