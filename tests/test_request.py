from pathlib import Path
from types import SimpleNamespace

import pytest

from gway_request import core
from gway_request.commands import issue


def test_split_issue_text_title_only():
    assert core.split_issue_text("Fix the LCD") == ("Fix the LCD", None)


def test_split_issue_text_multiline():
    assert core.split_issue_text("Fix the LCD\nIt fails after restart.") == (
        "Fix the LCD",
        "It fails after restart.",
    )


def test_split_issue_text_rejects_empty():
    with pytest.raises(ValueError, match="cannot be empty"):
        core.split_issue_text("  \n")


def test_project_path_resolves_gway_from_active_executable(tmp_path, monkeypatch):
    checkout = tmp_path / "gway"
    executable = checkout / "venv" / "bin" / "gway"
    executable.parent.mkdir(parents=True)
    executable.touch()
    (checkout / "gway.toml").write_text("[project]\nname = 'gway'\n")
    (checkout / ".git").mkdir()

    monkeypatch.setattr(core.shutil, "which", lambda name: str(executable))

    assert core.project_path("gway") == checkout


def test_project_path_uses_gway_path_for_registered_project(tmp_path, monkeypatch):
    checkout = tmp_path / "gway-lcd"
    checkout.mkdir()
    seen = {}

    def fake_run(command, **kwargs):
        seen.update(command=command, kwargs=kwargs)
        return SimpleNamespace(stdout=f"{checkout}\n")

    monkeypatch.setattr(core.subprocess, "run", fake_run)

    assert core.project_path("lcd") == checkout
    assert seen["command"] == ["gway", "path", "lcd"]


def test_github_repo_https(monkeypatch):
    monkeypatch.setattr(
        core.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            stdout="https://github.com/arthexis/gway-lcd.git\n"
        ),
    )
    assert core.github_repo(Path("/tmp/project")) == "arthexis/gway-lcd"


def test_github_repo_ssh(monkeypatch):
    monkeypatch.setattr(
        core.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            stdout="git@github.com:arthexis/gway-lcd.git\n"
        ),
    )
    assert core.github_repo(Path("/tmp/project")) == "arthexis/gway-lcd"


def test_issue_resolves_project_and_creates(monkeypatch):
    monkeypatch.setattr(
        "gway_request.commands.project_path", lambda project: Path("/repo")
    )
    monkeypatch.setattr(
        "gway_request.commands.github_repo", lambda path: "arthexis/gway-lcd"
    )
    seen = {}

    def fake_create(repo, title, body):
        seen.update(repo=repo, title=title, body=body)
        return "https://github.com/arthexis/gway-lcd/issues/123"

    monkeypatch.setattr("gway_request.commands.create_issue", fake_create)

    url = issue("lcd", "Broken LCD\nDetails here")

    assert url.endswith("/issues/123")
    assert seen == {
        "repo": "arthexis/gway-lcd",
        "title": "Broken LCD",
        "body": "Details here",
    }
