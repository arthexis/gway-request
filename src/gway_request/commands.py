from __future__ import annotations

from gway_request.core import create_issue, github_repo, project_path, split_issue_text


def issue(project: str, text: str) -> str:
    """Create a GitHub issue for an installed Gway project and return its URL."""
    title, body = split_issue_text(text)
    repo = github_repo(project_path(project))
    return create_issue(repo, title, body)
