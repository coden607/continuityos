from pathlib import Path

import pytest

from continuityos.entitlements import Entitlement, EntitlementLedger, EntitlementSource
from continuityos.privacy import DiagnosticPolicy, TelemetryFirewall
from continuityos.verify import VerificationContract, VerificationGate, VerificationRunner


def test_telemetry_firewall_is_allowlist_and_redacts_secrets():
    fw = TelemetryFirewall(DiagnosticPolicy(
        allowed_fields={"event", "module", "error_code"},
        forbidden_terms={"secret", "password", "token"},
    ))
    result = fw.sanitize({
        "event": "api_failed",
        "module": "research",
        "error_code": "TIMEOUT",
        "case_text": "I was arrested",
        "token": "sk-secret",
    })
    assert result == {"event": "api_failed", "module": "research", "error_code": "TIMEOUT"}


def test_telemetry_firewall_blocks_nested_content_and_pii_keys():
    fw = TelemetryFirewall(DiagnosticPolicy(allowed_fields={"event", "metadata"}))
    result = fw.sanitize({"event": "error", "metadata": {"email": "x@y.com", "duration_ms": 12}})
    assert result == {"event": "error", "metadata": {"duration_ms": 12}}


def test_founder_lifetime_entitlement_cannot_be_revoked():
    ledger = EntitlementLedger()
    grant = Entitlement.founder_lifetime("user-1")
    ledger.grant(grant)
    with pytest.raises(PermissionError):
        ledger.revoke(grant.id)
    assert ledger.active_for("user-1", "premium")


def test_normal_entitlement_can_be_revoked():
    ledger = EntitlementLedger()
    grant = Entitlement(subject_id="user-2", tier="premium", source=EntitlementSource.PROMO, revocable=True)
    ledger.grant(grant)
    ledger.revoke(grant.id)
    assert not ledger.active_for("user-2", "premium")


def test_verification_runner_executes_required_gates(tmp_path: Path):
    calls = []
    runner = VerificationRunner({
        VerificationGate.COMPILE: lambda root: calls.append("compile") or True,
        VerificationGate.TESTS: lambda root: calls.append("tests") or True,
    })
    result = runner.run(tmp_path, VerificationContract(gates=[VerificationGate.COMPILE, VerificationGate.TESTS]))
    assert result.passed
    assert calls == ["compile", "tests"]


def test_verification_runner_fails_closed_for_missing_gate(tmp_path: Path):
    runner = VerificationRunner({})
    result = runner.run(tmp_path, VerificationContract(gates=[VerificationGate.SECURITY]))
    assert not result.passed
    assert result.results[0].status == "missing"
