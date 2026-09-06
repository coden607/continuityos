from .models import Capability, ModelCandidate


def default_candidates() -> list[ModelCandidate]:
    return [
        ModelCandidate(
            id="local-default",
            provider="local",
            capabilities={Capability.TEXT},
            context_window=32768,
            quality=0.65,
            reliability=0.99,
            cost_per_million=0.0,
            latency_ms=150,
            privacy="local",
        ),
        ModelCandidate(
            id="cloud-reasoner",
            provider="generic-cloud",
            capabilities={Capability.TEXT, Capability.REASONING},
            context_window=200000,
            quality=0.95,
            reliability=0.97,
            cost_per_million=5.0,
            latency_ms=500,
            privacy="cloud",
        ),
    ]
