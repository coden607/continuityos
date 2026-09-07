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
        if req.privacy != "any":
            if _PRIVACY_RANK[candidate.privacy] < _PRIVACY_RANK[req.privacy]:
                return False
        return True

    def _score(self, candidate: ModelCandidate, req: TaskRequirements) -> tuple[float, list[str]]:
        reasons: list[str] = []
        score = candidate.quality * 35 + candidate.reliability * 30
        score += max(0.0, 20.0 - candidate.cost_per_million)
        score += max(0.0, 10.0 - min(candidate.latency_ms / 100.0, 10.0))
        score += {"local": 8.0, "private_cloud": 4.0, "cloud": 0.0}[candidate.privacy]
        if req.prefer_quality:
            score += candidate.quality * 15
            reasons.append("quality preference")
        if req.prefer_low_latency:
            score += max(0.0, 10.0 - min(candidate.latency_ms / 50.0, 10.0))
            reasons.append("latency preference")
        if candidate.cost_per_million == 0:
            reasons.append("zero marginal token cost")
        if candidate.privacy == "local":
            reasons.append("local privacy")
        if self.telemetry:
            stats = self.telemetry.stats(candidate.id, req.task_type)
            if stats.attempts:
                score += (stats.success_rate - 0.5) * 30
                reasons.append(f"observed success rate {stats.success_rate:.0%}")
        reasons.append("capabilities satisfied")
        reasons.append("context window satisfied")
        return score, reasons

    def route(self, req: TaskRequirements) -> RouteDecision:
        eligible = [candidate for candidate in self.candidates if self._eligible(candidate, req)]
        if not eligible:
            raise LookupError("no healthy candidate satisfies task requirements")
        ranked = [(candidate, *self._score(candidate, req)) for candidate in eligible]
        candidate, score, reasons = max(ranked, key=lambda row: row[1])
        return RouteDecision(candidate=candidate, score=round(score, 3), reasons=reasons)
