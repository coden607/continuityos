import json
from pathlib import Path

import continuityos
from continuityos.mcp import MCPServer
from continuityos.mcp_client import MCPClient

ROOT = Path(__file__).resolve().parents[1]


def test_release_version_is_synchronized():
    assert continuityos.__version__ == "1.2.1"
    assert 'version = "1.2.1"' in (ROOT / "pyproject.toml").read_text()
    assert json.loads((ROOT / "apps/web-pwa/package.json").read_text())["version"] == "1.2.1"
