from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from continuityos.engine import ContinuityEngine
from continuityos.health import HealthRegistry
from continuityos.mcp import MCPServer
from continuityos.mcp_client import MCPClient, MCPError
from continuityos.models import ModelCandidate, TaskRequirements
from continuityos.providers import ProviderFleet, ProviderRequest, ProviderResult
from continuityos.realtime import AudioChunkStream
from continuityos.workflow import DBOSAdapter


class FakeProvider:
    def __init__(self, name: str, *, fail: bool = False) -> None:
        self.name = name
        self.fail = fail
        self.calls: list[ProviderRequest] = []

    def available(self) -> bool:
        return True

    def complete(self, request: ProviderRequest) -> ProviderResult:
        self.calls.append(request)
        if self.fail:
            raise RuntimeError("provider failed")
        return ProviderResult(text=f"ok:{request.model}", model=request.model, input_tokens=3, output_tokens=2)


def candidate(cid: str, provider: str, quality: float) -> ModelCandidate:
    return ModelCandidate(
        id=cid,
        provider=provider,
        model=cid,
        capabilities={"reasoning"},
        context_window=100_000,
        cost_per_million=0,
        latency_ms=20,
        quality=quality,
        reliability=0.99,
        privacy="local",
    )


def test_provider_fleet_drives_engine_and_fails_over() -> None:
    first = FakeProvider("first", fail=True)
    second = FakeProvider("second")
    fleet = ProviderFleet([first, second])
    health = HealthRegistry()
    c1 = candidate("m1", "first", 1.0)
    c2 = candidate("m2", "second", 0.8)
    engine = ContinuityEngine([c1, c2], health, max_attempts=2)
    req = TaskRequirements(task_type="analysis", capabilities={"reasoning"}, context_needed=10)

    result = engine.execute_with_fleet(req, lambda c: ProviderRequest(model=c.id, messages=[{"role": "user", "content": "x"}]), fleet)

    assert result.candidate_id == "m2"
    assert result.attempts == 2
    assert result.result.text == "ok:m2"
    assert len(first.calls) == 1
    assert len(second.calls) == 1


def test_provider_fleet_rejects_unavailable_provider() -> None:
    fleet = ProviderFleet([])
    with pytest.raises(LookupError, match="no provider adapter"):
        fleet.complete("missing", ProviderRequest(model="x", messages=[]))


def test_mcp_client_raises_typed_error_on_jsonrpc_error(monkeypatch: pytest.MonkeyPatch) -> None:
    class Response:
        headers = {"Content-Type": "application/json"}
        def __enter__(self): return self
        def __exit__(self, *args): return None
        def read(self):
            return json.dumps({"jsonrpc": "2.0", "id": 1, "error": {"code": -32601, "message": "nope"}}).encode()

    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **k: Response())
    server = MCPServer(name="x", url="https://example.test/mcp", transport="streamable_http")

    with pytest.raises(MCPError) as exc:
        MCPClient().call(server, "tools/list")
    assert exc.value.code == -32601
    assert "nope" in str(exc.value)


def test_mcp_client_parses_last_sse_data_event(monkeypatch: pytest.MonkeyPatch) -> None:
    class Response:
        headers = {"Content-Type": "text/event-stream"}
        def __enter__(self): return self
        def __exit__(self, *args): return None
        def read(self):
            return b"event: message\ndata: {\"jsonrpc\":\"2.0\",\"id\":1,\"result\":{\"phase\":1}}\n\nevent: message\ndata: {\"jsonrpc\":\"2.0\",\"id\":1,\"result\":{\"phase\":2}}\n\n"

    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **k: Response())
    server = MCPServer(name="x", url="https://example.test/mcp", transport="streamable_http")
    result = MCPClient().call(server, "ping")
    assert result["result"]["phase"] == 2


def test_dbos_adapter_persists_running_and_completed_states(tmp_path: Path) -> None:
    seen: list[str] = []

    class FakeDBOS:
        def run(self, workflow_id: str, fn, *args, **kwargs):
            seen.append(workflow_id)
            return fn(*args, **kwargs)

    adapter = DBOSAdapter(FakeDBOS(), fallback_path=tmp_path / "workflows.db")
    result = adapter.run("wf-1", "answer", lambda x: x + 1, 41)

    assert result == 42
    assert seen == ["wf-1"]
    state = adapter.store.load("wf-1")
    assert state is not None
    assert state.status == "completed"
    assert state.step == "answer"


def test_audio_chunk_stream_preserves_order() -> None:
    async def run() -> list[bytes]:
        stream = AudioChunkStream()
        await stream.push(b"a")
        await stream.push(b"b")
        await stream.close()
        out: list[bytes] = []
        async for chunk in stream:
            out.append(chunk)
        return out

    assert asyncio.run(run()) == [b"a", b"b"]
