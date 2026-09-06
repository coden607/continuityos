import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PWA = ROOT / "apps" / "web-pwa"


def test_minimal_pwa_build_is_bootable_without_node_modules():
    subprocess.run(["npm", "run", "build"], cwd=PWA, check=True, capture_output=True, text=True)
    dist = PWA / "dist"
    html = (dist / "index.html").read_text()
    assert "/src/main.tsx" not in html
    assert "app.js" in html
    assert (dist / "app.js").exists()
    assert (dist / "service-worker.js").exists()
    assert (dist / "styles.css").exists()


def test_pwa_runtime_console_calls_continuity_api():
    source = (PWA / "src" / "app.js").read_text()
    assert "/status/health" in source
    assert "/execute" in source
    assert "serviceWorker.register" in source
