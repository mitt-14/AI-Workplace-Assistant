import json
import logging
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)

_database_lock = threading.Lock()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_database_path() -> Path:
    path = Path(settings.conversation_database_path)

    if not path.is_absolute():
        backend_root = Path(__file__).resolve().parents[2]
        path = backend_root / path

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    return path


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(
        get_database_path(),
        check_same_thread=False,
    )

    connection.row_factory = sqlite3.Row

    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

    return connection


def initialize_conversation_database() -> None:
    """
    Create conversation and message tables when they do not exist.
    """

    with _database_lock:
        with get_connection() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS conversations (
                    conversation_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS conversation_messages (
                    message_id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL CHECK (
                        role IN ('user', 'assistant')
                    ),
                    content TEXT NOT NULL,
                    provider TEXT,
                    sources_json TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (conversation_id)
                        REFERENCES conversations(conversation_id)
                        ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS
                    idx_messages_conversation_created
                ON conversation_messages(
                    conversation_id,
                    created_at
                );
                """
            )

    logger.info(
        "Conversation database initialized: path=%s",
        get_database_path(),
    )


def create_conversation(
    title: str | None = None,
) -> dict[str, Any]:
    conversation_id = str(uuid.uuid4())
    timestamp = utc_now()

    conversation_title = (
        title.strip()
        if title and title.strip()
        else "New conversation"
    )

    with _database_lock:
        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO conversations (
                    conversation_id,
                    title,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    conversation_id,
                    conversation_title,
                    timestamp,
                    timestamp,
                ),
            )

    return {
        "conversation_id": conversation_id,
        "title": conversation_title,
        "created_at": timestamp,
        "updated_at": timestamp,
        "message_count": 0,
    }


def get_conversation(
    conversation_id: str,
) -> dict[str, Any] | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT
                c.conversation_id,
                c.title,
                c.created_at,
                c.updated_at,
                COUNT(m.message_id) AS message_count
            FROM conversations c
            LEFT JOIN conversation_messages m
                ON m.conversation_id = c.conversation_id
            WHERE c.conversation_id = ?
            GROUP BY
                c.conversation_id,
                c.title,
                c.created_at,
                c.updated_at
            """,
            (conversation_id,),
        ).fetchone()

    return dict(row) if row else None


def list_conversations() -> list[dict[str, Any]]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                c.conversation_id,
                c.title,
                c.created_at,
                c.updated_at,
                COUNT(m.message_id) AS message_count
            FROM conversations c
            LEFT JOIN conversation_messages m
                ON m.conversation_id = c.conversation_id
            GROUP BY
                c.conversation_id,
                c.title,
                c.created_at,
                c.updated_at
            ORDER BY c.updated_at DESC
            """
        ).fetchall()

    return [
        dict(row)
        for row in rows
    ]


def add_message(
    *,
    conversation_id: str,
    role: str,
    content: str,
    provider: str | None = None,
    sources: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    message_id = str(uuid.uuid4())
    timestamp = utc_now()

    sources_json = json.dumps(
        sources or [],
        ensure_ascii=False,
    )

    with _database_lock:
        with get_connection() as connection:
            conversation = connection.execute(
                """
                SELECT conversation_id
                FROM conversations
                WHERE conversation_id = ?
                """,
                (conversation_id,),
            ).fetchone()

            if conversation is None:
                raise ValueError(
                    f"Conversation not found: {conversation_id}"
                )

            connection.execute(
                """
                INSERT INTO conversation_messages (
                    message_id,
                    conversation_id,
                    role,
                    content,
                    provider,
                    sources_json,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    message_id,
                    conversation_id,
                    role,
                    content,
                    provider,
                    sources_json,
                    timestamp,
                ),
            )

            connection.execute(
                """
                UPDATE conversations
                SET updated_at = ?
                WHERE conversation_id = ?
                """,
                (
                    timestamp,
                    conversation_id,
                ),
            )

    return {
        "message_id": message_id,
        "conversation_id": conversation_id,
        "role": role,
        "content": content,
        "provider": provider,
        "created_at": timestamp,
    }


def get_messages(
    conversation_id: str,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    query = """
        SELECT
            message_id,
            conversation_id,
            role,
            content,
            provider,
            sources_json,
            created_at
        FROM conversation_messages
        WHERE conversation_id = ?
        ORDER BY created_at DESC
    """

    parameters: list[Any] = [
        conversation_id
    ]

    if limit is not None:
        query += " LIMIT ?"
        parameters.append(limit)

    with get_connection() as connection:
        rows = connection.execute(
            query,
            parameters,
        ).fetchall()

    messages = [
        {
            **dict(row),
            "sources": json.loads(
                row["sources_json"] or "[]"
            ),
        }
        for row in rows
    ]

    messages.reverse()

    return messages


def delete_conversation(
    conversation_id: str,
) -> bool:
    with _database_lock:
        with get_connection() as connection:
            cursor = connection.execute(
                """
                DELETE FROM conversations
                WHERE conversation_id = ?
                """,
                (conversation_id,),
            )

    return cursor.rowcount > 0