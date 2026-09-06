from continuityos.tooling import tool_statuses


def test_doctor_catalog_covers_approved_cli_stack():
    commands = {item.command for item in tool_statuses()}
    expected = {
        "git", "gh", "docker", "supabase", "wrangler", "vercel", "railway",
        "ollama", "sops", "age", "whisper-cli", "piper", "n8n", "node", "npm",
        "uv", "ruff", "gitleaks", "trivy", "playwright", "litellm", "dbos", "caddy",
    }
    assert expected.issubset(commands)
