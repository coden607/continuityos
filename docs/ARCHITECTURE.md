# ContinuityOS v1.2 Architecture

ContinuityOS is an adapter-driven, local-first AI application operating layer. The core remains useful with no paid services and no optional AI SDKs installed.

## Execution path

```text
Task
 -> Guardrail policies
 -> Context-pressure evaluation
 -> Checkpoint when needed
 -> Capability/model routing
 -> Healthy provider execution
 -> Failover on transient failure
 -> Routing telemetry
 -> Memory persistence
 -> Response
```

`RuntimeOrchestrator` is the canonical model-execution path. CLI/API surfaces should reuse it rather than inventing parallel execution logic.

## Capability dispatch

Not every task should invoke a model. `CapabilityDispatcher` ranks models, skills, MCPs, tools and agents using capability fit, health, privacy, quality, reliability, latency and token cost. A zero-token local capability can beat a model when it satisfies the same requirement.

## Continuity / Token Spin

Context pressure is evaluated before execution. Low pressure proceeds normally; rising pressure triggers compression/checkpoint behavior. Handoff or emergency pressure increases the required context beyond the current model's window so the router selects a larger-context healthy candidate when one exists. Structured Context Capsules and receiver acknowledgement verification preserve objective, requirements, hard constraints and next action across model changes.

## Routing identity and learning

A candidate `id` is a stable logical routing identity. Its provider-facing `model` may change independently. Routing telemetry records task type, success, latency, tokens and cost against the stable identity. Learning updates recommendations/evidence only; it never silently rewrites source code or policy.

## Reliability and self-healing

Health probes feed a registry. A transient provider failure degrades the candidate and removes it from the current request; repeated failures can quarantine it. Bounded recovery actions may probe, retry or restore a component. Successful recovery makes it routable again. Production code mutation remains subject to Git/CI review.

## Runtime profiles

TOML profiles describe the app, providers, candidates and packs. The minimal profile uses `dev-echo`, while optional profiles can activate LiteLLM or future provider adapters. Domain packs carry agents, skills, MCP definitions, guardrails, schemas, knowledge and UI metadata.

## Persistence and memory

The guaranteed local path uses SQLite and `.continuity/` files. Optional Mem0, Graphiti and DBOS adapters sit behind interfaces. `.continuity/` is always treated as sensitive runtime state and is ignored by Git.

## MCP boundary

The default client follows the stateless MCP 2026 request model: self-describing requests, protocol/method headers and client metadata on each call, with optional `server/discover`. Legacy initialize/SSE support exists only as a compatibility path for older servers.

## Voice boundary

Speech interfaces are provider-neutral. whisper.cpp and Piper are local STT/TTS choices; Pipecat-compatible streaming primitives support richer realtime pipelines. No cloud voice provider is required for the core to start.

## Observability

Telemetry is vendor-neutral at the core. OpenTelemetry/Langfuse exporters are optional. Traces may include prompts or tool inputs, so production exporters must follow app privacy policy and redaction requirements.

## PWA boundary

The minimal PWA is browser-native JavaScript with no npm download required for its build. It exposes health and an execution console and caches the application shell offline. React/Vite may be added as an optional richer application blueprint without becoming a prerequisite for minimal development.

## Deployment boundary

Docker/Compose are provided for the API. GitHub Actions verifies Python, security, container and release artifacts. Cloudflare Pages deployment is opt-in and credential-gated; normal pushes do not deploy or incur a hosting requirement.

## Integration boundaries

Optional integrations include LiteLLM, Mem0, Graphiti, NeMo Guardrails, DBOS, OpenTelemetry, Langfuse, Pipecat, whisper.cpp, Piper and arbitrary MCP servers. Each is behind an interface so a superior future implementation can replace it without changing app business logic.
