from pathlib import Path

from typer.testing import CliRunner

from continuityos.cli import app


def write_config(path: Path):
    path.write_text('''
[app]
name = "ops-demo"
profile = "minimal"
[runtime]
checkpoint_dir = ".continuity/checkpoints"
telemetry_path = ".continuity/routes.jsonl"
memory_path = ".continuity/memory.db"
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


def test_config_check_reports_valid_profile(tmp_path: Path):
    path = tmp_path / "continuity.toml"
    write_config(path)
    result = CliRunner().invoke(app, ["config-check", str(path)])
    assert result.exit_code == 0
    assert '"app": "ops-demo"' in result.stdout
    assert '"models": 1' in result.stdout


def test_packs_command_discovers_reference_pack():
    root = Path(__file__).resolve().parents[1] / "packs"
    result = CliRunner().invoke(app, ["packs", "--root", str(root)])
    assert result.exit_code == 0
    assert "nextlaw607" in result.stdout
