import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator
from app.core.config import settings

def _path() -> Path:
    path = Path(settings.workflow_database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path

@contextmanager
def connection() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(str(_path()))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def initialize_workflow_database() -> None:
    with connection() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS workflow_executions (
          execution_id TEXT PRIMARY KEY, workflow_type TEXT NOT NULL, status TEXT NOT NULL,
          source_id TEXT, provider TEXT, analysis_json TEXT, error TEXT,
          started_at TEXT NOT NULL, completed_at TEXT
        );
        CREATE TABLE IF NOT EXISTS tasks (
          task_id TEXT PRIMARY KEY, title TEXT NOT NULL, description TEXT, owner TEXT, deadline TEXT,
          priority TEXT NOT NULL, status TEXT NOT NULL, source_type TEXT, source_id TEXT,
          workflow_execution_id TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS notifications (
          notification_id TEXT PRIMARY KEY, title TEXT NOT NULL, message TEXT NOT NULL, level TEXT NOT NULL,
          is_read INTEGER NOT NULL DEFAULT 0, workflow_execution_id TEXT, created_at TEXT NOT NULL
        );
        """)

def row_dict(row: sqlite3.Row) -> dict[str, Any]:
    return dict(row)

def encode_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, default=str)
