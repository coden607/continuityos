from __future__ import annotations

from collections import defaultdict

from pydantic import BaseModel, Field


class CouncilVote(BaseModel):
    agent: str
    proposal: str
    confidence: float = Field(ge=0, le=1)
    evidence: list[str] = []
    concerns: list[str] = []


class CouncilDecision(BaseModel):
    proposal: str
    score: float
    supporting_agents: list[str]
    evidence: list[str]
    dissent: list[str]


class MultiModelCouncil:
    """Model-agnostic arbitration. Agents submit typed votes; no model gets implicit authority."""

    def decide(self, votes: list[CouncilVote]) -> CouncilDecision:
        if not votes:
            raise ValueError("at least one council vote is required")
        scores: dict[str, float] = defaultdict(float)
        supporters: dict[str, list[str]] = defaultdict(list)
        evidence: dict[str, list[str]] = defaultdict(list)
        concerns: dict[str, list[str]] = defaultdict(list)
        for vote in votes:
            scores[vote.proposal] += vote.confidence
            supporters[vote.proposal].append(vote.agent)
            evidence[vote.proposal].extend(vote.evidence)
            concerns[vote.proposal].extend(vote.concerns)
        winner = max(scores, key=scores.get)
        dissent = [f"{v.agent}: {v.proposal}" for v in votes if v.proposal != winner]
        return CouncilDecision(
            proposal=winner,
            score=round(scores[winner], 4),
            supporting_agents=supporters[winner],
            evidence=list(dict.fromkeys(evidence[winner])),
            dissent=dissent + concerns[winner],
        )
