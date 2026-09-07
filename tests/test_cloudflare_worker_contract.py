import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_cloudflare_fastapi_worker_contract() -> None:
    worker = (ROOT / "services/api/cloudflare_worker.py").read_text()
    assert "from workers import asgi" in worker
    assert "from services.api.main import api" in worker
    assert "Default = asgi.entrypoint(api)" in worker

    config = json.loads((ROOT / "wrangler.api.jsonc").read_text())
    assert config["name"] == "continuityos-api"
    assert config["main"] == "services/api/cloudflare_worker.py"
    assert "python_workers" in config["compatibility_flags"]
    assert config["compatibility_date"] == "2026-09-06"


def test_cloudflare_api_deploy_is_manual_only() -> None:
    workflow = (ROOT / ".github/workflows/deploy-api.yml").read_text()
    assert "workflow_dispatch:" in workflow
    assert "push:" not in workflow
    assert "cp wrangler.api.jsonc wrangler.jsonc" in workflow
    assert "pywrangler deploy --dry-run" in workflow
    assert "github.ref == 'refs/heads/main'" in workflow
