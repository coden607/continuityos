from pathlib import Path


def test_bootstrap_uses_api_when_gh_missing_and_token_present(monkeypatch, tmp_path: Path):
    from continuityos.repository import RepositoryBootstrapper

    calls = []
    monkeypatch.setattr("shutil.which", lambda command: "/usr/bin/git" if command == "git" else None)
    monkeypatch.setenv("GH_TOKEN", "secret-token")
    monkeypatch.setattr(RepositoryBootstrapper, "_repo_exists_api", lambda self, repo, token: False)
    monkeypatch.setattr(RepositoryBootstrapper, "_create_repo_api", lambda self, repo, visibility, token: calls.append((repo, visibility, token)))
    monkeypatch.setattr(RepositoryBootstrapper, "_ensure_origin", lambda self, repo: None)
    monkeypatch.setattr(RepositoryBootstrapper, "_push_all", lambda self, token=None: None)

    result = RepositoryBootstrapper(tmp_path).bootstrap("coden607/continuityos")
    assert result.created is True
    assert result.pushed is True
    assert calls == [("coden607/continuityos", "public", "secret-token")]


def test_bootstrap_reports_missing_github_auth(monkeypatch, tmp_path: Path):
    from continuityos.repository import RepositoryBootstrapper

    monkeypatch.setattr("shutil.which", lambda command: "/usr/bin/git" if command == "git" else None)
    monkeypatch.delenv("GH_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    result = RepositoryBootstrapper(tmp_path).bootstrap("coden607/continuityos")
    assert result.created is False
    assert result.pushed is False
    assert "GitHub authentication" in result.message


def test_bootstrap_uses_locally_stored_token(monkeypatch, tmp_path: Path):
    from continuityos.repository import RepositoryBootstrapper
    from continuityos.secrets import SecretManager

    SecretManager(tmp_path).set("GITHUB_TOKEN", "stored-token")
    monkeypatch.setattr("shutil.which", lambda command: "/usr/bin/git" if command == "git" else None)
    monkeypatch.delenv("GH_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.setattr(RepositoryBootstrapper, "_repo_exists_api", lambda self, repo, token: token == "stored-token")
    monkeypatch.setattr(RepositoryBootstrapper, "_ensure_origin", lambda self, repo: None)
    monkeypatch.setattr(RepositoryBootstrapper, "_push_all", lambda self, token=None: None)
    result = RepositoryBootstrapper(tmp_path).bootstrap("coden607/continuityos")
    assert result.created is False
    assert result.pushed is True


def test_token_push_uses_ephemeral_askpass_without_token_in_command(monkeypatch, tmp_path: Path):
    from types import SimpleNamespace
    from continuityos.repository import RepositoryBootstrapper

    calls = []
    def fake_run(args, **kwargs):
        calls.append((list(args), kwargs.get("env")))
        if args[:3] == ["git", "branch", "--show-current"]:
            return SimpleNamespace(stdout="feat/test\n", returncode=0)
        return SimpleNamespace(stdout="", returncode=0)

    monkeypatch.setattr("continuityos.repository.subprocess.run", fake_run)
    RepositoryBootstrapper(tmp_path)._push_all(token="super-secret")

    push_calls = [(args, env) for args, env in calls if args[:2] == ["git", "push"]]
    assert len(push_calls) == 2
    for args, env in push_calls:
        assert "super-secret" not in " ".join(args)
        assert env["CONTINUITY_GITHUB_TOKEN"] == "super-secret"
        assert env["GIT_TERMINAL_PROMPT"] == "0"
        assert "GIT_ASKPASS" in env
    assert not list(tmp_path.glob(".continuity-askpass-*"))
