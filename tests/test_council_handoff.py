from continuityos.council import CouncilVote, MultiModelCouncil
from continuityos.handoff import HandoffAcknowledgement, verify_handoff
from continuityos.models import ContextCapsule


def capsule():
    return ContextCapsule(
        objective="finish app", current_task="route", user_requirements=["free-first"], hard_constraints=["never leak secrets"],
        decisions=[], completed_work=[], open_work=[], facts=[], artifacts=[], tool_state=[], citations=[], memory_refs=[], failed_approaches=[], current_plan=[],
        next_action="test", handoff_reason="context_pressure"
    )


def test_handoff_rejects_missing_constraint():
    ack = HandoffAcknowledgement(objective="finish app", current_task="route", next_action="test", acknowledged_requirements=["free-first"])
    result = verify_handoff(capsule(), ack)
    assert not result.accepted
    assert result.coverage < 1


def test_handoff_accepts_complete_acknowledgement():
    ack = HandoffAcknowledgement(objective="finish app", current_task="route", next_action="test", acknowledged_requirements=["free-first"], acknowledged_constraints=["never leak secrets"])
    assert verify_handoff(capsule(), ack).accepted


def test_council_uses_confidence_weighted_consensus():
    decision = MultiModelCouncil().decide([
        CouncilVote(agent="planner", proposal="A", confidence=.8, evidence=["x"]),
        CouncilVote(agent="critic", proposal="B", confidence=.6),
        CouncilVote(agent="verifier", proposal="A", confidence=.9, evidence=["y"]),
    ])
    assert decision.proposal == "A"
    assert decision.supporting_agents == ["planner", "verifier"]
    assert set(decision.evidence) == {"x", "y"}
