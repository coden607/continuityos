from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AppSection(StrictModel):
    name: str
    domain: str = "general"
    version: str = "0.1.0"
    profile: Literal["minimal", "ai", "full"] = "minimal"


class DevelopmentSection(StrictModel):
    method: str = "continuity-hybrid"
    roles: list[str] = Field(default_factory=list)
    architecture_gate: bool = True
    security_gate: bool = True
    eval_gate: bool = True


class QualitySection(StrictModel):
    min_quality: float = Field(default=.9, ge=0, le=1)
    min_reliability: float = Field(default=.9, ge=0, le=1)
    prefer_zero_token: bool = True
    escalation: list[str] = Field(default_factory=lambda: [
        "deterministic", "local_free", "economical", "premium", "council"
    ])


class VerificationSection(StrictModel):
    gates: list[str] = Field(default_factory=lambda: ["compile", "tests"])
    commands: dict[str, str] = Field(default_factory=dict)
    performance_budgets: dict[str, float] = Field(default_factory=lambda: {"lcp_ms": 2500.0, "cls": 0.1, "inp_ms": 200.0})


class FeaturesSection(StrictModel):
    pwa: bool = True
    api: bool = True
    voice: bool = False
    memory: bool = True


class DeploymentSection(StrictModel):
    targets: list[str] = Field(default_factory=lambda: ["github"])
    secrets: list[str] = Field(default_factory=list)


class AppBlueprint(StrictModel):
    app: AppSection
    development: DevelopmentSection = Field(default_factory=DevelopmentSection)
    quality: QualitySection = Field(default_factory=QualitySection)
    verification: VerificationSection = Field(default_factory=VerificationSection)
    features: FeaturesSection = Field(default_factory=FeaturesSection)
    deployment: DeploymentSection = Field(default_factory=DeploymentSection)


def load_blueprint(path: str | Path) -> AppBlueprint:
    with Path(path).open("rb") as handle:
        return AppBlueprint.model_validate(tomllib.load(handle))
