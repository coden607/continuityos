from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_gitignore_covers_common_secret_files():
    text = (ROOT / ".gitignore").read_text()
    for pattern in [".env", "*.pem", "*.key", ".secrets/"]:
        assert pattern in text


def test_pwa_manifest_exists():
    assert (ROOT / "apps/web-pwa/public/manifest.webmanifest").exists()
