from continuityos.agent_bus import AgentBus, AgentMessage


def test_agent_bus_delivers_typed_message():
    bus = AgentBus()
    message = AgentMessage(sender="planner", recipient="critic", task_id="t1", type="evidence_bundle", payload={"claims": []})
    bus.publish(message)
    assert bus.receive("critic")[0].task_id == "t1"
