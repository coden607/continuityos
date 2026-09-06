from pathlib import Path

from typer.testing import CliRunner

from continuityos.cli import app

ROOT = Path(__file__).resolve().parents[1]


def test_runtime_state_directory_is_gitignored():
    assert ".continuity/" in (ROOT / ".gitignore").read_text()


def test_example_runtime_profile_exists_and_is_secret_free():
    text = (ROOT / "continuity.toml.example").read_text()
    assert 'provider = "dev"' in text
    assert "API_KEY=" not in text
    assert "TOKEN=" not in text


def test_cli_execute_can_load_runtime_profile(tmp_path: Path):
    config = tmp_path / "continuity.toml"
    config.write_text('''
[app]
name = "demo"
profile = "minimal"
[runtime]
checkpoint_dir = "''' + str(tmp_path / 'checkpoints') + '''"
telemetry_path = "''' + str(tmp_path / 'routes.jsonl') + '''"
memory_path = "''' + str(tmp_path / 'memory.db') + '''"
[[models]]
id = "dev-echo"
provider = "dev"
capabilities = ["text"]
context_window = 1000000
quality = 0.1
reliability = 1.0
cost_per_million = 0.0
latency_ms = 0
privacy = "local"
''')
    result = CliRunner().invoke(app, ["execute", "hello-config", "--config", str(config)])
    assert result.exit_code == 0
    assert '"text": "hello-config"' in result.stdout


def test_container_scaffolding_exists():
    assert (ROOT / "Dockerfile").exists()
    assert (ROOT / "compose.yaml").exists()
    assert (ROOT / ".dockerignore").exists()
