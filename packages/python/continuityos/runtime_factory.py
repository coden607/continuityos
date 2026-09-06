from __future__ import annotations

from .config import ContinuityConfig
from .dev_provider import DevEchoProvider
from .health import HealthRegistry
from .memory import SQLiteMemoryAdapter
from .providers import LiteLLMAdapter, ProviderFleet
from .runtime import RuntimeOrchestrator
from .telemetry import RoutingTelemetry


def build_runtime(config: ContinuityConfig) -> RuntimeOrchestrator:
    providers = []
    requested = {model.provider for model in config.models}
    if "dev" in requested:
        providers.append(DevEchoProvider())
    if "litellm" in requested:
        providers.append(LiteLLMAdapter())
    fleet = ProviderFleet(providers)
    return RuntimeOrchestrator(
        candidates=config.models,
        health=HealthRegistry(),
        fleet=fleet,
        telemetry=RoutingTelemetry(config.runtime.telemetry_path),
        memory=SQLiteMemoryAdapter(config.runtime.memory_path),
        checkpoint_dir=config.runtime.checkpoint_dir,
    )
