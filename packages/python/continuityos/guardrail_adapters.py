from __future__ import annotations

from typing import Any

from .models import GuardrailDecision


class NeMoGuardrailsAdapter:
    """Adapter around an injected NeMo rails instance; keeps NeMo optional and domain policies composable."""

    def __init__(self, rails: Any) -> None:
        self.rails = rails

    async def evaluate_text(self, text: str) -> GuardrailDecision:
        try:
            response = await self.rails.generate_async(messages=[{"role": "user", "content": text}])
        except Exception as exc:
            return GuardrailDecision(allowed=False, reasons=[f"guardrail failure: {exc}"])
        content = response.get("content", "") if isinstance(response, dict) else str(response)
        blocked = content.strip().lower().startswith(("i'm sorry", "i cannot", "blocked:"))
        return GuardrailDecision(allowed=not blocked, reasons=["NeMo evaluated input"])
