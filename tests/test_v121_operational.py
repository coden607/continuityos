from pathlib import Path

from fastapi.testclient import TestClient
from typer.testing import CliRunner

from continuityos.cli import app
from continuityos.repository import RepoBootstrapResult, RepositoryBootstrapper
from services.api.main import api


def test_repo_bootstrap_cli_exits_nonzero_when_repo_not_ready(monkeypatch):
    def fake_bootstrap(self, repository: str, *, visibility: str = "public", push: bool = True):
        return RepoBootstrapResult(
            repository=repository,
            created=False,
            pushed=False,
            message="GitHub authentication is required via gh, GH_TOKEN, or GITHUB_TOKEN",
        )

    monkeypatch.setattr(RepositoryBootstrapper, "bootstrap", fake_bootstrap)
    result = CliRunner().invoke(app, ["repo-bootstrap", "coden607/continuityos"])
    assert result.exit_code == 1
    assert '"created": false' in result.stdout


def test_api_execute_uses_continuity_config_when_set(tmp_path: Path, monkeypatch):
    config = tmp_path / "continuity.toml"
    config.write_text(
        f'''\n[app]\nname = "api-profile"\nprofile = "minimal"\n[runtime]\ncheckpoint_dir = "{tmp_path / 'checkpoints'}"\ntelemetry_path = "{tmp_path / 'routes.jsonl'}"\nmemory_path = "{tmp_path / 'memory.db'}"\n[[models]]\nid = "profile-echo"\nprovider = "dev"\nmodel = "profile-model"\ncapabilities = ["text"]\ncontext_window = 1000000\nmax_output_tokens = 1024\nquality = 0.3\nreliability = 1.0\ncost_per_million = 0.0\nlatency_ms = 0\nprivacy = "local"\n''',
        encoding="utf-8",
    )
    monkeypatch.setenv("CONTINUITY_CONFIG", str(config))
    response = TestClient(api).post("/execute", json={"task_id": "configured", "prompt": "hello", "capability": "text"})
    assert response.status_code == 200
    body = response.json()
    assert body["candidate_id"] == "profile-echo"
    assert body["model"] == "profile-model"
