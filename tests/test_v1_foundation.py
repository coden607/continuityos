from pathlib import Path

from continuityos.adaptive import RoutingLearner
from continuityos.compression import compress_capsule
from continuityos.engine import ContinuityEngine
from continuityos.health import HealthRegistry, HealthState
from continuityos.integrations import integration_statuses
from continuityos.memory import MemoryRecord
from continuityos.memory_adapters import Mem0Adapter
from continuityos.models import Capability, ModelCandidate, TaskRequirements
from continuityos.self_heal import HealthCheckResult, SelfHealingSupervisor
from continuityos.telemetry import RoutingTelemetry
from continuityos.mcp import MCPServer
from continuityos.mcp_client import MCPClient
from continuityos.secrets import SecretManager


def candidate(cid: str, cost: float = 0.0):
    return ModelCandidate(id=cid, provider="local", capabilities={Capability.TEXT}, context_window=100000, quality=.8, reliability=.9, cost_per_million=cost, latency_ms=10, privacy="local")


def test_capsule_compression_preserves_critical_fields():
    cap = ContinuityEngine.capsule_for_handoff(objective="obj", current_task="task", next_action="next", reason="pressure", requirements=["must"], constraints=["never lose"], facts=["x"*1000])
    out = compress_capsule(cap, target_chars=300)
    assert out.objective == "obj" and out.user_requirements == ["must"] and out.hard_constraints == ["never lose"]
    assert len(out.facts[0]) < 1000


def test_routing_learner_uses_observed_success(tmp_path: Path):
    tel = RoutingTelemetry(tmp_path / "routing.jsonl")
    for _ in range(4): tel.record("a", "code", success=True, latency_ms=20, tokens=10, cost=0)
    for _ in range(4): tel.record("b", "code", success=False, latency_ms=20, tokens=10, cost=0)
    req = TaskRequirements(capabilities={Capability.TEXT}, task_type="code")
    recs = RoutingLearner(tel).recommend([candidate("a"), candidate("b")], req)
    assert recs[0].candidate_id == "a"


def test_self_healing_supervisor_recovers():
    registry = HealthRegistry()
    sup = SelfHealingSupervisor(registry, quarantine_after=1)
    state = {"ok": False}
    sup.register("api", lambda: HealthCheckResult("api", state["ok"]), healer=lambda: state.__setitem__("ok", True) or True)
    sup.check("api")
    assert registry.get("api").state == HealthState.QUARANTINED
    result = sup.heal("api")
    assert result.recovered and registry.routable("api")


def test_mem0_adapter_with_injected_client():
    class Client:
        def __init__(self): self.rows=[]
        def add(self, value, user_id, metadata): self.rows.append((value,user_id,metadata))
        def search(self, query, user_id, limit): return {"results":[{"memory":"hello","metadata":{"key":"k"}}]}
    c=Client(); adapter=Mem0Adapter(c)
    adapter.put(MemoryRecord(namespace="u", key="k", value="hello"))
    assert adapter.get("u","k").value == "hello"


def test_mcp_convenience_methods(monkeypatch):
    client=MCPClient(); server=MCPServer(name="x", url="https://example.com")
    calls=[]
    def fake(server, method, params=None, request_id=1):
        calls.append(method)
        if method=="tools/list": return {"result":{"tools":[{"name":"a"}]}}
        return {"result":{}}
    monkeypatch.setattr(client,"call",fake)
    assert client.list_tools(server)[0]["name"]=="a"
    client.call_tool(server,"a",{"x":1})
    assert calls == ["tools/list","tools/call"]


def test_secret_sync_all_invokes_each_pair(tmp_path: Path, monkeypatch):
    sm=SecretManager(tmp_path); sm.set("A","1"); sm.set("B","2")
    seen=[]
    monkeypatch.setattr(sm,"sync",lambda key,target,repository=None: seen.append((key,target)) or type("R",(),{"target":target,"synced":True,"reason":""})())
    sm.sync_all(["github","supabase"])
    assert set(seen)=={("A","github"),("A","supabase"),("B","github"),("B","supabase")}


def test_optional_integration_statuses_are_stable():
    names={s.name for s in integration_statuses()}
    assert {"litellm","mem0","graphiti","nemo_guardrails","dbos","opentelemetry","langfuse","pipecat"}.issubset(names)

def test_v1_version_and_cli_registration():
    import continuityos
    from continuityos.cli import app
    from typer.testing import CliRunner
    assert continuityos.__version__ == "1.2.1"
    runner = CliRunner()
    result = runner.invoke(app, ["integrations"])
    assert result.exit_code == 0 and "mem0" in result.stdout
