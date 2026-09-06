from continuityos.continuity import evaluate_context
from continuityos.models import ContextBudget, ContinuityAction, ContextCapsule


def test_context_thresholds():
    assert evaluate_context(ContextBudget(limit=1000, used=500, reserve=0)) == ContinuityAction.NORMAL
    assert evaluate_context(ContextBudget(limit=1000, used=700, reserve=0)) == ContinuityAction.COMPRESS
    assert evaluate_context(ContextBudget(limit=1000, used=850, reserve=0)) == ContinuityAction.CHECKPOINT
    assert evaluate_context(ContextBudget(limit=1000, used=920, reserve=0)) == ContinuityAction.HANDOFF


def test_context_capsule_requires_next_action():
    capsule = ContextCapsule(
        objective="ship",
        current_task="route",
        user_requirements=[], hard_constraints=[], decisions=[], completed_work=[],
        open_work=[], facts=[], artifacts=[], tool_state=[], citations=[], memory_refs=[],
        failed_approaches=[], current_plan=[], next_action="test", handoff_reason="context_pressure",
    )
    assert capsule.next_action == "test"
