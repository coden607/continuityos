from __future__ import annotations

from typing import Protocol

from .models import GuardrailDecision


class GuardrailPolicy(Protocol):
    def evaluate(self, action: str, payload: dict) -> GuardrailDecision: ...


class AllowReadOnlyPolicy:
    """Safe default example: reads pass, mutations require approval."""

    def evaluate(self, action: str, payload: dict) -> GuardrailDecision:
        if action.startswith(("read:", "search:", "inspect:")):
            return GuardrailDecision(allowed=True)
        return GuardrailDecision(
            allowed=False,
            reasons=["consequential or unknown action requires explicit authorization"],
            requires_human_approval=True,
        )
