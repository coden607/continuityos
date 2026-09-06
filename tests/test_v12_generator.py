from pathlib import Path

from continuityos.generator import AppGenerator
from continuityos.config import load_config


def test_generated_app_is_immediately_runnable_with_zero_cost_profile(tmp_path: Path):
    generated = AppGenerator(tmp_path).create("Ready App", template="generic")
    config_path = generated.root / "continuity.toml"
    assert config_path.exists()
    cfg = load_config(config_path)
    assert cfg.app.name == "Ready App"
    assert cfg.models[0].provider == "dev"
    assert cfg.models[0].cost_per_million == 0
    ignore = (generated.root / ".gitignore").read_text()
    assert ".continuity/" in ignore
    assert ".env.*" in ignore


def test_generated_readme_contains_first_run_commands(tmp_path: Path):
    generated = AppGenerator(tmp_path).create("Ready App")
    readme = (generated.root / "README.md").read_text()
    assert "continuity config-check continuity.toml" in readme
    assert 'continuity execute "hello" --config continuity.toml' in readme
