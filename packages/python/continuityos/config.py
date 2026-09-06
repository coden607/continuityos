from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from .models import ModelCandidate


class AppConfig(BaseModel):
    name: str = "continuity-app"
    profile: Literal["minimal", "ai", "full"] = "minimal"


class RuntimeConfig(BaseModel):
    checkpoint_dir: str = ".continuity/checkpoints"
    telemetry_path: str = ".continuity/routes.jsonl"
    memory_path: str = ".continuity/memory.db"


class ContinuityConfig(BaseModel):
    app: AppConfig = Field(default_factory=AppConfig)
    runtime: RuntimeConfig = Field(default_factory=RuntimeConfig)
    models: list[ModelCandidate] = Field(default_factory=list)
    packs_dir: str = "packs"


def load_config(path: str | Path) -> ContinuityConfig:
    path = Path(path)
    with path.open("rb") as fh:
        data = tomllib.load(fh)
    return ContinuityConfig.model_validate(data)
