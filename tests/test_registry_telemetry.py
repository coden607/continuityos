from pathlib import Path

from continuityos.health import HealthRegistry
from continuityos.models import Capability, ModelCandidate, TaskRequirements
from continuityos.registry import CapabilityRegistry
from continuityos.router import Router
from continuityos.telemetry import RoutingTelemetry


def test_registry_filters_by_capability():
    registry = CapabilityRegistry()
    registry.register(ModelCandidate(id='text', capabilities={Capability.TEXT}, context_window=8000, quality=.7, reliability=.9, cost_per_million=0, latency_ms=50, privacy='local'))
    registry.register(ModelCandidate(id='vision', capabilities={Capability.TEXT, Capability.VISION}, context_window=16000, quality=.8, reliability=.9, cost_per_million=1, latency_ms=100, privacy='cloud'))
    assert [c.id for c in registry.for_capabilities({Capability.VISION})] == ['vision']


def test_router_records_outcome_and_learns(tmp_path: Path):
    telemetry = RoutingTelemetry(tmp_path / 'routing.jsonl')
    candidates = [
        ModelCandidate(id='a', capabilities={Capability.TEXT}, context_window=8000, quality=.8, reliability=.95, cost_per_million=0, latency_ms=100, privacy='local'),
        ModelCandidate(id='b', capabilities={Capability.TEXT}, context_window=8000, quality=.8, reliability=.95, cost_per_million=0, latency_ms=100, privacy='local'),
    ]
    telemetry.record('a', 'text', success=False, latency_ms=100, tokens=10, cost=0)
    telemetry.record('b', 'text', success=True, latency_ms=100, tokens=10, cost=0)
    router = Router(candidates, HealthRegistry(), telemetry=telemetry)
    result = router.route(TaskRequirements(capabilities={Capability.TEXT}, context_needed=10, task_type='text'))
    assert result.candidate.id == 'b'
