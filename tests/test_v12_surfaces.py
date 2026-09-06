from fastapi.testclient import TestClient
from typer.testing import CliRunner

from continuityos.cli import app
from continuityos.dev_provider import DevEchoProvider
from continuityos.providers import ProviderRequest
from services.api.main import api


def test_dev_echo_provider_is_zero_dependency():
    p = DevEchoProvider()
    r = p.complete(ProviderRequest(model="dev-echo", messages=[{"role":"user","content":"ping"}]))
    assert r.text == "ping"
    assert r.cost == 0


def test_cli_execute_runs_end_to_end():
    result = CliRunner().invoke(app, ["execute", "hello"])
    assert result.exit_code == 0
    assert '"text": "hello"' in result.stdout
    assert '"candidate_id": "dev-echo"' in result.stdout


def test_api_execute_runs_end_to_end():
    client = TestClient(api)
    response = client.post("/execute", json={"task_id":"api1","prompt":"hello","capability":"text"})
    assert response.status_code == 200
    data = response.json()
    assert data["text"] == "hello"
    assert data["candidate_id"] == "dev-echo"
