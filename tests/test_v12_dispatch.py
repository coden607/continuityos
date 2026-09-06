from continuityos.dispatch import CapabilityDispatcher, DispatchRequirements, DispatchTarget, TargetKind
from continuityos.health import HealthRegistry, HealthState
from continuityos.models import Capability, ModelCandidate
from continuityos.plugins import PluginManifest


def model_target() -> DispatchTarget:
    model = ModelCandidate(
        id="cloud-reranker", provider="litellm", model="openai/reranker",
        capabilities={Capability.RERANK}, context_window=100000,
        quality=.95, reliability=.98, cost_per_million=4.0, latency_ms=250, privacy="cloud",
    )
    return DispatchTarget.from_model(model)


def skill_target() -> DispatchTarget:
    plugin = PluginManifest(
        name="local-rerank", version="1.0", capabilities={Capability.RERANK}, kind="skill"
    )
    return DispatchTarget.from_plugin(plugin, quality=.85, reliability=.99, latency_ms=20, privacy="local")


def test_dispatch_prefers_zero_token_skill_over_paid_model_when_capability_matches():
    dispatcher = CapabilityDispatcher([model_target(), skill_target()], HealthRegistry())
    decision = dispatcher.route(DispatchRequirements(capabilities={Capability.RERANK}, prefer_zero_token=True))
    assert decision.target.id == "local-rerank"
    assert decision.target.kind == TargetKind.SKILL
    assert "avoids model tokens" in decision.reasons


def test_dispatch_can_restrict_target_kind_to_models():
    dispatcher = CapabilityDispatcher([model_target(), skill_target()], HealthRegistry())
    decision = dispatcher.route(DispatchRequirements(capabilities={Capability.RERANK}, target_kinds={TargetKind.MODEL}))
    assert decision.target.id == "cloud-reranker"


def test_dispatch_excludes_unhealthy_target():
    health = HealthRegistry()
    health.set("local-rerank", HealthState.UNHEALTHY)
    dispatcher = CapabilityDispatcher([model_target(), skill_target()], health)
    decision = dispatcher.route(DispatchRequirements(capabilities={Capability.RERANK}, prefer_zero_token=True))
    assert decision.target.id == "cloud-reranker"
