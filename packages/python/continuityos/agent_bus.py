from __future__ import annotations

from collections import defaultdict, deque

from .models import AgentMessage


class AgentBus:
    def __init__(self) -> None:
        self._queues: dict[str, deque[AgentMessage]] = defaultdict(deque)

    def publish(self, message: AgentMessage) -> None:
        self._queues[message.recipient].append(message)

    def receive(self, recipient: str, limit: int = 100) -> list[AgentMessage]:
        queue = self._queues[recipient]
        out: list[AgentMessage] = []
        while queue and len(out) < limit:
            out.append(queue.popleft())
        return out

__all__ = ["AgentBus", "AgentMessage"]
