from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"


def test_container_build_workflow_exists():
    text = (WORKFLOWS / "container.yml").read_text()
    assert "docker/build-push-action" in text
    assert "push: false" in text


def test_pwa_cloudflare_deploy_is_manual_and_secret_gated():
    text = (WORKFLOWS / "deploy-pwa.yml").read_text()
    assert "workflow_dispatch" in text
    assert "CLOUDFLARE_API_TOKEN" in text
    assert "cloudflare/wrangler-action" in text


def test_release_workflow_uploads_build_artifacts():
    text = (WORKFLOWS / "release.yml").read_text()
    assert "actions/upload-artifact" in text
    assert "pip wheel" in text
