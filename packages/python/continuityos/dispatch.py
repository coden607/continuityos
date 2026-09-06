from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

from .health import HealthRegistry
from .models import Capability, ModelCandidate
from .plugins import PluginManifest


class TargetKind(str, Enum):
    MODEL = "model"
    MCP = "mcp"
    SKILL = "skill"
    AGENT = "agent"
    TOOL = "tool"
    PROVIDER = "provider"
    MEMORY = "memory"
    VOICE = "voice"
    GUARDRAIL = "guardrail"


class DispatchTarget(BaseModel):
    id: str
    kind: TargetKind
    capabilities: set[Capability]
    quality: float = Field(default=.7, ge=0, le=1)
    reliability: float = Field(default=.95, ge=0, le=1)
    token_cost_per_million: float = Field(default=0, ge=0)
    latency_ms: int = Field(default=0, ge=0)
    privacy: Literal["local", "private_cloud", "cloud"] = "local"
    context_window: int | None = Field(default=None, gt=0)
    reference: str | None = None
    outputs: set[str] = Field(default_factory=set)
    languages: set[str] = Field(default_factory=set)
    frameworks: set[str] = Field(default_factory=set)
    verification: set[str] = Field(default_factory=set)

    @classmethod
    def from_model(cls, model: ModelCandidate) -> "DispatchTarget":
        return cls(
            id=model.id,
            kind=TargetKind.MODEL,
            capabilities=model.capabilities,
            quality=model.quality,
            reliability=model.reliability,
            token_cost_per_million=model.cost_per_million,
            latency_ms=model.latency_ms,
            privacy=model.privacy,
            context_window=model.context_window,
            reference=model.model or model.id,
        )

    @classmethod
    def from_plugin(
        cls,
        plugin: PluginManifest,
        *,
        quality: float = .7,
        reliability: float = .95,
        token_cost_per_million: float = 0,
        latency_ms: int = 0,
        privacy: Literal["local", "private_cloud", "cloud"] = "local",
    ) -> "DispatchTarget":
        return cls(
            id=plugin.name,
            kind=TargetKind(plugin.kind),
            capabilities=plugin.capabilities,
            quality=quality,
            reliability=reliability,
            token_cost_per_million=token_cost_per_million,
            latency_ms=latency_ms,
            privacy=privacy,
            reference=plugin.entrypoint,
        )


class DispatchRequirements(BaseModel):
    capabilities: set[Capability]
    target_kinds: set[TargetKind] | None = None
    privacy: Literal["local", "private_cloud", "cloud", "any"] = "any"
    context_needed: int = Field(default=0, ge=0)
    prefer_zero_token: bool = True
    prefer_low_latency: bool = False
    min_quality: float = Field(default=0, ge=0, le=1)
    min_reliability: float = Field(default=0, ge=0, le=1)
    required_outputs: set[str] = Field(default_factory=set)
    languages: set[str] = Field(default_factory=set)
    frameworks: set[str] = Field(default_factory=set)
    required_verification: set[str] = Field(default_factory=set)


class DispatchDecision(BaseModel):
    target: DispatchTarget
    score: float
    reasons: list[str]


_PRIVACY_RANK = {"local": 3, "private_cloud": 2, "cloud": 1}


class CapabilityDispatcher:
    """Routes work across models, skills, MCPs, agents and tools by capability and cost."""

    def __init__(self, targets: list[DispatchTarget], health: HealthRegistry) -> None:
        self.targets = list(targets)
        self.health = health

    def _eligible(self, target: DispatchTarget, req: DispatchRequirements) -> bool:
        if not req.capabilities.issubset(target.capabilities):
            return False
        if req.target_kinds is not None and target.kind not in req.target_kinds:
            return False
        if not self.health.routable(target.id):
            return False
        if req.privacy != "any" and _PRIVACY_RANK[target.privacy] < _PRIVACY_RANK[req.privacy]:
            return False
        if target.kind == TargetKind.MODEL and req.context_needed:
            if target.context_window is None or target.context_window < req.context_needed:
                return False
        if target.quality < req.min_quality or target.reliability < req.min_reliability:
            return False
        if not req.required_outputs.issubset(target.outputs):
            return False
        if not req.languages.issubset(target.languages):
            return False
        if not req.frameworks.issubset(target.frameworks):
            return False
        if not req.required_verification.issubset(target.verification):
            return False
        return True

    def _score(self, target: DispatchTarget, req: DispatchRequirements) -> tuple[float, list[str]]:
        score = target.quality * 35 + target.reliability * 30
        score += max(0.0, 20.0 - target.token_cost_per_million)
        score += max(0.0, 10.0 - min(target.latency_ms / 100.0, 10.0))
        score += {"local": 8.0, "private_cloud": 4.0, "cloud": 0.0}[target.privacy]
        reasons = ["capabilities satisfied"]
        if req.prefer_zero_token and target.token_cost_per_million == 0:
            score += 30
            if target.kind != TargetKind.MODEL:
                reasons.append("avoids model tokens")
            else:
                reasons.append("zero marginal token cost")
        if req.prefer_low_latency:
            score += max(0.0, 10.0 - min(target.latency_ms / 50.0, 10.0))
            reasons.append("latency preference")
        if target.privacy == "local":
            reasons.append("local privacy")
        return score, reasons

    def route(self, req: DispatchRequirements) -> DispatchDecision:
        eligible = [target for target in self.targets if self._eligible(target, req)]
        if not eligible:
            raise LookupError("no healthy target satisfies dispatch requirements")
        ranked = [(target, *self._score(target, req)) for target in eligible]
        target, score, reasons = max(ranked, key=lambda row: row[1])
        return DispatchDecision(target=target, score=round(score, 3), reasons=reasons)
