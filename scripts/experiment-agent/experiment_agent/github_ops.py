"""GitHub issues, comments, and labels."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

LABEL_EXPERIMENT = "experiment-agent"
LABEL_PROGRESS = "agent-in-progress"
ISSUE_TITLE_PREFIX = "experiment-agent:"


def _gh(args: list[str]) -> str:
    return subprocess.check_output(["gh", *args], cwd=REPO_ROOT, text=True)


def ensure_labels(repo: str) -> None:
    for name, color, desc in [
        (LABEL_EXPERIMENT, "1D76DB", "Proposal and work from experiment-agent"),
        (LABEL_PROGRESS, "FBCA04", "Agent is actively working this item"),
    ]:
        subprocess.run(
            [
                "gh",
                "label",
                "create",
                name,
                "--repo",
                repo,
                "--color",
                color,
                "--description",
                desc,
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )


def has_active_run(repo: str) -> bool:
    """True if an open experiment issue is still in progress."""
    raw = _gh(
        [
            "issue",
            "list",
            "--repo",
            repo,
            "--label",
            LABEL_EXPERIMENT,
            "--state",
            "open",
            "--json",
            "number,labels",
            "--limit",
            "30",
        ]
    )
    for issue in json.loads(raw):
        labels = {lb["name"] for lb in issue.get("labels", [])}
        if LABEL_PROGRESS in labels:
            return True
    return False


def _issue_number_from_url(url: str) -> int:
    """Parse issue number from `gh issue create` URL output."""
    path = url.strip().rstrip("/")
    if not path:
        raise ValueError("empty issue URL from gh issue create")
    number = path.split("/")[-1]
    if not number.isdigit():
        raise ValueError(f"could not parse issue number from: {url!r}")
    return int(number)


def create_proposal_issue(repo: str, title: str, body: str) -> int:
    full_title = title if title.startswith(ISSUE_TITLE_PREFIX) else f"{ISSUE_TITLE_PREFIX} {title}"
    url = _gh(
        [
            "issue",
            "create",
            "--repo",
            repo,
            "--title",
            full_title,
            "--body",
            body,
            "--label",
            LABEL_EXPERIMENT,
            "--label",
            LABEL_PROGRESS,
        ]
    )
    return _issue_number_from_url(url)


def comment_issue(repo: str, issue_number: int, body: str) -> None:
    _gh(
        [
            "issue",
            "comment",
            str(issue_number),
            "--repo",
            repo,
            "--body",
            body,
        ]
    )
