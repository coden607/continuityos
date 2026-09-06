from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator


class OpenTelemetryTracer:
    def __init__(self, tracer: Any) -> None:
        self.tracer = tracer

    @contextmanager
    def span(self, name: str, attributes: dict[str, Any] | None = None) -> Iterator[None]:
        with self.tracer.start_as_current_span(name) as span:
            for key, value in (attributes or {}).items():
                span.set_attribute(key, value)
            yield


class LangfuseTracer:
    """Minimal adapter over an injected Langfuse client, avoiding SDK version lock-in."""

    def __init__(self, client: Any) -> None:
        self.client = client

    @contextmanager
    def span(self, name: str, attributes: dict[str, Any] | None = None) -> Iterator[None]:
        span = self.client.start_span(name=name, metadata=attributes or {})
        try:
            yield
        except Exception as exc:
            if hasattr(span, "update"):
                span.update(status_message=str(exc), level="ERROR")
            raise
        finally:
            if hasattr(span, "end"):
                span.end()
