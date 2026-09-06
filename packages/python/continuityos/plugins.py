from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from .models import Capability


class PluginManifest(BaseModel):
    name: str
    version: str
    capabilities: set[Capability]
    kind: Literal["mcp", "skill", "memory", "voice", "guardrail", "tool", "provider"]
    entrypoint: str | None = None
    requires: list[str] = []


class PluginRegistry:
    def __init__(self) -> None:
        self._plugins: dict[str, PluginManifest] = {}

    def register(self, manifest: PluginManifest) -> None:
        self._plugins[manifest.name] = manifest

    def resolve(self, capability: Capability) -> list[PluginManifest]:
        return [p for p in self._plugins.values() if capability in p.capabilities]

    def all(self) -> list[PluginManifest]:
        return list(self._plugins.values())
