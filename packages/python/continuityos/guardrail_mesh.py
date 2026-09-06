from __future__ import annotations

from .guardrails import GuardrailPolicy
from .models import GuardrailDecision


class GuardrailMesh:
    def __init__(self, policies: list[GuardrailPolicy]) -> None:
        self.policies = policies

    def evaluate(self, action: str, payload: dict) -> GuardrailDecision:
        reasons: list[str] = []
        requires_approval = False
        for policy in self.policies:
            decision = policy.evaluate(action, payload)
            reasons.extend(decision.reasons)
            requires_approval = requires_approval or decision.requires_human_approval
            if not decision.allowed:
                return GuardrailDecision(allowed=False, reasons=reasons, requires_human_approval=requires_approval)
        return GuardrailDecision(allowed=True, reasons=reasons, requires_human_approval=requires_approval)
