"""Auto-merge and CI-fix dispatch for issues labeled automerge."""

from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

LABEL_AUTOMERGE = "automerge"
FIX_MARKER_PREFIX = "<!-- issue-bot:fix-attempt:"
MAX_FIX_ATTEMPTS = 3
MERGE_MARKER = "<!-- pr-bot:merged -->"


def _gh(args: list[str]) -> str:
    return subprocess.check_output(["gh", *args], cwd=REPO_ROOT, text=True)


def closes_issue_number(pr_body: str | None) -> int | None:
    if not pr_body:
        return None
    match = re.search(r"(?:closes|fixes|resolves)\s+#(\d+)", pr_body, re.I)
    return int(match.group(1)) if match else None


def issue_has_automerge(repo: str, issue_number: int) -> bool:
    raw = _gh(
        [
            "issue",
            "view",
            str(issue_number),
            "--repo",
            repo,
            "--json",
            "labels",
        ]
    )
    labels = {lb["name"] for lb in json.loads(raw).get("labels", [])}
    return LABEL_AUTOMERGE in labels


def checks_status(repo: str, pr_number: int) -> str:
    """Return pending, success, failure, or unknown."""
    result = subprocess.run(
        [
            "gh",
            "pr",
            "checks",
            str(pr_number),
            "--repo",
            repo,
            "--json",
            "name,state,bucket",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        combined = f"{result.stderr or ''}{result.stdout or ''}".lower()
        if "no checks" in combined:
            return "pending"
        return "unknown"

    checks = json.loads(result.stdout)
    if not checks:
        return "pending"

    states: list[str] = []
    for check in checks:
        name = (check.get("name") or "").lower()
        if name == "approve":
            continue
        state = (check.get("state") or check.get("bucket") or "").upper()
        states.append(state)

    if not states:
        return "pending"
    if any(s in {"FAIL", "FAILURE", "CANCELLED", "TIMED_OUT", "ACTION_REQUIRED"} for s in states):
        return "failure"
    if any(s in {"PENDING", "IN_PROGRESS", "QUEUED", "WAITING"} for s in states):
        return "pending"
    if all(s in {"PASS", "SUCCESS", "SKIPPED", "NEUTRAL"} for s in states):
        return "success"
    return "unknown"


def count_fix_attempts(repo: str, issue_number: int) -> int:
    owner, name = repo.split("/", 1)
    try:
        bodies = subprocess.check_output(
            [
                "gh",
                "api",
                f"/repos/{owner}/{name}/issues/{issue_number}/comments",
                "--jq",
                ".[].body",
            ],
            cwd=REPO_ROOT,
            text=True,
        )
    except subprocess.CalledProcessError:
        return 0
    return sum(1 for line in bodies.splitlines() if FIX_MARKER_PREFIX in line)


def already_merged_comment(repo: str, pr_number: int) -> bool:
    owner, name = repo.split("/", 1)
    try:
        bodies = subprocess.check_output(
            [
                "gh",
                "api",
                f"/repos/{owner}/{name}/issues/{pr_number}/comments",
                "--jq",
                ".[].body",
            ],
            cwd=REPO_ROOT,
            text=True,
        )
    except subprocess.CalledProcessError:
        return False
    return MERGE_MARKER in bodies


def merge_pull_request(repo: str, pr_number: int) -> None:
    _gh(
        [
            "pr",
            "merge",
            str(pr_number),
            "--repo",
            repo,
            "--squash",
            "--delete-branch",
        ]
    )


def post_merge_comment(repo: str, pr_number: int, issue_number: int) -> None:
    body = (
        f"{MERGE_MARKER}\n"
        f"## Auto-merged\n\n"
        f"All required checks passed and issue #{issue_number} has the `{LABEL_AUTOMERGE}` label.\n\n"
        f"Issue #{issue_number} will close via `Closes #{issue_number}` in the PR body.\n\n"
        "---\n_Automated by [pr-bot](scripts/pr-bot/README.md) automerge._"
    )
    _gh(["pr", "comment", str(pr_number), "--repo", repo, "--body", body])


def post_fix_limit_comment(repo: str, pr_number: int, issue_number: int, attempts: int) -> None:
    body = (
        f"## Automerge paused\n\n"
        f"CI failed after **{attempts}** automated fix attempts for issue #{issue_number}. "
        f"Manual changes or merge are required.\n\n"
        "---\n_[pr-bot](scripts/pr-bot/README.md) automerge._"
    )
    _gh(["pr", "comment", str(pr_number), "--repo", repo, "--body", body])


def dispatch_issue_bot_fix(repo: str, issue_number: int, pr_number: int) -> None:
    ref = os.environ.get("PR_BOT_DEFAULT_BRANCH", "main")
    subprocess.run(
        [
            "gh",
            "workflow",
            "run",
            "Issue bot",
            "--repo",
            repo,
            "--ref",
            ref,
            "-f",
            f"issue_number={issue_number}",
            "-f",
            "fix_mode=true",
            "-f",
            f"pr_number={pr_number}",
        ],
        cwd=REPO_ROOT,
        check=True,
        text=True,
    )


def run_automerge(repo: str, pr_number: int, pr_body: str | None) -> None:
    issue_number = closes_issue_number(pr_body)
    if issue_number is None:
        print(f"PR #{pr_number}: no Closes #n in body; skip automerge.")
        return
    if not issue_has_automerge(repo, issue_number):
        print(f"PR #{pr_number}: issue #{issue_number} lacks {LABEL_AUTOMERGE}; skip automerge.")
        return
    if already_merged_comment(repo, pr_number):
        print(f"PR #{pr_number}: already auto-merged; skip.")
        return

    status = checks_status(repo, pr_number)
    print(f"PR #{pr_number} checks: {status}")

    if status == "pending":
        print("Checks still running; wait for next PR Check completion.")
        return

    if status == "success":
        try:
            merge_pull_request(repo, pr_number)
            post_merge_comment(repo, pr_number, issue_number)
            print(f"Merged PR #{pr_number} (closes #{issue_number}).")
        except subprocess.CalledProcessError as exc:
            print(f"Merge failed for PR #{pr_number}: {exc}")
            _gh(
                [
                    "pr",
                    "comment",
                    str(pr_number),
                    "--repo",
                    repo,
                    "--body",
                    f"Automerge failed for #{pr_number}: `{exc}`. "
                    "Check branch protection or merge conflicts.\n\n"
                    "---\n_[pr-bot](scripts/pr-bot/README.md)_",
                ]
            )
        return

    if status == "failure":
        attempts = count_fix_attempts(repo, issue_number)
        if attempts >= MAX_FIX_ATTEMPTS:
            print(f"Max fix attempts ({MAX_FIX_ATTEMPTS}) reached for #{issue_number}.")
            post_fix_limit_comment(repo, pr_number, issue_number, attempts)
            return
        print(f"Dispatching issue-bot fix for #{issue_number} (attempt {attempts + 1}).")
        dispatch_issue_bot_fix(repo, issue_number, pr_number)
        return

    print(f"Checks status {status!r}; no automerge action.")
