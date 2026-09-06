from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SecretSyncResult:
    target: str
    synced: bool
    reason: str = ""


class SecretManager:
    """Local-first secret entry with optional CLI sync. Never prints secret values."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.local_env = self.root / ".env.local"

    def set(self, key: str, value: str) -> Path:
        if not key or any(ch.isspace() for ch in key) or "=" in key:
            raise ValueError("invalid secret key")
        self.root.mkdir(parents=True, exist_ok=True)
        existing = self._load()
        existing[key] = value
        self.local_env.write_text("\n".join(f"{k}={v}" for k, v in sorted(existing.items())) + "\n")
        os.chmod(self.local_env, 0o600)
        return self.local_env

    def keys(self) -> list[str]:
        return sorted(self._load())

    def cli_available(self, command: str) -> bool:
        return shutil.which(command) is not None

    def sync_all(self, targets: list[str], *, repository: str | None = None) -> list[SecretSyncResult]:
        results: list[SecretSyncResult] = []
        for key in self.keys():
            for target in targets:
                results.append(self.sync(key, target, repository=repository))
        return results

    def sync(self, key: str, target: str, *, repository: str | None = None) -> SecretSyncResult:
        value = self._get(key)
        commands: dict[str, tuple[str, list[str], bool]] = {
            "github": ("gh", ["gh", "secret", "set", key, "--repo", repository or ""], True),
            "supabase": ("supabase", ["supabase", "secrets", "set", f"{key}={value}"], False),
            "cloudflare": ("wrangler", ["wrangler", "secret", "put", key], True),
            "vercel": ("vercel", ["vercel", "env", "add", key, "production"], True),
            "railway": ("railway", ["railway", "variables", "--set", f"{key}={value}"], False),
        }
        if target not in commands:
            raise ValueError(f"unsupported secret target: {target}")
        binary, command, via_stdin = commands[target]
        if target == "github" and not repository:
            raise ValueError("repository is required for GitHub secret sync")
        if not self.cli_available(binary):
            return SecretSyncResult(target=target, synced=False, reason=f"{binary} CLI not installed")
        subprocess.run(command, input=value if via_stdin else None, text=True, check=True, capture_output=True)
        return SecretSyncResult(target=target, synced=True)

    def sync_github(self, key: str, repository: str) -> bool:
        return self.sync(key, "github", repository=repository).synced

    def _load(self) -> dict[str, str]:
        existing: dict[str, str] = {}
        if self.local_env.exists():
            for line in self.local_env.read_text().splitlines():
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    existing[k] = v
        return existing

    def _get(self, key: str) -> str:
        try:
            return self._load()[key]
        except KeyError as exc:
            raise KeyError(key) from exc
