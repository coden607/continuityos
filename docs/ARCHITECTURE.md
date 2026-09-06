# ContinuityOS Architecture

ContinuityOS is a local-first application operating layer. The core is intentionally provider-neutral: providers, MCPs, memory systems, voice engines and domain behavior are registered through contracts and packs rather than imported into business logic.

## Execution plane

`RuntimeOrchestrator.execute()` is the canonical task path:

1. deterministic guardrail evaluation;
2. context-pressure decision;
3. checkpoint creation when pressure requires it;
4. health/capability/context-aware candidate routing;
5. live provider fleet execution with bounded failover;
6. health degradation/quarantine feedback on provider failure;
7. routing telemetry (success, latency, tokens, cost);
8. result persistence to configured memory;
9. typed execution result.

The CLI and FastAPI `/execute` surface both use this same runtime factory/path when a profile is supplied.

## Token Spin / capability dispatch

Model routing and cross-capability dispatch are distinct:

- `CapabilityDispatcher` ranks models, skills, MCPs, tools and agents and can prefer a zero-token local capability before calling an LLM.
- `Router` ranks model candidates by capability fit, reliability, quality, privacy, latency, cost and context fit.
- At handoff pressure the runtime filters toward a larger-context candidate when possible.
- Candidate `id` is a stable routing/telemetry alias; candidate `model` is the provider-facing name. That allows switching an alias from one hosted/local model to another without discarding learned outcomes.
- `RoutingTelemetry` records outcomes and `RoutingLearner` computes evidence-based recommendations.

## Continuity

`ContextBudget` drives normal/compress/checkpoint/handoff/emergency actions. `ContextCapsule` is the structured handoff/checkpoint unit and preserves objective, requirements, hard constraints, artifacts, citations and next action. Compression is field-aware; critical requirements/constraints are preserved ahead of low-value history.

## Reliability

Health states are healthy, degraded, unhealthy, quarantined and recovering. A transient provider failure degrades the provider and skips it for the current execution; repeated failures can quarantine it. `SelfHealingSupervisor` may run bounded probes/healers and restore a component only after a successful post-heal probe. Code mutation is intentionally outside this runtime loop.

## Persistence

The zero-cost fallback uses SQLite/file storage for memory, checkpoints and telemetry under `.continuity/`. Optional adapters connect Mem0, Graphiti and DBOS. `.continuity/` is never committed.

## MCP

The default MCP client follows the current stateless request model: protocol/method/name/client metadata is carried on each request and no mandatory session initialization is assumed. `server/discover` is supported, and an explicit `legacy_initialize()` compatibility method remains for older MCP servers.

## Voice

Voice is split into STT, TTS and realtime transport:

- `whisper.cpp` adapter interface for local STT;
- Piper adapter for local TTS;
- Pipecat-compatible realtime interface;
- streaming audio primitive for integration tests/pipelines.

## Guardrails

Deterministic application policy remains the base layer. Optional NeMo integration sits behind the same guardrail contract. Provider/model output cannot directly bypass tool authorization. Domain packs add stricter policies.

## App/pack boundary

`continuity new` creates a runnable app with `continuity.toml`, local-state ignore rules and a domain pack. `PackLoader` accepts the generic generated manifest and richer nested domain manifests (such as NextLaw607) without changing the core runtime.

## Deployment

- Base runtime can run directly with Python or Docker Compose.
- Minimal PWA is dependency-free at runtime/build time and communicates with the API.
- GitHub Actions verify Python, PWA, security and container builds.
- Cloudflare Pages deployment is opt-in/manual and requires configured secrets.
- Hosted model/observability/memory services remain optional.
