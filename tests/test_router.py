from continuityos.health import HealthRegistry, HealthState
from continuityos.models import Capability, ModelCandidate, TaskRequirements
from continuityos.router import Router


def candidates():
    return [
        ModelCandidate(id="cheap", capabilities={Capability.TEXT}, context_window=16000, quality=0.7, reliability=0.99, cost_per_million=0.0, latency_ms=100, privacy="local"),
        ModelCandidate(id="big", capabilities={Capability.TEXT, Capability.REASONING}, context_window=200000, quality=0.95, reliability=0.97, cost_per_million=10.0, latency_ms=500, privacy="cloud"),
    ]


def test_router_prefers_free_local_when_sufficient():
    router = Router(candidates(), HealthRegistry())
    result = router.route(TaskRequirements(capabilities={Capability.TEXT}, context_needed=4000, privacy="local"))
    assert result.candidate.id == "cheap"


def test_router_uses_reasoning_model_for_reasoning_task():
    router = Router(candidates(), HealthRegistry())
    result = router.route(TaskRequirements(capabilities={Capability.REASONING}, context_needed=32000))
    assert result.candidate.id == "big"


def test_unhealthy_provider_is_excluded():
    health = HealthRegistry()
    health.set("big", HealthState.UNHEALTHY)
    router = Router(candidates(), health)
    try:
        router.route(TaskRequirements(capabilities={Capability.REASONING}, context_needed=32000))
    except LookupError:
        pass
    else:
        raise AssertionError("expected no healthy candidate")
