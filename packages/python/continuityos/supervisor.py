from __future__ import annotations

from .health import HealthRegistry, HealthState


class HealthSupervisor:
    """Small reliability kernel for health reporting, quarantine and recovery."""

    def __init__(self, registry: HealthRegistry, quarantine_after: int = 3) -> None:
        self.registry = registry
        self.quarantine_after = quarantine_after

    def report(self, component: str, success: bool) -> HealthState:
        if success:
            self.registry.mark_success(component)
        else:
            self.registry.mark_failure(component, quarantine_after=self.quarantine_after)
        return self.registry.get(component).state

    def recover(self, component: str) -> None:
        self.registry.set(component, HealthState.RECOVERING)
