from __future__ import annotations

from pydantic import BaseModel, Field

from .models import ContextCapsule


class HandoffAcknowledgement(BaseModel):
    objective: str
    current_task: str
    next_action: str
    acknowledged_constraints: list[str] = []
    acknowledged_requirements: list[str] = []


class HandoffVerification(BaseModel):
    accepted: bool
    missing: list[str] = []
    conflicts: list[str] = []
    coverage: float = Field(ge=0, le=1)


def verify_handoff(capsule: ContextCapsule, acknowledgement: HandoffAcknowledgement) -> HandoffVerification:
    missing: list[str] = []
    conflicts: list[str] = []
    checks = 3 + len(capsule.hard_constraints) + len(capsule.user_requirements)
    matched = 0

    for field in ("objective", "current_task", "next_action"):
        expected = getattr(capsule, field).strip()
        actual = getattr(acknowledgement, field).strip()
        if expected == actual:
            matched += 1
        else:
            conflicts.append(field)

    for constraint in capsule.hard_constraints:
        if constraint in acknowledgement.acknowledged_constraints:
            matched += 1
        else:
            missing.append(f"constraint:{constraint}")
    for requirement in capsule.user_requirements:
        if requirement in acknowledgement.acknowledged_requirements:
            matched += 1
        else:
            missing.append(f"requirement:{requirement}")

    coverage = matched / checks if checks else 1.0
    return HandoffVerification(accepted=not missing and not conflicts, missing=missing, conflicts=conflicts, coverage=round(coverage, 4))
