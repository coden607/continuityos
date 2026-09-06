# ContinuityOS v1 Design

## Mission
ContinuityOS is a local-first, provider-neutral operating layer for persistent AI applications. It lets an app retain task state, memory, provenance, tools, guardrails and UI while models and providers change.

Tagline: **Build once. Swap models. Never lose the thread.**

## Non-goals
- Not a single-model wrapper.
- Not a permissionless autonomous code mutator.
- Not a replacement for domain-specific safety policy.
- Not dependent on a paid cloud service for development.

## Product vocabulary
- Continuity Core: runtime contracts and orchestration.
- Continuity Engine: context budgets, checkpoints, compression, recovery and cross-model handoff.
- Continuity Bus: typed agent/tool messages.
- Continuity Capsule: structured handoff object.
- Continuity Packs: domain plugins.
- Continuity Blueprints: application templates.
- CLI executable: `continuity`.

## Invariants
1. A $0/local development path must remain functional.
2. Every external provider is behind an interface or adapter.
3. Secrets never belong in Git or logs.
4. Context continuity is a first-class runtime capability.
5. Self-healing may recover services, but production code/policy mutation is proposed through tests/PRs, not applied blindly.
6. Consequential tools run through schema validation, policy, authorization and guardrails.
7. Observability is vendor-neutral at the instrumentation layer.
8. Heavy services are optional profiles; MINIMAL remains useful.

## Architecture

### App shell
React/Vite/TypeScript PWA, offline-first service worker and IndexedDB cache. Domain UI modules are loaded by pack manifest.

### Core runtime
Python/FastAPI with Pydantic v2 schemas. Pydantic AI/LangGraph/LiteLLM/DBOS are integration targets, not assumptions embedded into core contracts.

### Capability Registry
Models, MCPs, agents, memory, voice and tools advertise capabilities. Routing asks for capabilities rather than a vendor name.

### Model Router
Candidate scoring incorporates capability fit, reliability, context fit, privacy, latency, monetary/token cost, quality and health. Unhealthy or quarantined candidates are ineligible.

### Continuity Engine
Context pressure bands:
- <65% normal
- 65-80% compress low-value history
- 80-90% checkpoint
- >=90% handoff
- >=97% emergency handoff/recovery

A Context Capsule carries objective, active task, hard requirements, hard constraints, decisions, completed/open work, facts, artifacts, citations, tool state, failed approaches, current plan and next action. Receiving models must acknowledge/reconstruct critical state before continuation.

### Continuity Bus
Messages include sender, recipient, task ID, type, payload/provenance, confidence and open questions. Agents do not pass entire raw conversations by default.

### Reliability Kernel
Uniform health state: healthy, degraded, unhealthy, quarantined, recovering. Supports retries, circuit breakers, provider failover, checkpoint recovery and bounded healing actions.

### Learning Loop
Learns routing statistics and evaluation outcomes automatically. Persistent code/policy changes require tests, security checks and review gates.

### Secrets Fabric
SOPS + age is the portable encrypted-file default. ContinuityOS secret adapters can sync a key to GitHub, Supabase, Cloudflare, Vercel/Railway or future CLIs without printing values.

### Voice
whisper.cpp is the local STT default. STT, TTS and realtime/full-duplex providers are separate interfaces so cloud or local engines can be replaced independently.

### Memory/RAG
Postgres/SQLite core persistence, pgvector, Mem0 and Graphiti/FalkorDB adapters. Docling and crawling/retrieval are application integrations.

### MCP gateway
Per-app MCP servers are declared by pack. MCP execution is policy-gated and health-aware.

### Guardrail Mesh
Deterministic app policy + typed schemas + tool capabilities + optional NeMo rails + independent verification/human approval where consequence warrants it.

### Observability
OpenTelemetry instrumentation contract, with Langfuse/Sentry/local exporters as adapters. Track route decisions, model/tool spans, tokens, cost, latency, errors and guardrail outcomes.

## NextLaw607 reference pack
NextLaw607 is the first reference domain pack. Legal citation verification, New York primary-law sources, legal agents and live encounter policies belong inside the pack/application and must not make ContinuityOS itself a legal-only framework.

## Security boundaries
- `.env`, decrypted secret files and local secret storage are ignored by Git.
- Pre-commit and CI secret scanning.
- Model tools are deny-by-default; no direct arbitrary shell/database access from model output.
- Redact sensitive data from telemetry/exporters.
- Local/offline mode may not silently fall back to a cloud provider.

## Test strategy
- Deterministic unit tests for router, thresholds, capsules, health transitions and policies.
- Contract tests for adapters.
- Integration tests for API, DB checkpoints and model failover.
- E2E tests for PWA and selected packs.
- Security tests for secrets and unauthorized tool calls.
- Evaluation packs for model-dependent behavior.

## v0.1 foundation scope
- Monorepo structure.
- Typed candidate/capability models.
- Health-aware model router.
- Continuity Engine thresholds and Context Capsule schema.
- Typed Agent Bus.
- Guardrail interface.
- FastAPI health/router endpoints.
- Typer CLI: doctor, health, route.
- Minimal PWA shell.
- GitHub Actions CI/security.
- Secret-safe repository defaults.
- NextLaw607 reference pack manifest.

Heavy production integrations (actual Mem0/Graphiti/NeMo/DBOS/LiteLLM/whisper services) are adapter seams/milestones after the executable v0.1 core, so the foundation remains testable without network services.
