from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Callable

from .continuity import evaluate_context
from .health import HealthRegistry
from .models import ContextBudget, ContextCapsule, ContinuityAction, ModelCandidate, TaskRequirements
from .providers import ProviderFleet, ProviderRequest, ProviderResult
from .router import Router
from .telemetry import RoutingTelemetry


@dataclass(frozen=True)
class ExecutionResult:
    candidate_id: str
    provider: str
    result: ProviderResult
    attempts: int
    continuity_action: ContinuityAction


class ContinuityEngine:
    """Capability-aware routing + retry/failover + context pressure handling."""

    def __init__(
        self,
        candidates: list[ModelCandidate],
        health: HealthRegistry,
        telemetry: RoutingTelemetry | None = None,
        max_attempts: int = 3,
    ) -> None:
        self.health = health
        self.telemetry = telemetry
        self.max_attempts = max_attempts
        self._candidates = list(candidates)

    def plan_context(self, budget: ContextBudget) -> ContinuityAction:
        return evaluate_context(budget)

    def execute(
        self,
        requirements: TaskRequirements,
        request_factory: Callable[[ModelCandidate], ProviderRequest],
        invoke: Callable[[ModelCandidate, ProviderRequest], ProviderResult],
        *,
        budget: ContextBudget | None = None,
    ) -> ExecutionResult:
        continuity_action = evaluate_context(budget) if budget else ContinuityAction.NORMAL
        attempted: set[str] = set()
        last_error: Exception | None = None

        for attempt in range(1, self.max_attempts + 1):
            remaining = [c for c in self._candidates if c.id not in attempted]
            if not remaining:
                break
            router = Router(remaining, self.health, self.telemetry)
            try:
                decision = router.route(requirements)
            except LookupError as exc:
                last_error = exc
                break
            candidate = decision.candidate
            attempted.add(candidate.id)
            request = request_factory(candidate)
            started = perf_counter()
            try:
                result = invoke(candidate, request)
            except Exception as exc:  # provider boundary intentionally broad
                latency_ms = int((perf_counter() - started) * 1000)
                self.health.mark_failure(candidate.id)
                if self.telemetry:
                    self.telemetry.record(candidate.id, requirements.task_type, success=False, latency_ms=latency_ms, tokens=0, cost=0.0)
                last_error = exc
                continue

            latency_ms = int((perf_counter() - started) * 1000)
            self.health.mark_success(candidate.id)
            if self.telemetry:
                self.telemetry.record(
                    candidate.id,
                    requirements.task_type,
                    success=True,
                    latency_ms=latency_ms,
                    tokens=result.total_tokens,
                    cost=result.cost,
                )
            return ExecutionResult(
                candidate_id=candidate.id,
                provider=candidate.provider,
                result=result,
                attempts=attempt,
                continuity_action=continuity_action,
            )

        raise RuntimeError(f"all eligible providers failed: {last_error}")

    def execute_with_fleet(
        self,
        requirements: TaskRequirements,
        request_factory: Callable[[ModelCandidate], ProviderRequest],
        fleet: ProviderFleet,
        *,
        budget: ContextBudget | None = None,
    ) -> ExecutionResult:
        return self.execute(
            requirements,
            request_factory,
            lambda candidate, request: fleet.complete(candidate.provider, request),
            budget=budget,
        )

    @staticmethod
    def capsule_for_handoff(
        *, objective: str,
        current_task: str,
        next_action: str,
        reason: str,
        requirements: list[str] | None = None,
        constraints: list[str] | None = None,
        facts: list[str] | None = None,
        completed_work: list[str] | None = None,
        open_work: list[str] | None = None,
    ) -> ContextCapsule:
        return ContextCapsule(
            objective=objective,
            current_task=current_task,
            user_requirements=requirements or [],
            hard_constraints=constraints or [],
            decisions=[],
            completed_work=completed_work or [],
            open_work=open_work or [],
            facts=facts or [],
            artifacts=[],
            tool_state=[],
            citations=[],
            memory_refs=[],
            failed_approaches=[],
            current_plan=[],
            next_action=next_action,
            handoff_reason=reason,
        )
