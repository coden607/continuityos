from __future__ import annotations

from .health import HealthRegistry
from .models import ModelCandidate, RouteDecision, TaskRequirements
from .telemetry import RoutingTelemetry


_PRIVACY_RANK = {"local": 3, "private_cloud": 2, "cloud": 1}


class Router:
    def __init__(self, candidates: list[ModelCandidate], health: HealthRegistry, telemetry: RoutingTelemetry | None = None) -> None:
        self.candidates = candidates
        self.health = health
        self.telemetry = telemetry

    def _eligible(self, candidate: ModelCandidate, req: TaskRequirements) -> bool:
        if not req.capabilities.issubset(candidate.capabilities):
            return False
        if candidate.context_window < req.context_needed:
            return False
        if not self.health.routable(candidate.id):
            return False
        if req.max_cost_per_million is not None and candidate.cost_per_million > req.max_cost_per_million:
            return False
        if req.privacy != "any" and _PRIVACY_RANK[candidate.privacy] < _PRIVACY_RANK[req.privacy]:
            return False
        return True

    def _score(self, candidate: ModelCandidate, req: TaskRequirements) -> tuple[float, list[str]]:
        score = 0.0
        reasons: list[str] = []
        score += candidate.quality * (45 if req.prefer_quality else 30)
        score += candidate.reliability * 30
        score += max(0.0, 20.0 - candidate.cost_per_million)
        score += max(0.0, 15.0 - min(candidate.latency_ms / 100.0, 15.0))
        score += {"local": 10.0, "private_cloud": 5.0, "cloud": 0.0}[candidate.privacy]
        if candidate.cost_per_million == 0:
            score += 15
            reasons.append("zero marginal token cost")
        if req.prefer_low_latency:
            score += max(0.0, 10.0 - min(candidate.latency_ms / 50.0, 10.0))
            reasons.append("latency preference")
        if candidate.privacy == "local":
            reasons.append("local privacy")
        if self.telemetry:
            stats = self.telemetry.stats(candidate.id, req.task_type)
            if stats.attempts:
                score += stats.success_rate * 20
                reasons.append(f"{stats.success_rate:.0%} observed success")
        return score, reasons

    def route(self, req: TaskRequirements) -> RouteDecision:
        eligible = [c for c in self.candidates if self._eligible(c, req)]
        if not eligible:
            raise LookupError("no healthy candidate satisfies route requirements")
        ranked = [(candidate, *self._score(candidate, req)) for candidate in eligible]
        candidate, score, reasons = max(ranked, key=lambda row: row[1])
        return RouteDecision(candidate=candidate, score=round(score, 3), reasons=reasons)
