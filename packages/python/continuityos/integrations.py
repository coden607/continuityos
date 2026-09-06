from __future__ import annotations

import importlib.util
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class IntegrationStatus:
    name: str
    module: str
    available: bool


_OPTIONAL = {
    "litellm": "litellm",
    "mem0": "mem0",
    "graphiti": "graphiti_core",
    "nemo_guardrails": "nemoguardrails",
    "dbos": "dbos",
    "opentelemetry": "opentelemetry",
    "langfuse": "langfuse",
    "pipecat": "pipecat",
}


def integration_statuses() -> list[IntegrationStatus]:
    return [IntegrationStatus(name, module, importlib.util.find_spec(module) is not None) for name, module in _OPTIONAL.items()]


class OptionalIntegration:
    def __init__(self, name: str) -> None:
        if name not in _OPTIONAL:
            raise KeyError(name)
        self.name = name
        self.module = _OPTIONAL[name]

    def available(self) -> bool:
        return importlib.util.find_spec(self.module) is not None

    def require(self) -> Any:
        if not self.available():
            raise RuntimeError(f"optional integration '{self.name}' is not installed")
        return __import__(self.module)
