from __future__ import annotations

from .models import Capability, ModelCandidate


class CapabilityRegistry:
    def __init__(self) -> None:
        self._candidates: dict[str, ModelCandidate] = {}

    def register(self, candidate: ModelCandidate) -> None:
        self._candidates[candidate.id] = candidate

    def unregister(self, candidate_id: str) -> None:
        self._candidates.pop(candidate_id, None)

    def all(self) -> list[ModelCandidate]:
        return list(self._candidates.values())

    def for_capabilities(self, capabilities: set[Capability]) -> list[ModelCandidate]:
        return [c for c in self._candidates.values() if capabilities.issubset(c.capabilities)]
