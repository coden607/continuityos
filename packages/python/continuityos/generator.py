from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from .blueprint import AppBlueprint


@dataclass(frozen=True)
class GeneratedApp:
    root: Path
    pack_file: Path
    env_example: Path
    config_file: Path
    blueprint_file: Path | None = None
    manifest_file: Path | None = None
    verification_file: Path | None = None


class AppGenerator:
    def __init__(self, destination: str | Path) -> None:
        self.destination = Path(destination)

    def create(self, name: str, *, template: str = "generic", force: bool = False) -> GeneratedApp:
        slug = self._slug(name)
        root = self._prepare_root(slug, force)
        (root / "packs" / slug).mkdir(parents=True, exist_ok=True)
        (root / "app").mkdir(exist_ok=True)

        pack = {
            "name": slug,
            "display_name": name,
            "template": template,
            "version": "0.1.0",
            "skills": [], "mcp": [], "agents": [], "guardrails": [], "knowledge": [],
        }
        pack_file = root / "packs" / slug / "pack.json"
        pack_file.write_text(json.dumps(pack, indent=2) + "\n", encoding="utf-8")
        config_file = root / "continuity.toml"
        config_file.write_text(self._runtime_config(name, "minimal"), encoding="utf-8")
        env_example = root / ".env.example"
        env_example.write_text("# Add app-specific secret names and non-secret configuration here.\n", encoding="utf-8")
        self._common_files(root, name, slug, template)
        return GeneratedApp(root=root, pack_file=pack_file, env_example=env_example, config_file=config_file)

    def create_from_blueprint(self, blueprint: AppBlueprint, *, force: bool = False) -> GeneratedApp:
        name = blueprint.app.name
        slug = self._slug(name)
        root = self._prepare_root(slug, force)
        continuity_dir = root / ".continuity"
        pack_dir = root / "packs" / slug
        for path in (continuity_dir, pack_dir, root / "src", root / "tests"):
            path.mkdir(parents=True, exist_ok=True)

        blueprint_file = root / "continuity.blueprint.toml"
        blueprint_file.write_text(self._blueprint_toml(blueprint), encoding="utf-8")

        pack = {
            "name": slug,
            "display_name": name,
            "domain": blueprint.app.domain,
            "version": blueprint.app.version,
            "skills": [], "mcp": [], "agents": [], "guardrails": [], "knowledge": [],
        }
        pack_file = pack_dir / "pack.json"
        pack_file.write_text(json.dumps(pack, indent=2) + "\n", encoding="utf-8")

        config_file = root / "continuity.toml"
        config_file.write_text(self._runtime_config(name, blueprint.app.profile), encoding="utf-8")

        env_example = root / ".env.example"
        env_example.write_text(
            "# Secret names only. Never commit real values.\n" +
            "".join(f"{key}=\n" for key in blueprint.deployment.secrets),
            encoding="utf-8",
        )
        self._common_files(root, name, slug, "blueprint")

        verification_file = continuity_dir / "verification.json"
        verification_file.write_text(json.dumps({
            "gates": blueprint.verification.gates,
            "commands": blueprint.verification.commands,
            "performance_budgets": blueprint.verification.performance_budgets,
            "min_quality": blueprint.quality.min_quality,
            "min_reliability": blueprint.quality.min_reliability,
        }, indent=2) + "\n", encoding="utf-8")

        managed_paths = [
            "continuity.blueprint.toml", "continuity.toml", ".env.example", ".gitignore",
            "README.md", f"packs/{slug}/pack.json", ".continuity/verification.json",
        ]
        fingerprints = {
            rel: self._sha256(root / rel) for rel in managed_paths if (root / rel).is_file()
        }
        manifest_file = continuity_dir / "manifest.json"
        manifest_file.write_text(json.dumps({
            "generator": "ContinuityOS",
            "schema_version": 1,
            "app": {"name": name, "slug": slug, "version": blueprint.app.version, "domain": blueprint.app.domain},
            "managed_paths": managed_paths,
            "owned_paths": ["src", "tests"],
            "fingerprints": fingerprints,
        }, indent=2) + "\n", encoding="utf-8")

        return GeneratedApp(
            root=root, pack_file=pack_file, env_example=env_example, config_file=config_file,
            blueprint_file=blueprint_file, manifest_file=manifest_file, verification_file=verification_file,
        )

    def _prepare_root(self, slug: str, force: bool) -> Path:
        root = self.destination / slug
        if root.exists() and any(root.iterdir()) and not force:
            raise FileExistsError(root)
        root.mkdir(parents=True, exist_ok=True)
        return root

    @staticmethod
    def _runtime_config(name: str, profile: str) -> str:
        return "\n".join([
            "[app]", f"name = {json.dumps(name)}", f"profile = {json.dumps(profile)}", "",
            "[runtime]", 'checkpoint_dir = ".continuity/checkpoints"',
            'telemetry_path = ".continuity/routes.jsonl"', 'memory_path = ".continuity/memory.db"', "",
            "[[models]]", 'id = "dev-echo"', 'provider = "dev"', 'capabilities = ["text"]',
            "context_window = 1000000", "quality = 0.1", "reliability = 1.0",
            "cost_per_million = 0.0", "latency_ms = 0", 'privacy = "local"',
            "max_output_tokens = 4096", "",
        ])

    @staticmethod
    def _common_files(root: Path, name: str, slug: str, template: str) -> None:
        (root / ".gitignore").write_text(
            ".env\n.env.*\n!.env.example\n.secrets/\n.continuity/checkpoints/\n.continuity/routes.jsonl\n.continuity/memory.db\n__pycache__/\n.venv/\nnode_modules/\ndist/\n",
            encoding="utf-8",
        )
        (root / "README.md").write_text(
            f"# {name}\n\nGenerated by ContinuityOS using the `{template}` blueprint.\n\n"
            "## First run\n\n```bash\ncontinuity config-check continuity.toml\n"
            'continuity execute "hello" --config continuity.toml\n```\n\n'
            f"Customize `packs/{slug}/pack.json` and app-owned `src/`/`tests/` without editing generated managed files.\n",
            encoding="utf-8",
        )

    @staticmethod
    def _sha256(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    @staticmethod
    def _blueprint_toml(bp: AppBlueprint) -> str:
        def q(value: str) -> str: return json.dumps(value)
        def arr(values: list[str]) -> str: return "[" + ", ".join(q(v) for v in values) + "]"
        return "\n".join([
            "[app]", f"name = {q(bp.app.name)}", f"domain = {q(bp.app.domain)}", f"version = {q(bp.app.version)}", f"profile = {q(bp.app.profile)}", "",
            "[development]", f"method = {q(bp.development.method)}", f"roles = {arr(bp.development.roles)}",
            f"architecture_gate = {str(bp.development.architecture_gate).lower()}", f"security_gate = {str(bp.development.security_gate).lower()}", f"eval_gate = {str(bp.development.eval_gate).lower()}", "",
            "[quality]", f"min_quality = {bp.quality.min_quality}", f"min_reliability = {bp.quality.min_reliability}", f"prefer_zero_token = {str(bp.quality.prefer_zero_token).lower()}", f"escalation = {arr(bp.quality.escalation)}", "",
            "[verification]", f"gates = {arr(bp.verification.gates)}", "",
            "[verification.commands]", *[f"{key} = {q(value)}" for key, value in sorted(bp.verification.commands.items())], "",
            "[verification.performance_budgets]", *[f"{key} = {value}" for key, value in sorted(bp.verification.performance_budgets.items())], "",
            "[features]", f"pwa = {str(bp.features.pwa).lower()}", f"api = {str(bp.features.api).lower()}", f"voice = {str(bp.features.voice).lower()}", f"memory = {str(bp.features.memory).lower()}", "",
            "[deployment]", f"targets = {arr(bp.deployment.targets)}", f"secrets = {arr(bp.deployment.secrets)}", "",
        ])

    @staticmethod
    def _slug(name: str) -> str:
        slug = "".join(ch.lower() if ch.isalnum() else "-" for ch in name).strip("-")
        while "--" in slug:
            slug = slug.replace("--", "-")
        if not slug:
            raise ValueError("app name must contain letters or numbers")
        return slug
