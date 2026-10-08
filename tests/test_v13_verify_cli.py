import json
from pathlib import Path

from typer.testing import CliRunner

from continuityos.blueprint import load_blueprint
from continuityos.cli import app
from continuityos.generator import AppGenerator


def _blueprint() -> str:
    return '''
[app]
name = "VerifyApp"

[verification]
gates = ["tests", "typecheck"]

[verification.commands]
tests = "python -c 'print(1)'"
typecheck = "python -c 'print(2)'"
'''


def test_blueprint_verification_commands_are_preserved(tmp_path: Path):
    path = tmp_path / "bp.toml"
    path.write_text(_blueprint(), encoding="utf-8")
    bp = load_blueprint(path)
    assert bp.verification.commands["tests"].startswith("python -c")

    generated = AppGenerator(tmp_path / "apps").create_from_blueprint(bp)
    metadata = json.loads(generated.verification_file.read_text(encoding="utf-8"))
    assert metadata["commands"]["typecheck"].startswith("python -c")


def test_verify_cli_runs_declared_commands(tmp_path: Path):
    root = tmp_path / "app"
    (root / ".continuity").mkdir(parents=True)
    (root / ".continuity" / "verification.json").write_text(json.dumps({
        "gates": ["tests", "typecheck"],
        "commands": {
            "tests": "python -c \"print('tests ok')\"",
            "typecheck": "python -c \"print('types ok')\"",
        },
    }), encoding="utf-8")
    result = CliRunner().invoke(app, ["verify", str(root)])
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    assert payload["passed"] is True
    assert {item["status"] for item in payload["results"]} == {"passed"}


def test_verify_cli_fails_closed_for_missing_command(tmp_path: Path):
    root = tmp_path / "app"
    (root / ".continuity").mkdir(parents=True)
    (root / ".continuity" / "verification.json").write_text(json.dumps({
        "gates": ["tests", "security"],
        "commands": {"tests": "python -c \"print('ok')\""},
    }), encoding="utf-8")
    result = CliRunner().invoke(app, ["verify", str(root)])
    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    statuses = {item["gate"]: item["status"] for item in payload["results"]}
    assert statuses["tests"] == "passed"
    assert statuses["security"] == "missing"
