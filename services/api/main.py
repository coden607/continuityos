from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from continuityos import __version__
from continuityos.continuity import evaluate_context
from continuityos.council import CouncilDecision, CouncilVote, MultiModelCouncil
from continuityos.defaults import default_candidates
from continuityos.handoff import HandoffAcknowledgement, HandoffVerification, verify_handoff
from continuityos.health import HealthRegistry
from continuityos.integrations import integration_statuses
from continuityos.models import ContextBudget, ContextCapsule, RouteDecision, TaskRequirements
from continuityos.router import Router
from continuityos.dev_provider import DevEchoProvider
from continuityos.providers import ProviderFleet
from continuityos.runtime import ExecutionRequest, RuntimeOrchestrator
from continuityos.models import Capability, ModelCandidate
from continuityos.config import load_config
from continuityos.runtime_factory import build_runtime

api = FastAPI(title="ContinuityOS API", version=__version__)
api.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:4173", "http://localhost:4173"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Accept"],
)
health_registry = HealthRegistry()
router = Router(default_candidates(), health_registry)


class HandoffRequest(BaseModel):
    capsule: ContextCapsule
    acknowledgement: HandoffAcknowledgement


@api.get("/status/live")
def live() -> dict:
    return {"status": "alive"}


@api.get("/status/ready")
def ready() -> dict:
    return {"status": "ready"}


@api.get("/status/health")
def health() -> dict:
    return {"status": "healthy", "providers": health_registry.snapshot()}


@api.post("/route/preview", response_model=RouteDecision)
def route_preview(requirements: TaskRequirements) -> RouteDecision:
    try:
        return router.route(requirements)
    except LookupError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@api.post("/continuity/action")
def continuity_action(budget: ContextBudget) -> dict:
    return {"action": evaluate_context(budget).value, "pressure": budget.pressure}


@api.post("/continuity/handoff/verify", response_model=HandoffVerification)
def handoff_verify(request: HandoffRequest) -> HandoffVerification:
    return verify_handoff(request.capsule, request.acknowledgement)


@api.post("/council/decide", response_model=CouncilDecision)
def council_decide(votes: list[CouncilVote]) -> CouncilDecision:
    try:
        return MultiModelCouncil().decide(votes)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@api.get("/platform/capabilities")
def platform_capabilities() -> dict:
    return {
        "version": __version__,
        "features": [
            "routing", "continuity", "handoff-verification", "council", "checkpoints", "durable-workflows",
            "health", "self-healing", "guardrails", "voice", "tts", "realtime-voice", "memory", "mcp", "plugins", "observability", "secrets", "app-generator", "adaptive-routing", "context-compression"
        ],
        "optional_adapters": ["litellm", "whisper.cpp", "piper", "pipecat", "mem0", "graphiti", "nemo-guardrails", "opentelemetry", "langfuse", "dbos"],
    }


@api.get("/platform/integrations")
def platform_integrations() -> dict:
    return {"integrations": [item.__dict__ for item in integration_statuses()]}


class ExecuteAPIRequest(BaseModel):
    task_id: str
    prompt: str
    capability: str = "text"


def _api_runtime(capability: Capability) -> RuntimeOrchestrator:
    configured = os.environ.get("CONTINUITY_CONFIG")
    if configured:
        path = Path(configured)
        if not path.is_file():
            raise HTTPException(status_code=503, detail=f"CONTINUITY_CONFIG not found: {path}")
        try:
            return build_runtime(load_config(path))
        except Exception as exc:
            raise HTTPException(status_code=503, detail=f"invalid ContinuityOS runtime configuration: {exc}") from exc

    candidate = ModelCandidate(
        id="dev-echo", provider="dev", capabilities={capability}, context_window=1_000_000,
        quality=0.1, reliability=1.0, cost_per_million=0.0, latency_ms=0, privacy="local",
    )
    return RuntimeOrchestrator(candidates=[candidate], health=HealthRegistry(), fleet=ProviderFleet([DevEchoProvider()]))


@api.post("/execute")
def execute_api(request: ExecuteAPIRequest) -> dict:
    capability = Capability(request.capability)
    runtime = _api_runtime(capability)
    try:
        result = runtime.execute(ExecutionRequest(task_id=request.task_id, prompt=request.prompt, requirements=TaskRequirements(capabilities={capability})))
    except LookupError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return result.model_dump(mode="json")
