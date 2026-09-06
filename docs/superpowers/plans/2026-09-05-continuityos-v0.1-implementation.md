# ContinuityOS v0.1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first executable ContinuityOS foundation with a typed capability router, Continuity Engine, health-aware model selection, Agent Bus, API, CLI, secret-safe repository defaults, GitHub Actions, and a minimal PWA shell.

**Architecture:** The core package is Python and owns routing/continuity contracts. FastAPI and Typer expose those contracts without embedding provider logic. The PWA is intentionally thin and talks to the API, while all future heavy integrations attach behind stable interfaces.

**Tech Stack:** Python 3.13, Pydantic v2, FastAPI, Typer, Pytest, React/Vite/TypeScript, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-09-05-continuityos-v1-design.md`

## Global Constraints
- Development must have a $0/local path.
- Provider/model/vendor implementations are adapters, not business logic.
- Never commit secrets.
- Consequential tool calls require validation/policy layers.
- Production self-learning never silently edits runtime code.
- Context handoff must preserve requirements, constraints, artifacts, citations, tool state, and next action.
- Build incremental working slices; heavy integrations remain optional in v0.1.

---

### Task 1: Repository safety and typed core contracts

**Files:**
- Create: `.gitignore`, `.env.example`, `.sops.yaml.example`, `.pre-commit-config.yaml`
- Create: `pyproject.toml`
- Create: `packages/python/continuityos/models.py`
- Create: `packages/python/continuityos/health.py`
- Test: `tests/test_models.py`, `tests/test_health.py`

**Interfaces:**
- Produces `Capability`, `ModelCandidate`, `TaskRequirements`, `RouteDecision`, `ContextBudget`, `ContextCapsule`, `HealthRegistry`.

### Task 2: Capability Router and Continuity Engine

**Files:**
- Create: `packages/python/continuityos/router.py`
- Create: `packages/python/continuityos/continuity.py`
- Create: `packages/python/continuityos/engine.py`
- Test: `tests/test_router.py`, `tests/test_continuity.py`

**Interfaces:**
- Router consumes candidate list, requirements, and health registry.
- Continuity Engine produces pressure action and structured handoff capsules.

### Task 3: Agent Bus and guardrail contracts

**Files:**
- Create: `packages/python/continuityos/bus.py`
- Create: `packages/python/continuityos/guardrails.py`
- Test: `tests/test_bus.py`, `tests/test_guardrails.py`

### Task 4: FastAPI and CLI surfaces

**Files:**
- Create: `services/api/main.py`
- Create: `packages/python/continuityos/cli.py`
- Test: `tests/test_api.py`, `tests/test_cli.py`

### Task 5: PWA shell and CI/security automation

**Files:**
- Create: `apps/web-pwa/*`
- Create: `.github/workflows/ci.yml`
- Create: `.github/workflows/security.yml`
- Create: `renovate.json`
- Test: repository policy tests + web manifest validation.

### Task 6: NextLaw607 reference pack boundary

**Files:**
- Create: `packs/nextlaw607/pack.json`
- Create: `packs/nextlaw607/README.md`
- Test: validate that the pack declares agents, skills, MCPs and guardrails without importing them into ContinuityOS core.
