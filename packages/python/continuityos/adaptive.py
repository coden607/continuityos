from __future__ import annotations

from dataclasses import dataclass

from .models import ModelCandidate, TaskRequirements
from .telemetry import RoutingTelemetry


@dataclass(frozen=True)
class RoutingRecommendation:
    candidate_id: str
    score: float
    rationale: tuple[str, ...]


class RoutingLearner:
    """Learns routing preferences from observed outcomes without autonomously mutating code or policy."""

    def __init__(self, telemetry: RoutingTelemetry) -> None:
        self.telemetry = telemetry

    def recommend(self, candidates: list[ModelCandidate], requirements: TaskRequirements) -> list[RoutingRecommendation]:
        recs: list[RoutingRecommendation] = []
        for candidate in candidates:
            stats = self.telemetry.stats(candidate.id, requirements.task_type)
            score = candidate.quality * 0.35 + candidate.reliability * 0.25
            rationale = ["declared quality/reliability"]
            if stats.attempts:
                score += stats.success_rate * 0.30
                score += max(0.0, 0.10 - min(stats.avg_cost / 100.0, 0.10))
                rationale.append(f"{stats.attempts} observed attempts")
                rationale.append(f"{stats.success_rate:.0%} observed success")
            elif candidate.cost_per_million == 0:
                score += 0.05
                rationale.append("zero-cost exploration candidate")
            recs.append(RoutingRecommendation(candidate.id, round(score, 4), tuple(rationale)))
        return sorted(recs, key=lambda r: r.score, reverse=True)
