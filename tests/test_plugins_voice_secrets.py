import os
from pathlib import Path

from continuityos.models import Capability
from continuityos.plugins import PluginManifest, PluginRegistry
from continuityos.secrets import SecretManager
from continuityos.voice import LocalWhisperAdapter, VoiceRouter


def test_plugin_registry_resolves_capability():
    registry = PluginRegistry()
    registry.register(PluginManifest(name='courtlistener', version='1', capabilities={Capability.MCP}, kind='mcp'))
    assert registry.resolve(Capability.MCP)[0].name == 'courtlistener'


def test_secret_manager_writes_private_env(tmp_path: Path):
    manager = SecretManager(tmp_path)
    path = manager.set('TEST_KEY', 'secret-value')
    assert path.name == '.env.local'
    assert 'secret-value' in path.read_text()
    assert oct(path.stat().st_mode & 0o777) == '0o600'


def test_voice_router_uses_local_whisper_when_available(monkeypatch):
    monkeypatch.setattr(LocalWhisperAdapter, 'available', lambda self: True)
    router = VoiceRouter([LocalWhisperAdapter(command='whisper-cli')])
    assert router.select_stt(require_local=True).name == 'whisper.cpp'
