from __future__ import annotations

import shutil
from pydantic import BaseModel


class ToolStatus(BaseModel):
    name: str
    command: str
    installed: bool
    required: bool = False
    purpose: str


TOOL_CATALOG = [
    ("git", "git", True, "source control"),
    ("GitHub CLI", "gh", False, "repository, actions and secret sync"),
    ("Docker", "docker", False, "local containers"),
    ("Supabase CLI", "supabase", False, "database/auth/storage management"),
    ("Cloudflare Wrangler", "wrangler", False, "edge/PWA deployment and secrets"),
    ("Vercel CLI", "vercel", False, "optional web deployment"),
    ("Railway CLI", "railway", False, "optional service deployment"),
    ("Ollama", "ollama", False, "local model runtime"),
    ("SOPS", "sops", False, "encrypted secret files"),
    ("age", "age", False, "local secret encryption"),
    ("whisper.cpp", "whisper-cli", False, "local speech-to-text"),
    ("n8n", "n8n", False, "optional automation"),
    ("Piper", "piper", False, "local text-to-speech"),
    ("uv", "uv", False, "fast Python environment/package management"),
    ("Ruff", "ruff", False, "Python linting and formatting"),
    ("Gitleaks", "gitleaks", False, "secret scanning"),
    ("Trivy", "trivy", False, "container and dependency vulnerability scanning"),
    ("Playwright", "playwright", False, "browser automation and end-to-end testing"),
    ("LiteLLM", "litellm", False, "multi-provider model gateway"),
    ("DBOS", "dbos", False, "durable workflow execution"),
    ("Caddy", "caddy", False, "local reverse proxy and TLS"),
    ("Node.js", "node", False, "PWA tooling"),
    ("npm", "npm", False, "PWA packages"),
]


def tool_statuses() -> list[ToolStatus]:
    return [ToolStatus(name=n, command=c, installed=shutil.which(c) is not None, required=r, purpose=p) for n, c, r, p in TOOL_CATALOG]
