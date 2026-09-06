from pathlib import Path

import pytest

from continuityos.blueprint import AppBlueprint, load_blueprint
from continuityos.dispatch import CapabilityDispatcher, DispatchRequirements, DispatchTarget, TargetKind
from continuityos.health import HealthRegistry
from continuityos.models import Capability


def test_dispatch_rejects_free_target_below_quality_floor():
    health = HealthRegistry()
    low = DispatchTarget(id="free", kind=TargetKind.TOOL, capabilities={Capability.TEXT}, quality=.70)
    strong = DispatchTarget(id="strong", kind=TargetKind.MODEL, capabilities={Capability.TEXT}, quality=.96, token_cost_per_million=10)
    for target in (low, strong):
        health.mark_success(target.id)
    decision = CapabilityDispatcher([low, strong], health).route(
        DispatchRequirements(capabilities={Capability.TEXT}, min_quality=.9)
    )
    assert decision.target.id == "strong"


def test_dispatch_rejects_target_missing_output_contract():
    health = HealthRegistry()
    patch_only = DispatchTarget(
        id="patch-only", kind=TargetKind.TOOL, capabilities={Capability.CODE}, quality=.99, outputs={"patch"}
    )
    complete = DispatchTarget(
        id="complete", kind=TargetKind.MODEL, capabilities={Capability.CODE}, quality=.95,
        outputs={"patch", "tests"}, token_cost_per_million=8
    )
    for target in (patch_only, complete):
        health.mark_success(target.id)
    decision = CapabilityDispatcher([patch_only, complete], health).route(
        DispatchRequirements(capabilities={Capability.CODE}, required_outputs={"patch", "tests"})
    )
    assert decision.target.id == "complete"


def test_dispatch_filters_language_framework_and_verification():
    health = HealthRegistry()
    wrong = DispatchTarget(
        id="wrong", kind=TargetKind.TOOL, capabilities={Capability.CODE}, quality=.99,
        languages={"python"}, frameworks={"django"}, verification={"tests"}
    )
    right = DispatchTarget(
        id="right", kind=TargetKind.MODEL, capabilities={Capability.CODE}, quality=.95,
        languages={"typescript"}, frameworks={"nextjs"}, verification={"tests", "typecheck"},
        token_cost_per_million=5
    )
    for target in (wrong, right):
        health.mark_success(target.id)
    decision = CapabilityDispatcher([wrong, right], health).route(
        DispatchRequirements(
            capabilities={Capability.CODE}, languages={"typescript"}, frameworks={"nextjs"},
            required_verification={"tests", "typecheck"}
        )
    )
    assert decision.target.id == "right"


def test_blueprint_loads_and_rejects_unknown_fields(tmp_path: Path):
    path = tmp_path / "continuity.blueprint.toml"
    path.write_text('''
[app]
name = "CaseCraft"
domain = "legal"
version = "0.1.0"
profile = "minimal"

[development]
method = "continuity-hybrid"
roles = ["platform-steward", "developer", "qa"]
architecture_gate = true
security_gate = true
eval_gate = true

[quality]
min_quality = 0.92
min_reliability = 0.95
prefer_zero_token = true
escalation = ["deterministic", "local_free", "economical", "premium", "council"]

[verification]
gates = ["compile", "tests", "typecheck", "security", "architecture"]

[features]
pwa = true
api = true
voice = false
memory = true

[deployment]
targets = ["github"]

secrets = ["OPENAI_API_KEY"]
''')
    bp = load_blueprint(path)
    assert isinstance(bp, AppBlueprint)
    assert bp.quality.min_quality == .92
    assert "typecheck" in bp.verification.gates

    path.write_text(path.read_text() + '\nunknown = "bad"\n')
    with pytest.raises(Exception):
        load_blueprint(path)
