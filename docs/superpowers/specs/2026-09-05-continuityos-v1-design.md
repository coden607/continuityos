# ContinuityOS v1 Design

## Mission
ContinuityOS is a local-first, provider-neutral, modular operating layer for AI applications. It lets apps share a common PWA shell, model/agent routing, context continuity, memory, MCP/skill plugins, voice, guardrails, observability, secrets, health/recovery, CI/CD, and deployment adapters while remaining usable at $0 during development.

## Non-negotiable principles
- $0-first development: every paid capability has a local/free fallback.
- Provider-neutral: capabilities are selected by policy and telemetry, not hard-coded vendors.
- Context continuity: model switches never rely on lossy free-form summaries alone.
- Fail closed for consequential tools: schema, policy, authorization, and guardrail checks precede execution.
- Self-healing means retries, checkpoints, failover, quarantine, rollback, and recovery; autonomous production code mutation is forbidden.
- Self-learning may tune routing statistics and propose improvements, but code/policy changes require tests and review.
- Secrets are entered once, encrypted at rest, never committed in plaintext, and synced through adapters.
- Offline-first PWA behavior is a first-class capability.
- Components are modular and replaceable through stable interfaces.

## Core subsystems
1. App Shell — React/Vite/TypeScript PWA, service worker, offline packs, plugin UI.
2. AI Control Plane — capability registry, task classifier, model/provider router, Pydantic AI adapters, LangGraph orchestration, LiteLLM-compatible gateway.
3. Continuity Engine — context budget tracking, semantic compression checkpoints, Context Capsules, handoff verification, recovery.
4. Agent Bus — typed inter-agent messages with provenance and task IDs.
5. Reliability Kernel — health states, retries, circuit breakers, provider failover, workflow checkpoints, plugin quarantine, recovery hooks.
6. Memory — Mem0-compatible user/agent memory, Graphiti/FalkorDB temporal graph, Postgres/pgvector canonical data.
7. Knowledge/RAG — Docling ingestion, hybrid retrieval, Crawl4AI/Playwright adapters, reranking.
8. Voice — provider-neutral STT/TTS/realtime interfaces, whisper.cpp local STT fallback, WebRTC/VAD/Pipecat adapters.
9. Guardrail Mesh — deterministic policies, NeMo-compatible rails, tool schema validation, capability authorization, domain plugins.
10. Observability — OpenTelemetry-first traces/metrics/logs, Langfuse/Sentry adapters, token/cost/routing telemetry.
11. Secrets & CLI Fabric — SOPS+age local vault, CLI adapters for GitHub/Supabase/Cloudflare/Vercel/Railway and future providers.
12. Evolution — Renovate, capability adapters, benchmark/eval gates, versioned plugin contracts.

## Continuity Engine thresholds
- <65% context: normal.
- 65–80%: trim redundant retrieval and compress low-value history.
- 80–90%: create verified checkpoint/Context Capsule.
- >=90%: handoff or escalate to a larger-context model before another expensive turn.
- Emergency: persist state and halt unsafe continuation until a resumable route exists.

## Context Capsule required fields
objective, current_task, user_requirements, hard_constraints, decisions, completed_work, open_work, facts, artifacts, tool_state, citations, memory_refs, failed_approaches, current_plan, next_action, handoff_reason.

## Router scoring
Candidate score is a weighted combination of capability fit, quality, context fit, reliability, privacy fit, latency fit, token cost, dollar cost, failure rate, and context pressure. Apps may override weights without changing the router implementation.

## Health states
healthy, degraded, unhealthy, quarantined, recovering.

## Profiles
- minimal: API + local DB + one model adapter + CLI.
- ai: minimal + routing + continuity + agent bus + memory adapters.
- full: ai + PWA + graph + voice + guardrails + observability + workers + deployment adapters.

## Repository shape
- `apps/web-pwa`
- `services/api`
- `packages/python/continuityos`
- `packages/ts/*`
- `plugins/{skills,mcp,guardrails,providers}`
- `integrations/*`
- `workflows/{archon,bmad,langgraph}`
- `.github/workflows`
- `docs/superpowers/{specs,plans}`

## v0.1 acceptance criteria
- Typed capability registry and candidate model definitions.
- Deterministic router with cost/context/reliability/privacy-aware scoring.
- Context budget evaluator and Context Capsule schema.
- Typed Agent Bus message schema.
- Health registry with automatic route exclusion for unhealthy/quarantined providers.
- FastAPI health and route-debug endpoints.
- `continuum` CLI with `doctor`, `health`, and `route` commands.
- Secret-safe `.gitignore`, `.env.example`, SOPS sample config, and secret-scanning CI.
- GitHub Actions for Python test/lint/security baseline.
- Minimal Vite PWA shell communicating with `/status/health`.
- Unit tests covering routing, context thresholds, capsules, and health behavior.
