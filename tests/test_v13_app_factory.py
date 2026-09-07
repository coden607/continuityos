import json
from pathlib import Path

from typer.testing import CliRunner

from continuityos.blueprint import load_blueprint
from continuityos.cli import app
from continuityos.generator import AppGenerator


def blueprint_text():
    return '''
[app]
name = "CaseCraft"
domain = "legal"
version = "0.1.0"
profile = "minimal"

[development]
method = "continuity-hybrid"
roles = ["platform-steward", "developer", "qa"]
architecture_gate = true
security_gate = true
eval_gate = true

[quality]
min_quality = 0.92
min_reliability = 0.95
prefer_zero_token = true
escalation = ["deterministic", "local_free", "economical", "premium", "council"]

[verification]
gates = ["compile", "tests", "typecheck", "security", "privacy", "architecture", "evals", "e2e", "accessibility", "performance", "pwa"]

[verification.performance_budgets]
lcp_ms = 2500
cls = 0.1
inp_ms = 200

[features]
pwa = true
api = true
voice = false
memory = true

[deployment]
targets = ["github"]
secrets = ["OPENAI_API_KEY"]
'''


def test_generator_from_blueprint_writes_managed_manifest(tmp_path: Path):
    bpfile = tmp_path / "bp.toml"; bpfile.write_text(blueprint_text())
    generated = AppGenerator(tmp_path / "out").create_from_blueprint(load_blueprint(bpfile))
    assert generated.blueprint_file.exists()
    manifest = json.loads(generated.manifest_file.read_text())
    assert "continuity.toml" in manifest["managed_paths"]
    assert "src" in manifest["owned_paths"]
    assert manifest["fingerprints"]["continuity.toml"]
    verify = json.loads(generated.verification_file.read_text())
    assert "performance" in verify["gates"]
    assert verify["performance_budgets"]["lcp_ms"] == 2500
    assert "OPENAI_API_KEY=" in generated.env_example.read_text()
    assert "sk-" not in generated.env_example.read_text()


def test_cli_blueprint_check(tmp_path: Path):
    bpfile = tmp_path / "bp.toml"; bpfile.write_text(blueprint_text())
    result = CliRunner().invoke(app, ["blueprint-check", str(bpfile)])
    assert result.exit_code == 0
    assert '"valid": true' in result.stdout.lower()


def test_cli_new_accepts_blueprint(tmp_path: Path):
    bpfile = tmp_path / "bp.toml"; bpfile.write_text(blueprint_text())
    result = CliRunner().invoke(app, ["new", "ignored", "--destination", str(tmp_path / "apps"), "--blueprint", str(bpfile)])
    assert result.exit_code == 0
    assert (tmp_path / "apps" / "casecraft" / ".continuity" / "manifest.json").exists()
