from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, field_validator


class MCPServer(BaseModel):
    name: str
    url: str

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        if not value.startswith(("https://", "http://")):
            raise ValueError("MCP URL must use HTTP(S)")
        return value
    transport: Literal["streamable_http", "stdio", "sse"] = "streamable_http"
    auth_env: str | None = None
    enabled: bool = True


class MCPRegistry:
    def __init__(self) -> None:
        self._servers: dict[str, MCPServer] = {}

    def register(self, server: MCPServer) -> None:
        self._servers[server.name] = server

    def get(self, name: str) -> MCPServer:
        try:
            return self._servers[name]
        except KeyError as exc:
            raise LookupError(name) from exc

    def enabled(self) -> list[MCPServer]:
        return [server for server in self._servers.values() if server.enabled]
