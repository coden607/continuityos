from __future__ import annotations

from typing import Any, Protocol


class RealtimeVoiceSession(Protocol):
    async def send_audio(self, chunk: bytes) -> None: ...
    async def receive(self) -> Any: ...
    async def interrupt(self) -> None: ...
    async def close(self) -> None: ...


class RealtimeVoiceProvider(Protocol):
    name: str
    def available(self) -> bool: ...
    async def connect(self, **kwargs: Any) -> RealtimeVoiceSession: ...


class PipecatAdapter:
    """Injection-based Pipecat adapter so apps can provide their transport/pipeline without core coupling."""

    name = "pipecat"

    def __init__(self, session_factory: Any | None = None) -> None:
        self.session_factory = session_factory

    def available(self) -> bool:
        return self.session_factory is not None

    async def connect(self, **kwargs: Any) -> RealtimeVoiceSession:
        if self.session_factory is None:
            raise RuntimeError("Pipecat session factory is not configured")
        session = self.session_factory(**kwargs)
        return await session if hasattr(session, "__await__") else session


class AudioChunkStream:
    """Small async producer/consumer primitive for realtime audio pipelines."""

    def __init__(self) -> None:
        import asyncio
        self._queue: asyncio.Queue[bytes | None] = asyncio.Queue()
        self._closed = False

    async def push(self, chunk: bytes) -> None:
        if self._closed:
            raise RuntimeError("audio stream is closed")
        await self._queue.put(bytes(chunk))

    async def close(self) -> None:
        if not self._closed:
            self._closed = True
            await self._queue.put(None)

    def __aiter__(self):
        return self

    async def __anext__(self) -> bytes:
        item = await self._queue.get()
        if item is None:
            raise StopAsyncIteration
        return item
