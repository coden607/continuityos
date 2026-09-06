from continuityos.health import HealthRegistry, HealthState
from continuityos.supervisor import HealthSupervisor


def test_supervisor_quarantines_after_repeated_failures():
    health = HealthRegistry()
    supervisor = HealthSupervisor(health, quarantine_after=2)
    supervisor.report('provider:x', False)
    assert health.get('provider:x').state == HealthState.DEGRADED
    supervisor.report('provider:x', False)
    assert health.get('provider:x').state == HealthState.QUARANTINED


def test_supervisor_can_recover_component():
    health = HealthRegistry()
    supervisor = HealthSupervisor(health)
    health.set('provider:x', HealthState.QUARANTINED)
    supervisor.recover('provider:x')
    assert health.get('provider:x').state == HealthState.RECOVERING
    supervisor.report('provider:x', True)
    assert health.get('provider:x').state == HealthState.HEALTHY
