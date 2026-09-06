# Changelog

## 1.2.1

- Make `continuity repo-bootstrap` return a nonzero process status when repository setup is not ready, while preserving its machine-readable JSON result.
- Make the FastAPI `/execute` path honor `CONTINUITY_CONFIG` and build the same profile-driven runtime used by the CLI.
- Return HTTP 503 for missing/invalid server runtime profiles or when no configured candidate can serve the request.

## 1.2.0

- Add the unified `RuntimeOrchestrator` execution path spanning guardrails, context pressure, routing, provider failover, telemetry, memory and checkpoints.
- Add a cross-capability dispatcher that can choose models, skills, MCPs, tools or agents and prefer zero-token capabilities.
- Make Token Spin context pressure actually escalate to a larger-context candidate when available.
- Add stable candidate aliases separate from provider-facing model identifiers.
- Add typed TOML runtime profiles, pack loading and runtime factory construction.
- Add zero-cost `dev-echo` execution through CLI and FastAPI for end-to-end development without model credentials.
- Modernize MCP requests to the 2026-07-28 stateless protocol and retain an explicit legacy initialize compatibility path.
- Add an immediately runnable app generator with local-state isolation and a default runtime profile.
- Replace the broken minimal TSX PWA path with a dependency-free offline browser shell and execution console.
- Add Docker/Compose, container CI, release packaging and credential-gated Cloudflare Pages deployment.
- Expand `continuity doctor` coverage across approved hosting, AI, security, voice and developer CLIs.
- Add GitHub REST repository creation fallback when `gh` is unavailable.
- Reuse `GH_TOKEN`/`GITHUB_TOKEN` from environment or ContinuityOS local secret storage.
- Authenticate REST-fallback pushes through an ephemeral `GIT_ASKPASS` bridge without embedding tokens in remote URLs or command arguments.
- Ignore `.continuity/` so checkpoints, telemetry and local memory cannot be accidentally committed.
- Add a reproducible local release-verification script.

## 1.1.0

- Add ProviderFleet and ContinuityEngine fleet execution/failover.
- Add deterministic provider benchmark runner feeding routing telemetry.
- Add typed MCP JSON-RPC errors and robust SSE event parsing.
- Add DBOS-compatible durable workflow adapter with SQLite recovery state.
- Add persistent SQLite memory backend.
- Add Langfuse-compatible tracing adapter.
- Add asynchronous realtime audio chunk stream primitive.

## 1.0.0

- Initial ContinuityOS foundation.
