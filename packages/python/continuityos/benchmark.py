from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter

from .models import ModelCandidate
from .providers import ProviderFleet, ProviderRequest
from .telemetry import RoutingTelemetry


@dataclass(frozen=True)
class BenchmarkCase:
    name: str
    prompt: str
    expected_substring: str | None = None


@dataclass(frozen=True)
class BenchmarkResult:
    case: str
    success: bool
    latency_ms: int
    tokens: int
    cost: float
    text: str


class BenchmarkRunner:
    """Runs deterministic smoke benchmarks and feeds observed outcomes into routing telemetry."""

    def __init__(self, fleet: ProviderFleet, telemetry: RoutingTelemetry) -> None:
        self.fleet = fleet
        self.telemetry = telemetry

    def run(self, candidate: ModelCandidate, task_type: str, cases: list[BenchmarkCase]) -> list[BenchmarkResult]:
        results: list[BenchmarkResult] = []
        for case in cases:
            request = ProviderRequest(model=candidate.model or candidate.id, messages=[{"role": "user", "content": case.prompt}])
            started = perf_counter()
            try:
                response = self.fleet.complete(candidate.provider, request)
                success = case.expected_substring is None or case.expected_substring in response.text
                tokens = response.total_tokens
                cost = response.cost
                text = response.text
            except Exception as exc:
                success = False
                tokens = 0
                cost = 0.0
                text = str(exc)
            latency_ms = int((perf_counter() - started) * 1000)
            self.telemetry.record(candidate.id, task_type, success=success, latency_ms=latency_ms, tokens=tokens, cost=cost)
            results.append(BenchmarkResult(case.name, success, latency_ms, tokens, cost, text))
        return results
