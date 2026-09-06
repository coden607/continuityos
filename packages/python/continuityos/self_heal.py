from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .health import HealthRegistry, HealthState


@dataclass(frozen=True)
class HealthCheckResult:
    component: str
    healthy: bool
    detail: str = ""


@dataclass(frozen=True)
class HealResult:
    component: str
    attempted: bool
    recovered: bool
    detail: str = ""


class SelfHealingSupervisor:
    """Runs registered health probes and bounded recovery actions; never rewrites production code."""

    def __init__(self, registry: HealthRegistry, quarantine_after: int = 3) -> None:
        self.registry = registry
        self.quarantine_after = quarantine_after
        self._checks: dict[str, Callable[[], HealthCheckResult]] = {}
        self._healers: dict[str, Callable[[], bool]] = {}

    def register(self, component: str, check: Callable[[], HealthCheckResult], healer: Callable[[], bool] | None = None) -> None:
        self._checks[component] = check
        if healer is not None:
            self._healers[component] = healer

    def check(self, component: str) -> HealthCheckResult:
        result = self._checks[component]()
        if result.healthy:
            self.registry.mark_success(component)
        else:
            self.registry.mark_failure(component, quarantine_after=self.quarantine_after)
        return result

    def check_all(self) -> list[HealthCheckResult]:
        return [self.check(name) for name in sorted(self._checks)]

    def heal(self, component: str) -> HealResult:
        healer = self._healers.get(component)
        if healer is None:
            return HealResult(component, attempted=False, recovered=False, detail="no recovery action registered")
        self.registry.set(component, HealthState.RECOVERING)
        recovered = bool(healer())
        if recovered:
            self.registry.mark_success(component)
        else:
            self.registry.mark_failure(component, quarantine_after=self.quarantine_after)
        return HealResult(component, attempted=True, recovered=recovered)
