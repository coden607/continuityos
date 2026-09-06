from __future__ import annotations

from contextlib import contextmanager
from time import perf_counter
from typing import Any, Iterator, Protocol


class Tracer(Protocol):
    @contextmanager
    def span(self, name: str, attributes: dict[str, Any] | None = None) -> Iterator[None]: ...


class InMemoryTracer:
    def __init__(self) -> None:
        self.spans: list[dict[str, Any]] = []

    @contextmanager
    def span(self, name: str, attributes: dict[str, Any] | None = None) -> Iterator[None]:
        started = perf_counter()
        span = {"name": name, "attributes": attributes or {}, "status": "ok", "duration_ms": 0.0}
        try:
            yield
        except Exception:
            span["status"] = "error"
            raise
        finally:
            span["duration_ms"] = round((perf_counter() - started) * 1000, 3)
            self.spans.append(span)
