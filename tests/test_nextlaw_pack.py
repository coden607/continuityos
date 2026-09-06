from pathlib import Path
import json


def test_nextlaw_reference_pack_is_valid():
    root = Path('packs/nextlaw607')
    manifest = json.loads((root / 'pack.json').read_text())
    assert manifest['app']['name'] == 'NextLaw607'
    assert 'courtlistener' in manifest['mcp']
    assert manifest['continuity']['fail_closed_on_unverified_law'] is True
