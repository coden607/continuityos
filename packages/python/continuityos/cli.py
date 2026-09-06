from __future__ import annotations

import json
from pathlib import Path

import typer

from . import __version__
from .defaults import default_candidates
from .generator import AppGenerator
from .health import HealthRegistry
from .models import Capability, ContextBudget, TaskRequirements
from .router import Router
from .secrets import SecretManager
from .tooling import tool_statuses
from .integrations import integration_statuses
from .repository import RepositoryBootstrapper
from .dev_provider import DevEchoProvider
from .providers import ProviderFleet
from .runtime import ExecutionRequest, RuntimeOrchestrator
from .config import load_config
from .runtime_factory import build_runtime
from .pack_loader import PackLoader

app = typer.Typer(help="ContinuityOS control CLI")
secrets_app = typer.Typer(help="Store and sync secrets without printing values")
app.add_typer(secrets_app, name="secrets")


@app.command()
def doctor() -> None:
    statuses = tool_statuses()
    typer.echo(json.dumps({
        "platform": "ContinuityOS",
        "version": __version__,
        "core": "healthy",
        "profile": "minimal",
        "secret_mode": "local-first",
        "tools": [s.model_dump() for s in statuses],
        "integrations": [i.__dict__ for i in integration_statuses()],
    }, indent=2))


@app.command()
def health() -> None:
    integrations = integration_statuses()
    typer.echo(json.dumps({"status": "healthy", "components": {"core": "healthy"}, "optional_integrations": {i.name: ("available" if i.available else "not-installed") for i in integrations}}, indent=2))


@app.command()
def route(capability: str = "text", context: int = 0, privacy: str = "any", task_type: str = "general") -> None:
    router = Router(default_candidates(), HealthRegistry())
    req = TaskRequirements(capabilities={Capability(capability)}, context_needed=context, privacy=privacy, task_type=task_type)
    typer.echo(router.route(req).model_dump_json(indent=2))


@app.command("context")
def context_action(limit: int = typer.Option(..., "--limit"), used: int = typer.Option(..., "--used"), reserve: int = typer.Option(0, "--reserve")) -> None:
    from .continuity import evaluate_context
    action = evaluate_context(ContextBudget(limit=limit, used=used, reserve=reserve))
    typer.echo(action.value)


@app.command("new")
def new_app(name: str, template: str = "generic", destination: Path = Path("."), force: bool = False) -> None:
    generated = AppGenerator(destination).create(name, template=template, force=force)
    typer.echo(str(generated.root))


@app.command("repo-bootstrap")
def repo_bootstrap(repository: str = typer.Argument("coden607/continuityos"), visibility: str = typer.Option("public", "--visibility"), push: bool = typer.Option(True, "--push/--no-push")) -> None:
    result = RepositoryBootstrapper(".").bootstrap(repository, visibility=visibility, push=push)
    typer.echo(json.dumps({"repository": result.repository, "created": result.created, "pushed": result.pushed, "message": result.message}, indent=2))
    if result.message != "repository ready":
        raise typer.Exit(code=1)


@app.command()
def execute(
    prompt: str,
    task_id: str = typer.Option("cli", "--task-id"),
    capability: str = typer.Option("text", "--capability"),
    config: Path | None = typer.Option(None, "--config", exists=True, dir_okay=False, readable=True),
) -> None:
    selected = Capability(capability)
    if config is not None:
        runtime = build_runtime(load_config(config))
    else:
        from .models import ModelCandidate
        candidate = ModelCandidate(
            id="dev-echo", provider="dev", capabilities={selected}, context_window=1_000_000,
            quality=0.1, reliability=1.0, cost_per_million=0.0, latency_ms=0, privacy="local",
        )
        runtime = RuntimeOrchestrator(candidates=[candidate], health=HealthRegistry(), fleet=ProviderFleet([DevEchoProvider()]))
    result = runtime.execute(ExecutionRequest(task_id=task_id, prompt=prompt, requirements=TaskRequirements(capabilities={selected})))
    typer.echo(result.model_dump_json(indent=2))


@app.command("config-check")
def config_check(path: Path = typer.Argument(..., exists=True, dir_okay=False, readable=True)) -> None:
    cfg = load_config(path)
    typer.echo(json.dumps({
        "valid": True,
        "app": cfg.app.name,
        "profile": cfg.app.profile,
        "models": len(cfg.models),
        "providers": sorted({model.provider for model in cfg.models}),
    }, indent=2))


@app.command("packs")
def packs_command(root: Path = typer.Option(Path("packs"), "--root")) -> None:
    packs = PackLoader(root).discover()
    typer.echo(json.dumps({"packs": [pack.model_dump(mode="json") for pack in packs]}, indent=2))


@app.command()
def version() -> None:
    typer.echo(f"ContinuityOS {__version__}")


@app.command()
def integrations() -> None:
    typer.echo(json.dumps({"integrations": [s.__dict__ for s in integration_statuses()]}, indent=2))


@app.command()
def plugins() -> None:
    typer.echo(json.dumps({"plugins": ["courtlistener", "whisper.cpp", "litellm", "mem0", "graphiti", "nemo-guardrails"]}, indent=2))


@secrets_app.command("set")
def secret_set(key: str, value: str = typer.Option(..., prompt=True, hide_input=True), root: Path = Path(".")) -> None:
    SecretManager(root).set(key, value)
    typer.echo(f"stored {key}")


@secrets_app.command("list")
def secret_list(root: Path = Path(".")) -> None:
    typer.echo(json.dumps({"keys": SecretManager(root).keys()}, indent=2))


@secrets_app.command("sync")
def secret_sync(key: str, target: str, repository: str | None = None, root: Path = Path(".")) -> None:
    result = SecretManager(root).sync(key, target, repository=repository)
    typer.echo(json.dumps({"target": result.target, "synced": result.synced, "reason": result.reason}, indent=2))


@secrets_app.command("sync-all")
def secret_sync_all(targets: str, repository: str | None = None, root: Path = Path(".")) -> None:
    target_list = [t.strip() for t in targets.split(",") if t.strip()]
    results = SecretManager(root).sync_all(target_list, repository=repository)
    typer.echo(json.dumps({"results": [r.__dict__ for r in results]}, indent=2))


if __name__ == "__main__":
    app()
