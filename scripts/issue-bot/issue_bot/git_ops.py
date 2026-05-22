"""Git branch, commit, push, and GitHub Actions outputs."""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def _git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        check=check,
        text=True,
        capture_output=True,
    )


def _slugify(title: str, *, max_len: int = 40) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug[:max_len] or "change"


def branch_name(issue_number: int, title: str) -> str:
    return f"issue-bot/{issue_number}-{_slugify(title)}"


def configure_bot_git() -> None:
    _git("config", "user.name", "github-actions[bot]")
    _git("config", "user.email", "github-actions[bot]@users.noreply.github.com")


def github_output(name: str, value: str) -> None:
    path = os.environ.get("GITHUB_OUTPUT")
    if not path:
        return
    with open(path, "a", encoding="utf-8") as handle:
        if "\n" in value:
            handle.write(f"{name}<<EOF\n{value}\nEOF\n")
        else:
            handle.write(f"{name}={value}\n")


def create_branch(branch: str, base: str) -> None:
    _git("fetch", "origin", base, check=False)
    _git("checkout", "-B", branch, f"origin/{base}")


def commit_and_push(branch: str, paths: list[str], message: str) -> None:
    for rel in paths:
        _git("add", rel)
    _git("commit", "-m", message)
    _git("push", "-u", "origin", branch)


def pr_body(issue_number: int, issue_title: str, summary: str, plan_excerpt: str) -> str:
    return f"""## Summary

{summary}

Implements #{issue_number}: {issue_title}

## Plan (excerpt)

{plan_excerpt[:2000]}

## Test plan

- [ ] Review generated changes
- [ ] PR Check passes
- [ ] Merge to close #{issue_number}

---
*Automated by [issue-bot](scripts/issue-bot/README.md) v2*
"""


def emit_pr_outputs(branch: str, title: str, body: str) -> None:
    github_output("branch", branch)
    github_output("pr_title", title)
    github_output("pr_body", body)
