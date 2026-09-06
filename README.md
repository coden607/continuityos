# ContinuityOS

**Build once. Swap models. Never lose the thread.**

ContinuityOS is a local-first, provider-neutral operating layer for modular AI applications. It keeps application logic stable while models, agents, skills, MCP servers, memory systems and deployment targets evolve.

## What v1.2 delivers

ContinuityOS 1.2 adds a complete execution path instead of isolated adapters:

- one fail-closed runtime orchestrator for guardrails, context pressure, routing, provider failover, telemetry, memory and checkpoints;
- capability dispatch across models, skills, MCPs, tools and agents so zero-token capabilities can win before an LLM is called;
- real context-pressure escalation to larger-context candidates when available;
- stable routing aliases decoupled from provider/model strings;
- task outcome telemetry and adaptive recommendations based on success, latency, tokens and cost;
- typed TOML runtime profiles and a runtime factory;
- immediate zero-cost `dev-echo` execution for new apps with no API key;
- current MCP stateless Streamable HTTP client plus an explicit legacy compatibility path;
- persistent SQLite memory/checkpoint fallbacks with optional Mem0, Graphiti and DBOS adapters;
- deterministic guardrails plus optional NeMo integration;
- whisper.cpp STT, Piper TTS and Pipecat-compatible realtime voice interfaces;
- OpenTelemetry/Langfuse observability seams;
- secret-safe repository bootstrap via `gh` or GitHub REST without embedding tokens in remote URLs;
- a genuinely dependency-free minimal PWA shell with health, execution console and offline caching;
- Docker/Compose, GitHub Actions container/release/security checks and opt-in Cloudflare Pages deployment;
- a reusable app generator that produces a runnable app profile and domain pack.

`packs/nextlaw607` is the first reference domain pack. Domain-specific code lives in packs so ContinuityOS core does not need to fork for legal, health, sales, counseling or future apps.

## $0-first rule

The base install requires no paid service. Every hosted integration is optional and should have a local/open-source fallback wherever practical. Missing optional tooling is reported by `continuity doctor`; it does not prevent the minimal runtime from starting.

## Canonical local workspace

```text
/mnt/data/Projects/ContinuityOS
```

Persistent release backups are also stored under the Library folder `/Projects/ContinuityOS`.

## Quick start

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
continuity config-check continuity.toml.example
continuity execute "hello" --config continuity.toml.example
pytest -q
```

Run the API with the zero-cost fallback runtime:

```bash
uvicorn services.api.main:api --reload
```

Run the API with a real runtime profile (the same factory used by the CLI):

```bash
CONTINUITY_CONFIG=continuity.toml.example uvicorn services.api.main:api --reload
```

Run the minimal PWA:

```bash
npm --prefix apps/web-pwa run build
python -m http.server 4173 --directory apps/web-pwa/dist
```

Or use Docker:

```bash
docker compose up --build
```

## Generate a new app

```bash
continuity new "My App" --template generic --destination ./Projects
cd ./Projects/my-app
continuity config-check continuity.toml
continuity execute "hello" --config continuity.toml
```

A generated app starts on the zero-cost `dev-echo` provider. Replace or extend the pack, MCPs, skills and provider profile without changing ContinuityOS core.

## Context continuity / Token Spin

Preview pressure handling:

```bash
continuity context --limit 200000 --used 181000 --reserve 8000
```

ContinuityOS tracks normal, compression, checkpoint, handoff and emergency states. At handoff pressure the runtime tries a larger-context healthy candidate, persists a checkpoint, and keeps stable task state. Structured Context Capsules and receiver verification are available for model-to-model handoff workflows.

The capability dispatcher can also avoid model tokens entirely when a healthy local skill, tool or MCP satisfies the task.

## Runtime profiles

`continuity.toml.example` is the base profile. A candidate has a stable `id` for telemetry and may map to a different provider-facing `model` string:

```toml
[[models]]
id = "cheap-reasoner"
provider = "litellm"
model = "openrouter/example/model"
context_window = 131072
max_output_tokens = 8192
quality = 0.82
reliability = 0.95
cost_per_1k = 0.0
```

This lets provider/model names change without discarding routing history for the logical candidate.

## Optional integration groups

The base package stays small. Install only what an app needs:

```bash
python -m pip install -e '.[litellm]'
python -m pip install -e '.[memory]'
python -m pip install -e '.[durable]'
python -m pip install -e '.[guardrails]'
python -m pip install -e '.[voice]'
python -m pip install -e '.[observability]'
# or all optional Python integrations
python -m pip install -e '.[full]'
```

## Secrets once, sync many

```bash
continuity secrets set OPENAI_API_KEY
continuity secrets set COURTLISTENER_API_TOKEN
continuity secrets sync-all github,supabase,cloudflare --repository coden607/continuityos
```

Real environment files, age private material and `.continuity/` runtime state are ignored by Git. ContinuityOS does not intentionally print stored values.

## GitHub bootstrap

With authenticated GitHub CLI:

```bash
continuity repo-bootstrap coden607/continuityos
```

Without `gh`, store a suitably scoped GitHub token once and use the REST fallback:

```bash
continuity secrets set GITHUB_TOKEN
continuity repo-bootstrap coden607/continuityos
```

The fallback uses an ephemeral `GIT_ASKPASS` bridge for push authentication. The token is not written into the Git remote URL or command arguments.

## MCP

ContinuityOS uses the current stateless MCP request model by default. Each request carries protocol/client metadata and method/name routing headers. `server/discover` is supported, while `legacy_initialize()` is retained only for older MCP servers during migration.

## API

Important endpoints include:

- `GET /status/live`
- `GET /status/ready`
- `GET /status/health`
- `GET /platform/capabilities`
- `GET /platform/integrations`
- `POST /route/preview`
- `POST /continuity/action`
- `POST /continuity/handoff/verify`
- `POST /council/decide`
- `POST /execute`

## Release verification

Run the same local gate used before cutting a release:

```bash
./scripts/verify-release.sh
```

See `docs/ARCHITECTURE.md` and `SECURITY.md` for invariants and trust boundaries.
