from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import urllib.error
import urllib.request
from pathlib import Path


_GITHUB_REMOTE_RE = re.compile(
    r"^(?:https://github\.com/|git@github\.com:)(?P<repo>[^/]+/[^/]+?)(?:\.git)?$"
)


def project_path(project: str) -> Path:
    """Resolve an installed Gway project to its managed checkout path."""
    result = subprocess.run(
        ["gway", "path", project],
        check=True,
        capture_output=True,
        text=True,
    )
    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError(f"gway path returned no path for {project!r}")
    path = Path(lines[-1]).expanduser()
    if not path.exists():
        raise RuntimeError(f"resolved project path does not exist: {path}")
    return path


def github_repo(path: Path) -> str:
    """Return owner/repository parsed from a checkout's origin remote."""
    result = subprocess.run(
        ["git", "-C", str(path), "remote", "get-url", "origin"],
        check=True,
        capture_output=True,
        text=True,
    )
    remote = result.stdout.strip()
    match = _GITHUB_REMOTE_RE.match(remote)
    if not match:
        raise ValueError(f"origin is not a supported GitHub remote: {remote}")
    repo = match.group("repo")
    return repo[:-4] if repo.endswith(".git") else repo


def split_issue_text(text: str) -> tuple[str, str | None]:
    """Use the first non-empty line as title and the remainder as body."""
    lines = text.strip().splitlines()
    while lines and not lines[0].strip():
        lines.pop(0)
    if not lines:
        raise ValueError("issue text cannot be empty")

    title = lines[0].strip()
    body = "\n".join(lines[1:]).strip() or None
    return title, body


def create_issue(repo: str, title: str, body: str | None = None) -> str:
    """Create a GitHub issue and return its URL."""
    if shutil.which("gh"):
        command = ["gh", "issue", "create", "--repo", repo, "--title", title]
        command.extend(["--body", body or ""])
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        return result.stdout.strip()

    token = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")
    if not token:
        raise RuntimeError(
            "GitHub authentication required: install/authenticate gh or set GH_TOKEN/GITHUB_TOKEN"
        )

    payload = {"title": title}
    if body:
        payload["body"] = body
    request = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/issues",
        data=json.dumps(payload).encode(),
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request) as response:
            data = json.load(response)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")
        raise RuntimeError(f"GitHub issue creation failed ({exc.code}): {detail}") from exc
    return str(data["html_url"])
