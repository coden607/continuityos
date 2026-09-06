import json
from pathlib import Path

from typer.testing import CliRunner

from continuityos.cli import app


def _write(root: Path, metadata: dict, evidence: dict):
    continuity = root / '.continuity'
    continuity.mkdir(parents=True)
    (continuity / 'verification.json').write_text(json.dumps(metadata), encoding='utf-8')
    (continuity / 'browser-evidence.json').write_text(json.dumps(evidence), encoding='utf-8')


def test_verify_cli_accepts_accessibility_and_performance_evidence(tmp_path: Path):
    root = tmp_path / 'app'
    _write(root, {
        'gates': ['accessibility', 'performance'],
        'commands': {},
        'performance_budgets': {'lcp_ms': 2500, 'cls': 0.1, 'inp_ms': 200},
    }, {
        'accessibility_passed': True,
        'performance': {'lcp_ms': 1800, 'cls': 0.03, 'inp_ms': 120},
    })
    result = CliRunner().invoke(app, ['verify', str(root)])
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    assert payload['passed'] is True


def test_verify_cli_fails_performance_budget_overrun(tmp_path: Path):
    root = tmp_path / 'app'
    _write(root, {
        'gates': ['performance'],
        'commands': {},
        'performance_budgets': {'lcp_ms': 2500, 'cls': 0.1, 'inp_ms': 200},
    }, {
        'accessibility_passed': True,
        'performance': {'lcp_ms': 3200, 'cls': 0.03, 'inp_ms': 120},
    })
    result = CliRunner().invoke(app, ['verify', str(root)])
    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert payload['results'][0]['status'] == 'failed'


def test_verify_cli_missing_browser_evidence_stays_fail_closed(tmp_path: Path):
    root = tmp_path / 'app'
    (root / '.continuity').mkdir(parents=True)
    (root / '.continuity' / 'verification.json').write_text(json.dumps({'gates':['accessibility'], 'commands':{}}), encoding='utf-8')
    result = CliRunner().invoke(app, ['verify', str(root)])
    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert payload['results'][0]['status'] == 'missing'
