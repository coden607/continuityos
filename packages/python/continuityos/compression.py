from __future__ import annotations

from typing import Protocol

from .models import ContextCapsule


class TextCompressor(Protocol):
    def __call__(self, text: str, target_chars: int) -> str: ...


def deterministic_compress(text: str, target_chars: int) -> str:
    if target_chars <= 0:
        return ""
    text = " ".join(text.split())
    if len(text) <= target_chars:
        return text
    if target_chars < 8:
        return text[:target_chars]
    return text[: target_chars - 1].rstrip() + "…"


def compress_capsule(
    capsule: ContextCapsule,
    *,
    target_chars: int = 8000,
    compressor: TextCompressor | None = None,
) -> ContextCapsule:
    """Compress low-priority text while preserving requirements, constraints and next action verbatim."""
    fn = compressor or deterministic_compress
    critical = (
        len(capsule.objective)
        + len(capsule.current_task)
        + len(capsule.next_action)
        + sum(map(len, capsule.user_requirements))
        + sum(map(len, capsule.hard_constraints))
    )
    remaining = max(0, target_chars - critical)
    buckets = 6
    each = max(64, remaining // buckets) if remaining else 64

    def compact(items: list[str]) -> list[str]:
        if not items:
            return []
        joined = "\n".join(items)
        return [fn(joined, each)]

    return capsule.model_copy(update={
        "decisions": compact(capsule.decisions),
        "completed_work": compact(capsule.completed_work),
        "open_work": compact(capsule.open_work),
        "facts": compact(capsule.facts),
        "failed_approaches": compact(capsule.failed_approaches),
        "current_plan": compact(capsule.current_plan),
    })
