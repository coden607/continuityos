from __future__ import annotations

from typing import Any, Protocol
import json
import sqlite3
from pathlib import Path

from pydantic import BaseModel


class MemoryRecord(BaseModel):
    namespace: str
    key: str
    value: Any
    metadata: dict[str, Any] = {}


class MemoryAdapter(Protocol):
    def put(self, record: MemoryRecord) -> None: ...
    def get(self, namespace: str, key: str) -> MemoryRecord | None: ...
    def search(self, namespace: str, query: str, limit: int = 10) -> list[MemoryRecord]: ...


class InMemoryMemoryAdapter:
    def __init__(self) -> None:
        self._records: dict[tuple[str, str], MemoryRecord] = {}

    def put(self, record: MemoryRecord) -> None:
        self._records[(record.namespace, record.key)] = record

    def get(self, namespace: str, key: str) -> MemoryRecord | None:
        return self._records.get((namespace, key))

    def search(self, namespace: str, query: str, limit: int = 10) -> list[MemoryRecord]:
        needle = query.lower()
        matches = [
            record for (ns, _), record in self._records.items()
            if ns == namespace and needle in str(record.value).lower()
        ]
        return matches[:limit]


class SQLiteMemoryAdapter:
    """Zero-cost persistent memory backend with namespace isolation."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS memory (namespace TEXT NOT NULL, key TEXT NOT NULL, value TEXT NOT NULL, metadata TEXT NOT NULL, PRIMARY KEY(namespace,key))"
            )

    def put(self, record: MemoryRecord) -> None:
        with sqlite3.connect(self.path) as db:
            db.execute(
                "INSERT INTO memory(namespace,key,value,metadata) VALUES (?,?,?,?) ON CONFLICT(namespace,key) DO UPDATE SET value=excluded.value, metadata=excluded.metadata",
                (record.namespace, record.key, json.dumps(record.value), json.dumps(record.metadata)),
            )

    def get(self, namespace: str, key: str) -> MemoryRecord | None:
        with sqlite3.connect(self.path) as db:
            row = db.execute("SELECT value,metadata FROM memory WHERE namespace=? AND key=?", (namespace, key)).fetchone()
        if row is None:
            return None
        return MemoryRecord(namespace=namespace, key=key, value=json.loads(row[0]), metadata=json.loads(row[1]))

    def search(self, namespace: str, query: str, limit: int = 10) -> list[MemoryRecord]:
        needle = f"%{query.lower()}%"
        with sqlite3.connect(self.path) as db:
            rows = db.execute(
                "SELECT key,value,metadata FROM memory WHERE namespace=? AND lower(value) LIKE ? ORDER BY key LIMIT ?",
                (namespace, needle, limit),
            ).fetchall()
        return [MemoryRecord(namespace=namespace, key=row[0], value=json.loads(row[1]), metadata=json.loads(row[2])) for row in rows]
