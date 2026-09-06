from pathlib import Path

from continuityos.config import ContinuityConfig, load_config
from continuityos.pack_loader import PackLoader
from continuityos.runtime_factory import build_runtime


def test_load_config_from_toml(tmp_path: Path):
    path = tmp_path / "continuity.toml"
    path.write_text('''
[app]
name = "demo"
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
    cfg = load_config(path)
    assert cfg.app.name == "demo"
    assert cfg.models[0].id == "dev-echo"
    assert cfg.models[0].capabilities == {"text"}


def test_pack_loader_discovers_pack_json(tmp_path: Path):
    root = tmp_path / "packs" / "legal"
    root.mkdir(parents=True)
    (root / "pack.json").write_text('{"name":"legal","version":"1.0","skills":["cite"],"mcp":[],"agents":[],"guardrails":[]}')
    packs = PackLoader(tmp_path / "packs").discover()
    assert [p.name for p in packs] == ["legal"]
    assert packs[0].skills == ["cite"]


def test_runtime_factory_builds_zero_cost_profile(tmp_path: Path):
    cfg = ContinuityConfig.model_validate({
        "app": {"name": "demo", "profile": "minimal"},
        "runtime": {"checkpoint_dir": str(tmp_path / "c"), "telemetry_path": str(tmp_path / "r.jsonl"), "memory_path": str(tmp_path / "m.db")},
        "models": [{"id":"dev-echo","provider":"dev","capabilities":["text"],"context_window":1000000,"quality":0.1,"reliability":1.0,"cost_per_million":0,"latency_ms":0,"privacy":"local"}],
    })
    runtime = build_runtime(cfg)
    assert runtime.candidates[0].provider == "dev"
    assert runtime.fleet.available() == ["dev"]
