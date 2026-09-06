from continuityos.guardrail_mesh import GuardrailMesh
from continuityos.guardrails import AllowReadOnlyPolicy


def test_guardrail_mesh_blocks_mutation_by_default():
    mesh = GuardrailMesh([AllowReadOnlyPolicy()])
    decision = mesh.evaluate('write:file', {'path': 'x'})
    assert not decision.allowed
    assert decision.requires_human_approval


def test_guardrail_mesh_allows_read():
    mesh = GuardrailMesh([AllowReadOnlyPolicy()])
    assert mesh.evaluate('read:file', {'path': 'x'}).allowed
