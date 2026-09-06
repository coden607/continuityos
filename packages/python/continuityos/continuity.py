from __future__ import annotations

from .models import ContextBudget, ContinuityAction


def evaluate_context(budget: ContextBudget) -> ContinuityAction:
    pressure = budget.pressure
    if pressure >= 0.98:
        return ContinuityAction.EMERGENCY
    if pressure >= 0.90:
        return ContinuityAction.HANDOFF
    if pressure >= 0.80:
        return ContinuityAction.CHECKPOINT
    if pressure >= 0.65:
        return ContinuityAction.COMPRESS
    return ContinuityAction.NORMAL
