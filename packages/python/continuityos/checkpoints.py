from __future__ import annotations

import sqlite3
from pathlib import Path

from .models import ContextCapsule


class CheckpointStore:
    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        self._init()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def _init(self) -> None:
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS checkpoints (task_id TEXT NOT NULL, version INTEGER NOT NULL, payload TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(task_id, version))"
            )

    def save(self, task_id: str, capsule: ContextCapsule) -> int:
        with self._connect() as db:
            row = db.execute("SELECT COALESCE(MAX(version), 0) FROM checkpoints WHERE task_id = ?", (task_id,)).fetchone()
            version = int(row[0]) + 1
            db.execute("INSERT INTO checkpoints(task_id, version, payload) VALUES (?, ?, ?)", (task_id, version, capsule.model_dump_json()))
            return version

    def latest(self, task_id: str) -> ContextCapsule | None:
        with self._connect() as db:
            row = db.execute("SELECT payload FROM checkpoints WHERE task_id = ? ORDER BY version DESC LIMIT 1", (task_id,)).fetchone()
        return ContextCapsule.model_validate_json(row[0]) if row else None
