from pathlib import Path


def test_browser_release_evidence_workflow_is_wired():
    workflow = Path('.github/workflows/browser-release-evidence.yml').read_text(encoding='utf-8')
    assert 'apps/web-pwa/scripts/browser-evidence.mjs' in workflow
    assert './scripts/verify-release.sh' in workflow
    assert 'actions/upload-artifact@v4' in workflow
    assert 'playwright install --with-deps chromium' in workflow


def test_browser_evidence_script_is_revision_bound_and_fail_closed():
    script = Path('apps/web-pwa/scripts/browser-evidence.mjs').read_text(encoding='utf-8')
    assert 'GITHUB_SHA' in script
    assert 'requires an exact revision' in script
    assert 'accessibility_passed' in script
    assert 'e2e_passed' in script
    assert 'pwa_passed' in script
    assert 'lcp_ms' in script
    assert 'cls' in script
    assert 'inp_ms' in script
    assert 'process.exitCode = 1' in script


def test_tag_release_is_blocked_on_browser_evidence():
    release = Path('.github/workflows/release.yml').read_text(encoding='utf-8')
    assert 'browser-evidence:' in release
    assert 'needs: browser-evidence' in release
    assert 'apps/web-pwa/scripts/browser-evidence.mjs' in release
    assert 'continuity verify .' in release
