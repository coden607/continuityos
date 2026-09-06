import json
from pathlib import Path

from typer.testing import CliRunner

from continuityos.cli import app


def _write(root: Path, metadata: dict, evidence: dict, *, add_provenance: bool = True):
    continuity = root / '.continuity'
    continuity.mkdir(parents=True)
    if add_provenance:
        evidence = {
            'revision': 'fixture-revision',
            'captured_at': '2026-09-06T19:00:00Z',
            'tool': 'test-browser-runner',
            **evidence,
        }
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


def _git_commit(root: Path) -> str:
    import subprocess
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "tests@example.invalid"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "ContinuityOS Tests"], cwd=root, check=True)
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(["git", "commit", "-qm", "fixture"], cwd=root, check=True)
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()


def test_browser_evidence_without_provenance_fails_closed(tmp_path: Path):
    root = tmp_path / "app"
    _write(root, {
        "gates": ["accessibility"],
        "commands": {},
    }, {
        "accessibility_passed": True,
    }, add_provenance=False)
    result = CliRunner().invoke(app, ["verify", str(root)])
    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert payload["results"][0]["status"] == "failed"


def test_browser_evidence_revision_must_match_checked_out_commit(tmp_path: Path):
    root = tmp_path / "app"
    _write(root, {
        "gates": ["accessibility"],
        "commands": {},
    }, {
        "revision": "deadbeef",
        "captured_at": "2026-09-06T19:00:00Z",
        "tool": "playwright+lighthouse",
        "accessibility_passed": True,
    })
    _git_commit(root)
    result = CliRunner().invoke(app, ["verify", str(root)])
    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert payload["results"][0]["status"] == "failed"
