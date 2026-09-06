from __future__ import annotations

from pathlib import Path

from continuityos.benchmark import BenchmarkCase, BenchmarkRunner
from continuityos.memory import MemoryRecord, SQLiteMemoryAdapter
from continuityos.models import ModelCandidate, TaskRequirements
from continuityos.observability_adapters import LangfuseTracer
from continuityos.providers import ProviderFleet, ProviderRequest, ProviderResult
from continuityos.telemetry import RoutingTelemetry


class FakeProvider:
    name = "fake"
    def available(self) -> bool: return True
    def complete(self, request: ProviderRequest) -> ProviderResult:
        ok = "pass" in request.messages[-1]["content"]
        return ProviderResult(text="PASS" if ok else "FAIL", model=request.model, input_tokens=2, output_tokens=1, cost=0.0)


def candidate() -> ModelCandidate:
    return ModelCandidate(
        id="fake-model",
        provider="fake",
        capabilities={"reasoning"},
        context_window=10000,
        quality=0.8,
        reliability=0.9,
        cost_per_million=0,
        latency_ms=5,
        privacy="local",
    )


def test_benchmark_runner_records_telemetry(tmp_path: Path) -> None:
    telemetry = RoutingTelemetry(tmp_path / "routes.jsonl")
    runner = BenchmarkRunner(ProviderFleet([FakeProvider()]), telemetry)
    cases = [
        BenchmarkCase(name="good", prompt="please pass", expected_substring="PASS"),
        BenchmarkCase(name="bad", prompt="no", expected_substring="PASS"),
    ]
    results = runner.run(candidate(), "benchmark", cases)

    assert [r.success for r in results] == [True, False]
    stats = telemetry.stats("fake-model", "benchmark")
    assert stats.attempts == 2
    assert stats.successes == 1


def test_sqlite_memory_adapter_persists_across_instances(tmp_path: Path) -> None:
    path = tmp_path / "memory.db"
    first = SQLiteMemoryAdapter(path)
    first.put(MemoryRecord(namespace="u1", key="goal", value="ship ContinuityOS", metadata={"kind": "goal"}))

    second = SQLiteMemoryAdapter(path)
    record = second.get("u1", "goal")
    assert record is not None
    assert record.value == "ship ContinuityOS"
    assert second.search("u1", "continuity")[0].metadata["kind"] == "goal"


def test_langfuse_tracer_closes_span_with_status() -> None:
    events: list[tuple[str, dict]] = []

    class Span:
        def update(self, **kwargs): events.append(("update", kwargs))
        def end(self): events.append(("end", {}))

    class Client:
        def start_span(self, **kwargs):
            events.append(("start", kwargs))
            return Span()

    tracer = LangfuseTracer(Client())
    with tracer.span("route", {"candidate": "local"}):
        pass

    assert events[0][0] == "start"
    assert events[0][1]["name"] == "route"
    assert events[-1][0] == "end"
