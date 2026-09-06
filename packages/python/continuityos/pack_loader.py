from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class PackManifest(BaseModel):
    name: str
    version: str = "0.1.0"
    display_name: str | None = None
    template: str | None = None
    skills: list[str] = Field(default_factory=list)
    mcp: list[Any] = Field(default_factory=list)
    agents: list[str] = Field(default_factory=list)
    guardrails: list[str] = Field(default_factory=list)
    knowledge: list[str] = Field(default_factory=list)


class PackLoader:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    def discover(self) -> list[PackManifest]:
        if not self.root.exists():
            return []
        manifests: list[PackManifest] = []
        for path in sorted(self.root.glob("*/pack.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            if "name" not in data and isinstance(data.get("app"), dict):
                app = data["app"]
                data = dict(data)
                data["name"] = path.parent.name
                data.setdefault("display_name", app.get("name"))
                data.setdefault("template", app.get("mode"))
            manifests.append(PackManifest.model_validate(data))
        return manifests

    def get(self, name: str) -> PackManifest:
        for pack in self.discover():
            if pack.name == name:
                return pack
        raise LookupError(name)
