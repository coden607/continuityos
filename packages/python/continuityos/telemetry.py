from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from statistics import mean


@dataclass(frozen=True)
class RouteStats:
    attempts: int = 0
    successes: int = 0
    avg_latency_ms: float = 0.0
    avg_tokens: float = 0.0
    avg_cost: float = 0.0

    @property
    def success_rate(self) -> float:
        return self.successes / self.attempts if self.attempts else 0.5


class RoutingTelemetry:
    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path else None
        self._events: list[dict] = []
        if self.path and self.path.exists():
            for line in self.path.read_text().splitlines():
                if line.strip():
                    self._events.append(json.loads(line))

    def record(self, candidate_id: str, task_type: str, *, success: bool, latency_ms: int, tokens: int, cost: float) -> None:
        event = {
            "candidate_id": candidate_id,
            "task_type": task_type,
            "success": bool(success),
            "latency_ms": int(latency_ms),
            "tokens": int(tokens),
            "cost": float(cost),
        }
        self._events.append(event)
        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(event, separators=(",", ":")) + "\n")

    def stats(self, candidate_id: str, task_type: str | None = None) -> RouteStats:
        events = [e for e in self._events if e["candidate_id"] == candidate_id and (task_type is None or e["task_type"] == task_type)]
        if not events:
            return RouteStats()
        return RouteStats(
            attempts=len(events),
            successes=sum(1 for e in events if e["success"]),
            avg_latency_ms=mean(e["latency_ms"] for e in events),
            avg_tokens=mean(e["tokens"] for e in events),
            avg_cost=mean(e["cost"] for e in events),
        )
