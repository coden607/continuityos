from pathlib import Path

import pytest

from continuityos.engine import ContinuityEngine
from continuityos.generator import AppGenerator
from continuityos.health import HealthRegistry
from continuityos.mcp import MCPServer
from continuityos.mcp_client import MCPClient
from continuityos.models import Capability, ContextBudget, ModelCandidate, TaskRequirements
from continuityos.providers import ProviderRequest, ProviderResult
from continuityos.secrets import SecretManager
from continuityos.workflow import DurableWorkflowStore, WorkflowState


def candidate(cid: str, quality: float) -> ModelCandidate:
    return ModelCandidate(id=cid, provider=cid, capabilities={Capability.TEXT}, context_window=100_000, quality=quality, reliability=.99, cost_per_million=0, latency_ms=1, privacy="local")


def test_engine_fails_over_and_reports_context_action(tmp_path: Path):
    health = HealthRegistry()
    engine = ContinuityEngine([candidate("best", .9), candidate("backup", .7)], health, max_attempts=2)
    calls = []
    def invoke(c, request):
        calls.append(c.id)
        if c.id == "best":
            raise RuntimeError("boom")
        return ProviderResult(text="ok", model=c.id, input_tokens=10, output_tokens=2)
    result = engine.execute(
        TaskRequirements(capabilities={Capability.TEXT}),
        lambda c: ProviderRequest(model=c.id, messages=[{"role": "user", "content": "hi"}]),
        invoke,
        budget=ContextBudget(limit=100, used=92),
    )
    assert result.candidate_id == "backup"
    assert result.attempts == 2
    assert result.continuity_action.value == "handoff"
    assert calls == ["best", "backup"]


def test_app_generator_creates_safe_modular_app(tmp_path: Path):
    generated = AppGenerator(tmp_path).create("My Great App", template="generic")
    assert generated.root.name == "my-great-app"
    assert generated.pack_file.exists()
    assert ".env.*" in (generated.root / ".gitignore").read_text()


def test_durable_workflow_roundtrip(tmp_path: Path):
    store = DurableWorkflowStore(tmp_path / "state.db")
    state = WorkflowState(workflow_id="w1", step="research", status="running", payload={"x": 1})
    store.save(state)
    assert store.load("w1") == state


def test_mcp_client_requires_auth_before_network(monkeypatch):
    server = MCPServer(name="x", url="https://example.test/mcp", auth_env="MISSING_TOKEN")
    monkeypatch.delenv("MISSING_TOKEN", raising=False)
    with pytest.raises(RuntimeError, match="missing MCP credential"):
        MCPClient().call(server, "tools/list")


def test_secret_manager_never_lists_values(tmp_path: Path):
    manager = SecretManager(tmp_path)
    manager.set("API_KEY", "super-secret")
    assert manager.keys() == ["API_KEY"]
    assert "super-secret" not in repr(manager.keys())


def test_cli_new_app(tmp_path: Path):
    from typer.testing import CliRunner
    from continuityos.cli import app
    result = CliRunner().invoke(app, ["new", "Demo App", "--destination", str(tmp_path)])
    assert result.exit_code == 0
    assert (tmp_path / "demo-app" / "packs" / "demo-app" / "pack.json").exists()


def test_tool_catalog_contains_core_cli():
    from continuityos.tooling import tool_statuses
    tools = {t.command: t for t in tool_statuses()}
    assert "git" in tools
    assert tools["git"].required
    assert "sops" in tools and "age" in tools


def test_sops_vault_fails_cleanly_when_tools_missing(monkeypatch, tmp_path: Path):
    from continuityos.vault import SopsAgeVault
    monkeypatch.setattr("shutil.which", lambda command: None)
    vault = SopsAgeVault(tmp_path)
    assert not vault.available()
    with pytest.raises(RuntimeError, match="sops and age"):
        vault.encrypt(tmp_path / "a", tmp_path / "b", age_recipient="age1test")


def test_cli_context_supports_named_options():
    from typer.testing import CliRunner
    from continuityos.cli import app
    result = CliRunner().invoke(app, ["context", "--limit", "100", "--used", "91"])
    assert result.exit_code == 0
    assert result.stdout.strip() == "handoff"


def test_repo_bootstrap_fails_cleanly_without_gh(monkeypatch, tmp_path: Path):
    from continuityos.repository import RepositoryBootstrapper
    monkeypatch.setattr("shutil.which", lambda command: "/usr/bin/git" if command == "git" else None)
    result = RepositoryBootstrapper(tmp_path).bootstrap("coden607/continuityos")
    assert not result.created and not result.pushed
    assert "GitHub authentication" in result.message


def test_cli_repo_bootstrap_accepts_positional_repository(monkeypatch):
    from typer.testing import CliRunner
    from continuityos.cli import app
    monkeypatch.setattr("continuityos.repository.shutil.which", lambda command: None)
    result = CliRunner().invoke(app, ["repo-bootstrap", "coden607/continuityos"])
    assert result.exit_code == 1
    body = __import__("json").loads(result.stdout)
    assert body["repository"] == "coden607/continuityos"
    assert body["pushed"] is False
