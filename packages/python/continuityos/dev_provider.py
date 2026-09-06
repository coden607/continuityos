from __future__ import annotations

from .providers import ProviderRequest, ProviderResult


class DevEchoProvider:
    """Zero-dependency development provider used to prove the full runtime path."""

    name = "dev"

    def available(self) -> bool:
        return True

    def complete(self, request: ProviderRequest) -> ProviderResult:
        text = ""
        for message in reversed(request.messages):
            if message.get("role") == "user":
                text = str(message.get("content", ""))
                break
        return ProviderResult(text=text, model=request.model, input_tokens=0, output_tokens=0, cost=0.0)
