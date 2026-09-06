from __future__ import annotations

from typing import Any

from .memory import MemoryRecord


class Mem0Adapter:
    def __init__(self, client: Any) -> None:
        self.client = client

    def put(self, record: MemoryRecord) -> None:
        self.client.add(str(record.value), user_id=record.namespace, metadata={"key": record.key, **record.metadata})

    def get(self, namespace: str, key: str) -> MemoryRecord | None:
        results = self.search(namespace, key, limit=10)
        return next((r for r in results if r.key == key), None)

    def search(self, namespace: str, query: str, limit: int = 10) -> list[MemoryRecord]:
        raw = self.client.search(query, user_id=namespace, limit=limit)
        rows = raw.get("results", raw) if isinstance(raw, dict) else raw
        out: list[MemoryRecord] = []
        for item in rows or []:
            meta = dict(item.get("metadata") or {})
            key = str(meta.pop("key", item.get("id", "memory")))
            value = item.get("memory", item.get("text", ""))
            out.append(MemoryRecord(namespace=namespace, key=key, value=value, metadata=meta))
        return out


class GraphitiAdapter:
    """Thin adapter around an injected Graphiti client to avoid locking ContinuityOS to one backend constructor."""

    def __init__(self, client: Any) -> None:
        self.client = client

    async def add_episode(self, *, name: str, body: str, source_description: str = "ContinuityOS") -> Any:
        kwargs = {"name": name, "episode_body": body, "source_description": source_description}
        return await self.client.add_episode(**kwargs)

    async def search(self, query: str, limit: int = 10) -> Any:
        return await self.client.search(query, num_results=limit)
