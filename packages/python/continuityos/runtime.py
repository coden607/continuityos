from __future__ import annotations

import json
from pathlib import Path
from time import perf_counter
from typing import Any

from pydantic import BaseModel, Field

from .continuity import evaluate_context
from .guardrails import GuardrailPolicy
from .health import HealthRegistry
from .memory import MemoryAdapter, MemoryRecord
from .models import ContextBudget, ContinuityAction, ModelCandidate, TaskRequirements
from .providers import ProviderFleet, ProviderRequest
from .router import Router
from .telemetry import RoutingTelemetry


class ExecutionRequest(BaseModel):
    task_id: str
    prompt: str
    requirements: TaskRequirements
    context_budget: ContextBudget | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExecutionResult(BaseModel):
    task_id: str
    text: str
    candidate_id: str
    provider: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    cost: float = 0.0
    context_action: str = ContinuityAction.NORMAL.value
    checkpoint_path: str | None = None
    attempts: list[str] = Field(default_factory=list)


class RuntimeOrchestrator:
    """Single fail-closed execution path for ContinuityOS AI tasks."""

    def __init__(
        self,
        *,
        candidates: list[ModelCandidate],
        health: HealthRegistry,
        fleet: ProviderFleet,
        telemetry: RoutingTelemetry | None = None,
        memory: MemoryAdapter | None = None,
        guardrails: list[GuardrailPolicy] | None = None,
        checkpoint_dir: str | Path = ".continuity/checkpoints",
    ) -> None:
        self.candidates = candidates
        self.health = health
        self.fleet = fleet
        self.telemetry = telemetry or RoutingTelemetry()
        self.memory = memory
        self.guardrails = guardrails or []
        self.checkpoint_dir = Path(checkpoint_dir)

    def _guard(self, request: ExecutionRequest) -> None:
        payload = {"task_id": request.task_id, "prompt": request.prompt, "metadata": request.metadata}
        reasons: list[str] = []
        for policy in self.guardrails:
            decision = policy.evaluate("model:complete", payload)
            if not decision.allowed:
                reasons.extend(decision.reasons or ["guardrail denied request"])
        if reasons:
            raise PermissionError("; ".join(reasons))

    def _checkpoint(self, request: ExecutionRequest, action: ContinuityAction) -> str | None:
        if action not in {ContinuityAction.CHECKPOINT, ContinuityAction.HANDOFF, ContinuityAction.EMERGENCY}:
            return None
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        path = self.checkpoint_dir / f"{request.task_id}.json"
        path.write_text(
            json.dumps(
                {
                    "task_id": request.task_id,
                    "prompt": request.prompt,
                    "requirements": request.requirements.model_dump(mode="json"),
                    "metadata": request.metadata,
                    "context_action": action.value,
                },
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        return str(path)

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        self._guard(request)
        action = evaluate_context(request.context_budget) if request.context_budget else ContinuityAction.NORMAL
        checkpoint_path = self._checkpoint(request, action)
        attempts: list[str] = []
        attempted: set[str] = set()
        routing_requirements = request.requirements
        if request.context_budget and action in {ContinuityAction.HANDOFF, ContinuityAction.EMERGENCY}:
            expanded = request.requirements.model_copy(
                update={"context_needed": max(request.requirements.context_needed, request.context_budget.limit + 1)}
            )
            try:
                Router(self.candidates, self.health, self.telemetry).route(expanded)
            except LookupError:
                pass
            else:
                routing_requirements = expanded

        while True:
            remaining = [candidate for candidate in self.candidates if candidate.id not in attempted]
            router = Router(remaining, self.health, self.telemetry)
            try:
                decision = router.route(routing_requirements)
            except LookupError:
                raise LookupError(f"no runnable candidate remains after attempts: {attempts}") from None

            candidate = decision.candidate
            attempted.add(candidate.id)
            attempts.append(candidate.id)
            provider_request = ProviderRequest(
                model=candidate.model or candidate.id,
                messages=[{"role": "user", "content": request.prompt}],
                max_tokens=candidate.max_output_tokens,
                metadata=request.metadata,
            )
            started = perf_counter()
            try:
                provider_result = self.fleet.complete(candidate.provider, provider_request)
            except Exception:
                elapsed = max(0, int((perf_counter() - started) * 1000))
                self.telemetry.record(
                    candidate.id,
                    request.requirements.task_type,
                    success=False,
                    latency_ms=elapsed,
                    tokens=0,
                    cost=0.0,
                )
                self.health.mark_failure(candidate.id)
                continue

            elapsed = max(0, int((perf_counter() - started) * 1000))
            self.health.mark_success(candidate.id)
            self.telemetry.record(
                candidate.id,
                request.requirements.task_type,
                success=True,
                latency_ms=elapsed,
                tokens=provider_result.total_tokens,
                cost=provider_result.cost,
            )
            result = ExecutionResult(
                task_id=request.task_id,
                text=provider_result.text,
                candidate_id=candidate.id,
                provider=candidate.provider,
                model=provider_result.model,
                input_tokens=provider_result.input_tokens,
                output_tokens=provider_result.output_tokens,
                cost=provider_result.cost,
                context_action=action.value,
                checkpoint_path=checkpoint_path,
                attempts=attempts,
            )
            if self.memory:
                self.memory.put(
                    MemoryRecord(
                        namespace=f"task:{request.task_id}",
                        key="last_result",
                        value=result.model_dump(mode="json"),
                        metadata={"candidate_id": candidate.id},
                    )
                )
            return result
