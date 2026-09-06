from pathlib import Path

import pytest

from continuityos.health import HealthRegistry
from continuityos.memory import SQLiteMemoryAdapter
from continuityos.models import Capability, ContextBudget, ModelCandidate, TaskRequirements
from continuityos.providers import ProviderFleet, ProviderRequest, ProviderResult
from continuityos.runtime import ExecutionRequest, RuntimeOrchestrator
from continuityos.telemetry import RoutingTelemetry


class FakeProvider:
    name = "fake"

    def __init__(self, fail: bool = False):
        self.fail = fail

    def available(self) -> bool:
        return True

    def complete(self, request: ProviderRequest) -> ProviderResult:
        if self.fail:
            raise RuntimeError("boom")
        return ProviderResult(text="answer", model=request.model, input_tokens=10, output_tokens=5, cost=0.0)


def candidate(cid: str, provider: str = "fake", quality: float = 0.8) -> ModelCandidate:
    return ModelCandidate(
        id=cid,
        provider=provider,
        capabilities={Capability.TEXT, Capability.REASONING},
        context_window=100_000,
        quality=quality,
        reliability=0.95,
        cost_per_million=0,
        latency_ms=10,
        privacy="local",
    )


def test_runtime_executes_routes_records_memory_and_telemetry(tmp_path: Path):
    telemetry = RoutingTelemetry(tmp_path / "routes.jsonl")
    memory = SQLiteMemoryAdapter(tmp_path / "memory.db")
    runtime = RuntimeOrchestrator(
        candidates=[candidate("local-a")],
        health=HealthRegistry(),
        fleet=ProviderFleet([FakeProvider()]),
        telemetry=telemetry,
        memory=memory,
        checkpoint_dir=tmp_path / "checkpoints",
    )

    result = runtime.execute(
        ExecutionRequest(
            task_id="t1",
            prompt="hello",
            requirements=TaskRequirements(capabilities={Capability.TEXT}, task_type="qa"),
            context_budget=ContextBudget(limit=1000, used=100),
        )
    )

    assert result.text == "answer"
    assert result.candidate_id == "local-a"
    assert result.context_action == "normal"
    assert telemetry.stats("local-a", "qa").attempts == 1
    assert memory.get("task:t1", "last_result").value["text"] == "answer"


def test_runtime_creates_checkpoint_when_context_pressure_is_high(tmp_path: Path):
    runtime = RuntimeOrchestrator(
        candidates=[candidate("local-a")],
        health=HealthRegistry(),
        fleet=ProviderFleet([FakeProvider()]),
        checkpoint_dir=tmp_path / "checkpoints",
    )

    result = runtime.execute(
        ExecutionRequest(
            task_id="t2",
            prompt="hello",
            requirements=TaskRequirements(capabilities={Capability.TEXT}),
            context_budget=ContextBudget(limit=1000, used=850),
        )
    )

    assert result.context_action == "checkpoint"
    assert result.checkpoint_path is not None
    assert Path(result.checkpoint_path).exists()


def test_runtime_fails_closed_when_guardrail_blocks(tmp_path: Path):
    class BlockingGuardrail:
        def evaluate(self, action: str, payload: dict):
            from continuityos.models import GuardrailDecision
            return GuardrailDecision(allowed=False, reasons=["blocked"])

    runtime = RuntimeOrchestrator(
        candidates=[candidate("local-a")],
        health=HealthRegistry(),
        fleet=ProviderFleet([FakeProvider()]),
        guardrails=[BlockingGuardrail()],
        checkpoint_dir=tmp_path / "checkpoints",
    )

    with pytest.raises(PermissionError, match="blocked"):
        runtime.execute(
            ExecutionRequest(
                task_id="t3",
                prompt="hello",
                requirements=TaskRequirements(capabilities={Capability.TEXT}),
            )
        )


def test_runtime_degrades_failed_candidate_and_falls_back(tmp_path: Path):
    class PrimaryProvider(FakeProvider):
        name = "primary"

    class BackupProvider(FakeProvider):
        name = "backup"

    health = HealthRegistry()
    runtime = RuntimeOrchestrator(
        candidates=[candidate("a", "primary", .95), candidate("b", "backup", .80)],
        health=health,
        fleet=ProviderFleet([PrimaryProvider(fail=True), BackupProvider()]),
        checkpoint_dir=tmp_path / "checkpoints",
    )

    result = runtime.execute(
        ExecutionRequest(
            task_id="t4",
            prompt="hello",
            requirements=TaskRequirements(capabilities={Capability.TEXT}),
        )
    )

    assert result.candidate_id == "b"
    assert health.get("a").state.value == "degraded"
    assert health.get("a").failure_count == 1


def test_runtime_uses_provider_model_name_separately_from_candidate_id(tmp_path: Path):
    class CaptureProvider(FakeProvider):
        name = "capture"
        def __init__(self):
            super().__init__()
            self.last_model = None
        def complete(self, request: ProviderRequest) -> ProviderResult:
            self.last_model = request.model
            return super().complete(request)

    provider = CaptureProvider()
    c = candidate("cheap-reasoner", "capture")
    c = c.model_copy(update={"model": "openai/gpt-future-mini"})
    runtime = RuntimeOrchestrator(
        candidates=[c],
        health=HealthRegistry(),
        fleet=ProviderFleet([provider]),
        checkpoint_dir=tmp_path / "checkpoints",
    )
    result = runtime.execute(ExecutionRequest(task_id="model-alias", prompt="hi", requirements=TaskRequirements(capabilities={Capability.TEXT})))
    assert provider.last_model == "openai/gpt-future-mini"
    assert result.candidate_id == "cheap-reasoner"


def test_handoff_pressure_routes_to_candidate_with_larger_context_window(tmp_path: Path):
    small = ModelCandidate(
        id="small", provider="small-provider", capabilities={Capability.TEXT}, context_window=1000,
        quality=.99, reliability=.99, cost_per_million=0, latency_ms=1, privacy="local",
    )
    large = ModelCandidate(
        id="large", provider="large-provider", capabilities={Capability.TEXT}, context_window=5000,
        quality=.70, reliability=.99, cost_per_million=0, latency_ms=2, privacy="local",
    )

    class Small(FakeProvider):
        name = "small-provider"
    class Large(FakeProvider):
        name = "large-provider"

    runtime = RuntimeOrchestrator(
        candidates=[small, large], health=HealthRegistry(), fleet=ProviderFleet([Small(), Large()]),
        checkpoint_dir=tmp_path / "checkpoints",
    )
    result = runtime.execute(ExecutionRequest(
        task_id="handoff-large", prompt="continue",
        requirements=TaskRequirements(capabilities={Capability.TEXT}),
        context_budget=ContextBudget(limit=1000, used=920),
    ))
    assert result.context_action == "handoff"
    assert result.candidate_id == "large"
