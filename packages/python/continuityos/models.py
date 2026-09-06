from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class Capability(str, Enum):
    TEXT = "text"
    REASONING = "reasoning"
    VISION = "vision"
    SPEECH_TO_TEXT = "speech_to_text"
    TEXT_TO_SPEECH = "text_to_speech"
    REALTIME_VOICE = "realtime_voice"
    EMBEDDING = "embedding"
    RERANK = "rerank"
    BROWSER = "browser"
    MCP = "mcp"


class ContinuityAction(str, Enum):
    NORMAL = "normal"
    COMPRESS = "compress"
    CHECKPOINT = "checkpoint"
    HANDOFF = "handoff"
    EMERGENCY = "emergency"


class ContextBudget(BaseModel):
    limit: int = Field(gt=0)
    used: int = Field(ge=0)
    reserve: int = Field(ge=0, default=0)

    @property
    def pressure(self) -> float:
        return min(1.0, (self.used + self.reserve) / self.limit)


class ContextCapsule(BaseModel):
    objective: str
    current_task: str
    user_requirements: list[str]
    hard_constraints: list[str]
    decisions: list[str]
    completed_work: list[str]
    open_work: list[str]
    facts: list[str]
    artifacts: list[str]
    tool_state: list[dict[str, Any]]
    citations: list[str]
    memory_refs: list[str]
    failed_approaches: list[str]
    current_plan: list[str]
    next_action: str
    handoff_reason: str


class ModelCandidate(BaseModel):
    id: str
    provider: str = "local"
    model: str | None = None
    capabilities: set[Capability]
    context_window: int = Field(gt=0)
    quality: float = Field(ge=0, le=1)
    reliability: float = Field(ge=0, le=1)
    cost_per_million: float = Field(ge=0)
    latency_ms: int = Field(ge=0)
    privacy: Literal["local", "private_cloud", "cloud"] = "cloud"
    max_output_tokens: int = Field(gt=0, default=4096)


class TaskRequirements(BaseModel):
    capabilities: set[Capability]
    context_needed: int = Field(ge=0, default=0)
    privacy: Literal["local", "private_cloud", "cloud", "any"] = "any"
    max_cost_per_million: float | None = Field(default=None, ge=0)
    prefer_low_latency: bool = False
    prefer_quality: bool = False
    task_type: str = "general"


class RouteDecision(BaseModel):
    candidate: ModelCandidate
    score: float
    reasons: list[str]


class GuardrailDecision(BaseModel):
    allowed: bool
    reasons: list[str] = []
    requires_human_approval: bool = False


class AgentMessage(BaseModel):
    sender: str
    recipient: str
    task_id: str
    type: str
    payload: dict[str, Any]
    provenance: list[str] = []
