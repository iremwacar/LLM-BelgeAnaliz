import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

DB_PATH = Path("storage") / "library.db"


class LibraryStore:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init()

    def _init(self):
        with self._lock:
            self._conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    original_name TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    status TEXT NOT NULL,
                    progress INTEGER NOT NULL DEFAULT 0,
                    current_step TEXT,
                    step_detail TEXT,
                    chunk_count INTEGER DEFAULT 0,
                    error_message TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    sources TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(document_id) REFERENCES documents(id)
                );
                """
            )
            self._conn.commit()

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def create_document(self, doc_id: str, original_name: str, file_path: str) -> dict:
        now = self._now()
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO documents (id, original_name, file_path, status, progress, current_step, step_detail, created_at, updated_at)
                VALUES (?, ?, ?, 'queued', 0, 'upload', 'Saving document', ?, ?)
                """,
                (doc_id, original_name, file_path, now, now),
            )
            self._conn.commit()
        return self.get_document(doc_id)

    def update_document(self, doc_id: str, **fields: Any):
        if not fields:
            return
        fields["updated_at"] = self._now()
        assignments = ", ".join(f"{key} = ?" for key in fields)
        values = list(fields.values()) + [doc_id]
        with self._lock:
            self._conn.execute(f"UPDATE documents SET {assignments} WHERE id = ?", values)
            self._conn.commit()

    def get_document(self, doc_id: str) -> Optional[dict]:
        with self._lock:
            row = self._conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
        return dict(row) if row else None

    def list_documents(self) -> list[dict]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM documents ORDER BY created_at DESC"
            ).fetchall()
        return [dict(row) for row in rows]

    def delete_document(self, doc_id: str):
        with self._lock:
            self._conn.execute("DELETE FROM messages WHERE document_id = ?", (doc_id,))
            self._conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
            self._conn.commit()

    def add_message(self, message_id: str, document_id: str, role: str, content: str, sources=None):
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO messages (id, document_id, role, content, sources, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    message_id,
                    document_id,
                    role,
                    content,
                    json.dumps(sources or [], ensure_ascii=False),
                    self._now(),
                ),
            )
            self._conn.commit()

    def list_messages(self, document_id: str) -> list[dict]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM messages WHERE document_id = ? ORDER BY created_at ASC",
                (document_id,),
            ).fetchall()
        messages = []
        for row in rows:
            item = dict(row)
            try:
                item["sources"] = json.loads(item["sources"] or "[]")
            except json.JSONDecodeError:
                item["sources"] = []
            messages.append(item)
        return messages
