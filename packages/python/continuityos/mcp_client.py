from __future__ import annotations

import json
import os
import urllib.request
from typing import Any

from . import __version__
from .mcp import MCPServer


MCP_PROTOCOL_VERSION = "2026-07-28"
LEGACY_MCP_PROTOCOL_VERSION = "2025-11-25"


class MCPError(RuntimeError):
    def __init__(self, code: int, message: str, data: Any | None = None) -> None:
        super().__init__(f"MCP JSON-RPC error {code}: {message}")
        self.code = code
        self.message = message
        self.data = data


def _validate_rpc(payload: dict[str, Any]) -> dict[str, Any]:
    error = payload.get("error")
    if isinstance(error, dict):
        raise MCPError(int(error.get("code", -32000)), str(error.get("message", "unknown error")), error.get("data"))
    return payload


class MCPClient:
    """MCP 2026-07-28 stateless Streamable HTTP client with legacy response compatibility."""

    def __init__(self, timeout: float = 30.0, protocol_version: str = MCP_PROTOCOL_VERSION) -> None:
        self.timeout = timeout
        self.protocol_version = protocol_version

    @staticmethod
    def _client_meta(params: dict[str, Any] | None = None) -> dict[str, Any]:
        merged = dict(params or {})
        meta = dict(merged.get("_meta") or {})
        meta.setdefault("io.modelcontextprotocol/clientInfo", {"name": "ContinuityOS", "version": __version__})
        merged["_meta"] = meta
        return merged

    def call(self, server: MCPServer, method: str, params: dict[str, Any] | None = None, request_id: int = 1) -> dict[str, Any]:
        if server.transport != "streamable_http":
            raise NotImplementedError(f"transport {server.transport} requires a transport adapter")

        rpc_params = self._client_meta(params)
        payload = json.dumps({"jsonrpc": "2.0", "id": request_id, "method": method, "params": rpc_params}).encode()
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "MCP-Protocol-Version": self.protocol_version,
            "Mcp-Method": method,
        }
        name = rpc_params.get("name")
        if isinstance(name, str) and name:
            headers["Mcp-Name"] = name
        if server.auth_env:
            token = os.getenv(server.auth_env)
            if not token:
                raise RuntimeError(f"missing MCP credential environment variable: {server.auth_env}")
            headers["Authorization"] = token if token.lower().startswith(("bearer ", "token ")) else f"Bearer {token}"

        request = urllib.request.Request(server.url, data=payload, headers=headers, method="POST")
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            content_type = response.headers.get("Content-Type", "")
            body = response.read().decode("utf-8")

        if "text/event-stream" in content_type:
            events: list[dict[str, Any]] = []
            data_lines: list[str] = []
            for line in body.splitlines():
                if not line:
                    if data_lines:
                        events.append(json.loads("\n".join(data_lines)))
                        data_lines = []
                    continue
                if line.startswith("data:"):
                    data_lines.append(line[5:].strip())
            if data_lines:
                events.append(json.loads("\n".join(data_lines)))
            if not events:
                raise RuntimeError("MCP server returned an empty event stream")
            return _validate_rpc(events[-1])
        return _validate_rpc(json.loads(body))

    def discover(self, server: MCPServer, request_id: int = 1) -> dict[str, Any]:
        return self.call(server, "server/discover", {}, request_id=request_id)

    def initialize(self, server: MCPServer, request_id: int = 1) -> dict[str, Any]:
        """Backward-compatible API name; current MCP uses server/discover rather than a handshake."""
        return self.discover(server, request_id=request_id)

    def legacy_initialize(self, server: MCPServer, request_id: int = 1) -> dict[str, Any]:
        """Explicit compatibility path for pre-2026 MCP servers."""
        previous = self.protocol_version
        try:
            self.protocol_version = LEGACY_MCP_PROTOCOL_VERSION
            return self.call(
                server,
                "initialize",
                {
                    "protocolVersion": LEGACY_MCP_PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": {"name": "ContinuityOS", "version": __version__},
                },
                request_id=request_id,
            )
        finally:
            self.protocol_version = previous

    def list_tools(self, server: MCPServer, request_id: int = 2) -> list[dict[str, Any]]:
        response = self.call(server, "tools/list", {}, request_id=request_id)
        result = response.get("result", {})
        return list(result.get("tools", []))

    def call_tool(self, server: MCPServer, name: str, arguments: dict[str, Any] | None = None, request_id: int = 3) -> dict[str, Any]:
        return self.call(server, "tools/call", {"name": name, "arguments": arguments or {}}, request_id=request_id)
