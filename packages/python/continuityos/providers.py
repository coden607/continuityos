from __future__ import annotations

from typing import Any, Protocol

from pydantic import BaseModel, Field


class ProviderRequest(BaseModel):
    model: str
    messages: list[dict[str, Any]]
    max_tokens: int | None = Field(default=None, gt=0)
    temperature: float | None = Field(default=None, ge=0, le=2)
    metadata: dict[str, Any] = {}


class ProviderResult(BaseModel):
    text: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    cost: float = 0.0
    raw: dict[str, Any] = {}

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


class ModelProvider(Protocol):
    name: str
    def available(self) -> bool: ...
    def complete(self, request: ProviderRequest) -> ProviderResult: ...


class LiteLLMAdapter:
    name = "litellm"

    def available(self) -> bool:
        try:
            import litellm  # noqa: F401
        except ImportError:
            return False
        return True

    def complete(self, request: ProviderRequest) -> ProviderResult:
        if not self.available():
            raise RuntimeError("LiteLLM is not installed; install continuityos[litellm]")
        import litellm
        response = litellm.completion(
            model=request.model,
            messages=request.messages,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
        )
        choice = response.choices[0]
        usage = getattr(response, "usage", None)
        return ProviderResult(
            text=choice.message.content or "",
            model=getattr(response, "model", request.model),
            input_tokens=getattr(usage, "prompt_tokens", 0) if usage else 0,
            output_tokens=getattr(usage, "completion_tokens", 0) if usage else 0,
            raw={},
        )


class ProviderFleet:
    """Registry of provider adapters keyed by provider name."""

    def __init__(self, providers: list[ModelProvider] | None = None) -> None:
        self._providers: dict[str, ModelProvider] = {}
        for provider in providers or []:
            self.register(provider)

    def register(self, provider: ModelProvider) -> None:
        self._providers[provider.name] = provider

    def get(self, name: str) -> ModelProvider:
        provider = self._providers.get(name)
        if provider is None or not provider.available():
            raise LookupError(f"no provider adapter available for '{name}'")
        return provider

    def complete(self, provider_name: str, request: ProviderRequest) -> ProviderResult:
        return self.get(provider_name).complete(request)

    def available(self) -> list[str]:
        return sorted(name for name, provider in self._providers.items() if provider.available())
