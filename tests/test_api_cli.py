from fastapi.testclient import TestClient
from typer.testing import CliRunner

from continuityos.cli import app
from services.api.main import api


def test_health_endpoint():
    client = TestClient(api)
    response = client.get('/status/health')
    assert response.status_code == 200
    assert response.json()['status'] == 'healthy'


def test_route_preview():
    client = TestClient(api)
    response = client.post('/route/preview', json={'capabilities': ['text'], 'context_needed': 1000, 'privacy': 'local'})
    assert response.status_code == 200
    assert response.json()['candidate']['id'] == 'local-default'


def test_cli_doctor():
    result = CliRunner().invoke(app, ['doctor'])
    assert result.exit_code == 0
    assert 'ContinuityOS' in result.stdout
