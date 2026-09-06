from fastapi.testclient import TestClient
from typer.testing import CliRunner

from continuityos.cli import app
from services.api.main import api


client = TestClient(api)
runner = CliRunner()


def test_api_reports_platform_capabilities():
    response = client.get('/platform/capabilities')
    assert response.status_code == 200
    body = response.json()
    assert 'continuity' in body['features']
    assert 'mcp' in body['features']


def test_cli_version_and_plugins():
    version = runner.invoke(app, ['version'])
    assert version.exit_code == 0
    assert '1.2.1' in version.stdout
    plugins = runner.invoke(app, ['plugins'])
    assert plugins.exit_code == 0
    assert 'courtlistener' in plugins.stdout
