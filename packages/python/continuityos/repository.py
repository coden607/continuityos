from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from .secrets import SecretManager


@dataclass(frozen=True)
class RepoBootstrapResult:
    repository: str
    created: bool
    pushed: bool
    message: str


class RepositoryBootstrapper:
    def __init__(self, root: str | Path = ".") -> None:
        self.root = Path(root).resolve()

    def _token(self) -> str | None:
        token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
        if token:
            return token
        try:
            manager = SecretManager(self.root)
            values = manager._load()
            return values.get("GH_TOKEN") or values.get("GITHUB_TOKEN")
        except OSError:
            return None

    def available(self) -> bool:
        return shutil.which("git") is not None and (shutil.which("gh") is not None or self._token() is not None)

    def _request(self, method: str, url: str, token: str, payload: dict | None = None) -> tuple[int, dict]:
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            url,
            method=method,
            data=data,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "ContinuityOS",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                body = response.read().decode("utf-8")
                return response.status, json.loads(body) if body else {}
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8") if exc.fp else ""
            parsed = json.loads(body) if body else {}
            return exc.code, parsed

    def _repo_exists_api(self, repository: str, token: str) -> bool:
        status, _ = self._request("GET", f"https://api.github.com/repos/{repository}", token)
        if status == 200:
            return True
        if status == 404:
            return False
        raise RuntimeError(f"GitHub repository lookup failed with HTTP {status}")

    def _create_repo_api(self, repository: str, visibility: str, token: str) -> None:
        owner, name = repository.split("/", 1)
        status_user, user = self._request("GET", "https://api.github.com/user", token)
        if status_user != 200:
            raise RuntimeError(f"GitHub authentication failed with HTTP {status_user}")
        payload = {
            "name": name,
            "private": visibility == "private",
            "visibility": visibility,
            "description": "ContinuityOS — Build once. Swap models. Never lose the thread.",
            "has_issues": True,
            "has_projects": True,
            "has_wiki": False,
            "auto_init": False,
        }
        endpoint = "https://api.github.com/user/repos" if user.get("login") == owner else f"https://api.github.com/orgs/{owner}/repos"
        status, body = self._request("POST", endpoint, token, payload)
        if status not in {201}:
            message = body.get("message", f"HTTP {status}")
            raise RuntimeError(f"GitHub repository creation failed: {message}")

    def _ensure_origin(self, repository: str) -> None:
        url = f"https://github.com/{repository}.git"
        remotes = subprocess.run(["git", "remote"], cwd=self.root, check=True, capture_output=True, text=True).stdout.split()
        if "origin" in remotes:
            subprocess.run(["git", "remote", "set-url", "origin", url], cwd=self.root, check=True)
        else:
            subprocess.run(["git", "remote", "add", "origin", url], cwd=self.root, check=True)

    def _push_all(self, token: str | None = None) -> None:
        branch = subprocess.run(["git", "branch", "--show-current"], cwd=self.root, check=True, capture_output=True, text=True).stdout.strip()
        env = None
        askpass_path: Path | None = None
        if token:
            self.root.mkdir(parents=True, exist_ok=True)
            handle = tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", delete=False, dir=self.root, prefix=".continuity-askpass-", suffix=".sh"
            )
            askpass_path = Path(handle.name)
            try:
                handle.write(
                    '#!/bin/sh\n'
                    'case "$1" in\n'
                    '  *Username*) printf "%s\\n" "x-access-token" ;;\n'
                    '  *) printf "%s\\n" "$CONTINUITY_GITHUB_TOKEN" ;;\n'
                    'esac\n'
                )
            finally:
                handle.close()
            os.chmod(askpass_path, 0o700)
            env = os.environ.copy()
            env.update({
                "GIT_ASKPASS": str(askpass_path),
                "GIT_ASKPASS_REQUIRE": "force",
                "GIT_TERMINAL_PROMPT": "0",
                "CONTINUITY_GITHUB_TOKEN": token,
            })
        try:
            if branch:
                subprocess.run(["git", "push", "-u", "origin", branch], cwd=self.root, check=True, env=env)
            subprocess.run(["git", "push", "origin", "--tags"], cwd=self.root, check=True, env=env)
        finally:
            if askpass_path is not None:
                askpass_path.unlink(missing_ok=True)

    def bootstrap(self, repository: str, *, visibility: str = "public", push: bool = True) -> RepoBootstrapResult:
        if visibility not in {"public", "private", "internal"}:
            raise ValueError("visibility must be public, private, or internal")
        if shutil.which("git") is None:
            return RepoBootstrapResult(repository=repository, created=False, pushed=False, message="git is required")

        gh = shutil.which("gh")
        token = self._token()
        created = False

        if gh is not None:
            subprocess.run(["gh", "auth", "status"], cwd=self.root, check=True, capture_output=True, text=True)
            check = subprocess.run(["gh", "repo", "view", repository], cwd=self.root, capture_output=True, text=True)
            created = check.returncode != 0
            if created:
                subprocess.run(
                    ["gh", "repo", "create", repository, f"--{visibility}", "--source", str(self.root), "--remote", "origin"],
                    cwd=self.root,
                    check=True,
                    capture_output=True,
                    text=True,
                )
            else:
                self._ensure_origin(repository)
            if push:
                gh_token = subprocess.run(["gh", "auth", "token"], cwd=self.root, check=True, capture_output=True, text=True).stdout.strip()
                self._push_all(token=gh_token or None)
            return RepoBootstrapResult(repository=repository, created=created, pushed=push, message="repository ready")

        if token is None:
            return RepoBootstrapResult(
                repository=repository,
                created=False,
                pushed=False,
                message="GitHub authentication is required via gh, GH_TOKEN, or GITHUB_TOKEN",
            )

        created = not self._repo_exists_api(repository, token)
        if created:
            self._create_repo_api(repository, visibility, token)
        self._ensure_origin(repository)
        if push:
            self._push_all(token=token)
        return RepoBootstrapResult(repository=repository, created=created, pushed=push, message="repository ready")
