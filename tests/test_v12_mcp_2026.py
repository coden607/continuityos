import json

from continuityos import __version__
from continuityos.mcp import MCPServer
from continuityos.mcp_client import MCPClient, MCP_PROTOCOL_VERSION


def test_mcp_uses_current_stateless_protocol_headers_and_client_meta(monkeypatch):
    captured = {}

    class Response:
        headers = {"Content-Type": "application/json"}
        status = 200
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self): return b'{"jsonrpc":"2.0","id":1,"result":{"content":[]}}'

    def fake_urlopen(request, timeout=0):
        captured["headers"] = dict(request.header_items())
        captured["payload"] = json.loads(request.data.decode())
        return Response()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    server = MCPServer(name="x", url="https://example.test/mcp")
    MCPClient().call_tool(server, "search", {"q": "otters"})

    lowered = {k.lower(): v for k, v in captured["headers"].items()}
    assert MCP_PROTOCOL_VERSION == "2026-07-28"
    assert lowered["mcp-protocol-version"] == MCP_PROTOCOL_VERSION
    assert lowered["mcp-method"] == "tools/call"
    assert lowered["mcp-name"] == "search"
    meta = captured["payload"]["params"]["_meta"]["io.modelcontextprotocol/clientInfo"]
    assert meta == {"name": "ContinuityOS", "version": __version__}


def test_discover_replaces_initialize_handshake(monkeypatch):
    client = MCPClient()
    called = {}
    def fake_call(server, method, params=None, request_id=1):
        called["method"] = method
        return {"result": {"capabilities": {}}}
    monkeypatch.setattr(client, "call", fake_call)
    result = client.discover(MCPServer(name="x", url="https://example.test/mcp"))
    assert called["method"] == "server/discover"
    assert result["result"]["capabilities"] == {}


def test_initialize_is_backward_compatibility_alias_for_discover(monkeypatch):
    client = MCPClient()
    monkeypatch.setattr(client, "discover", lambda server, request_id=1: {"result": {"compat": True}})
    result = client.initialize(MCPServer(name="x", url="https://example.test/mcp"))
    assert result["result"]["compat"] is True
