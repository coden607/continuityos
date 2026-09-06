from __future__ import annotations

from enum import Enum
from time import time

from pydantic import BaseModel


class HealthState(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    QUARANTINED = "quarantined"
    RECOVERING = "recovering"


class HealthRecord(BaseModel):
    state: HealthState = HealthState.HEALTHY
    failure_count: int = 0
    last_success: float | None = None
    last_failure: float | None = None


class HealthRegistry:
    def __init__(self) -> None:
        self._records: dict[str, HealthRecord] = {}

    def get(self, key: str) -> HealthRecord:
        return self._records.get(key, HealthRecord())

    def set(self, key: str, state: HealthState) -> None:
        record = self.get(key).model_copy()
        record.state = state
        self._records[key] = record

    def mark_success(self, key: str) -> None:
        record = self.get(key).model_copy()
        record.state = HealthState.HEALTHY
        record.failure_count = 0
        record.last_success = time()
        self._records[key] = record

    def mark_failure(self, key: str, quarantine_after: int = 3) -> None:
        record = self.get(key).model_copy()
        record.failure_count += 1
        record.last_failure = time()
        record.state = HealthState.QUARANTINED if record.failure_count >= quarantine_after else HealthState.DEGRADED
        self._records[key] = record

    def routable(self, key: str) -> bool:
        return self.get(key).state not in {HealthState.UNHEALTHY, HealthState.QUARANTINED}

    def snapshot(self) -> dict[str, dict]:
        return {key: value.model_dump(mode="json") for key, value in self._records.items()}
