from pathlib import Path

from continuityos.checkpoints import CheckpointStore
from continuityos.models import ContextCapsule


def capsule(next_action='continue'):
    return ContextCapsule(objective='ship', current_task='build', user_requirements=[], hard_constraints=[], decisions=[], completed_work=[], open_work=[], facts=[], artifacts=[], tool_state=[], citations=[], memory_refs=[], failed_approaches=[], current_plan=[], next_action=next_action, handoff_reason='checkpoint')


def test_checkpoint_round_trip(tmp_path: Path):
    store = CheckpointStore(tmp_path / 'state.db')
    version = store.save('task-1', capsule())
    assert version == 1
    loaded = store.latest('task-1')
    assert loaded is not None
    assert loaded.next_action == 'continue'


def test_checkpoint_versions_are_monotonic(tmp_path: Path):
    store = CheckpointStore(tmp_path / 'state.db')
    assert store.save('task-1', capsule('a')) == 1
    assert store.save('task-1', capsule('b')) == 2
    assert store.latest('task-1').next_action == 'b'
