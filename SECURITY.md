# Security Policy

ContinuityOS is local-first and fail-closed around secrets and consequential tool execution.

## Secrets and local state

- Never commit `.env`, `.env.local`, age private keys, cloud credentials, access tokens, private keys, local databases, transcripts or private user data.
- `.env.example` contains names only, never real values.
- `.continuity/` can contain prompts, checkpoints, routing telemetry and memory; it is sensitive runtime state and is Git-ignored.
- Secret synchronization must pass values through stdin/environment or provider CLIs without intentionally echoing them.
- GitHub REST fallback pushes use a temporary `GIT_ASKPASS` helper. Tokens are not embedded in remote URLs or Git command arguments, and the helper is removed after use.

## AI/tool boundaries

- Model output never receives unrestricted shell/database authority.
- Tool calls pass through schemas, policy/guardrail checks and app authorization.
- High-consequence domain packs can add stricter fail-closed validators.
- Memory is context, not authority. Domain facts that require authoritative verification must be revalidated against the relevant source.

## Self-healing boundaries

Self-healing may probe, retry, fail over, quarantine, checkpoint and recover bounded components. It may generate a proposed patch, but it does not silently rewrite or deploy production code. Production-changing patches must pass tests, security checks and the configured review policy.

## Observability

Logs/traces can become sensitive because prompts, tool inputs and response metadata may contain user data. Exporters should support redaction and should be explicitly enabled in deployments that send traces off-device.

## Incident response

If credential exposure is suspected, rotate/revoke the credential first. Then remove it from Git history, build artifacts and external logs, and investigate how the leak bypassed the local/CI checks.
