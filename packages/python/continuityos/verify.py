from __future__ import annotations

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Callable, Literal
import subprocess

from pydantic import BaseModel, Field


class VerificationGate(str, Enum):
    COMPILE = "compile"
    TESTS = "tests"
    TYPECHECK = "typecheck"
    LINT = "lint"
    SECURITY = "security"
    PRIVACY = "privacy"
    ARCHITECTURE = "architecture"
    EVALS = "evals"
    E2E = "e2e"
    ACCESSIBILITY = "accessibility"
    PERFORMANCE = "performance"
    PWA = "pwa"


class VerificationContract(BaseModel):
    gates: list[VerificationGate]


class GateResult(BaseModel):
    gate: VerificationGate
    status: Literal["passed", "failed", "missing"]
    detail: str = ""


class VerificationResult(BaseModel):
    results: list[GateResult] = Field(default_factory=list)

    @property
    def passed(self) -> bool:
        return bool(self.results) and all(item.status == "passed" for item in self.results)


GateRunner = Callable[[Path], bool]

class BrowserEvidence(BaseModel):
    revision: str | None = None
    captured_at: datetime | None = None
    tool: str | None = None
    e2e_passed: bool | None = None
    accessibility_passed: bool | None = None
    pwa_passed: bool | None = None
    performance: dict[str, float] = Field(default_factory=dict)


def _git_revision(root: Path) -> str | None:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None
    if completed.returncode != 0:
        return None
    revision = completed.stdout.strip()
    return revision or None


def browser_evidence_runners(root: str | Path, metadata: dict) -> dict[VerificationGate, GateRunner]:
    evidence_path = Path(root) / ".continuity" / "browser-evidence.json"
    if not evidence_path.is_file():
        return {}
    import json
    evidence = BrowserEvidence.model_validate(json.loads(evidence_path.read_text(encoding="utf-8")))
    root_path = Path(root)
    current_revision = _git_revision(root_path)
    provenance_valid = bool(
        evidence.revision
        and evidence.captured_at is not None
        and evidence.tool
        and (current_revision is None or evidence.revision == current_revision)
    )
    runners: dict[VerificationGate, GateRunner] = {}
    if evidence.e2e_passed is not None:
        runners[VerificationGate.E2E] = lambda path: provenance_valid and evidence.e2e_passed is True
    if evidence.accessibility_passed is not None:
        runners[VerificationGate.ACCESSIBILITY] = lambda path: provenance_valid and evidence.accessibility_passed is True
    if evidence.pwa_passed is not None:
        runners[VerificationGate.PWA] = lambda path: provenance_valid and evidence.pwa_passed is True
    budgets = metadata.get("performance_budgets") or {}
    if budgets:
        def performance_runner(path: Path) -> bool:
            if not provenance_valid:
                return False
            for name, limit in budgets.items():
                value = evidence.performance.get(name)
                if value is None or value > float(limit):
                    return False
            return True
        runners[VerificationGate.PERFORMANCE] = performance_runner
    return runners


class VerificationRunner:
    """Executes declared release gates and fails closed when a runner is unavailable."""

    def __init__(self, runners: dict[VerificationGate, GateRunner]) -> None:
        self.runners = dict(runners)

    def run(self, root: str | Path, contract: VerificationContract) -> VerificationResult:
        path = Path(root)
        results: list[GateResult] = []
        for gate in contract.gates:
            runner = self.runners.get(gate)
            if runner is None:
                results.append(GateResult(gate=gate, status="missing", detail="no runner registered"))
                continue
            try:
                passed = bool(runner(path))
            except Exception as exc:  # fail closed and retain evidence
                results.append(GateResult(gate=gate, status="failed", detail=f"{type(exc).__name__}: {exc}"))
            else:
                results.append(GateResult(gate=gate, status="passed" if passed else "failed"))
        return VerificationResult(results=results)
