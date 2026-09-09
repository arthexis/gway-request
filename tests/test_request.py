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
