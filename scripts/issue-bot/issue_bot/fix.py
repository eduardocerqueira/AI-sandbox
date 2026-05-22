"""Push CI fixes to an existing issue-bot PR branch."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

from issue_bot.git_ops import commit_and_push, configure_bot_git
from issue_bot.implement import _parse_implementation
from issue_bot.paths import apply_file_changes, read_context_files

REPO_ROOT = Path(__file__).resolve().parents[3]
FIX_MARKER_PREFIX = "<!-- issue-bot:fix-attempt:"


def _gh(args: list[str]) -> str:
    return subprocess.check_output(["gh", *args], cwd=REPO_ROOT, text=True)


def _git(*args: str) -> None:
    subprocess.run(["git", *args], cwd=REPO_ROOT, check=True, text=True)


def _failed_checks_summary(repo: str, pr_number: int) -> str:
    result = subprocess.run(
        [
            "gh",
            "pr",
            "checks",
            str(pr_number),
            "--repo",
            repo,
            "--json",
            "name,state,bucket,link",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        return result.stderr or result.stdout or "Could not load PR checks."

    lines: list[str] = []
    for check in json.loads(result.stdout):
        name = check.get("name", "?")
        if name.lower() == "approve":
            continue
        state = check.get("state") or check.get("bucket") or "?"
        if str(state).upper() in {"PASS", "SUCCESS", "SKIPPED", "NEUTRAL"}:
            continue
        link = check.get("link") or ""
        lines.append(f"- **{name}**: {state}" + (f" ({link})" if link else ""))
    return "\n".join(lines) if lines else "No failing checks listed (PR may need a new push)."


def _checkout_pr_branch(repo: str, pr_number: int) -> str:
    raw = _gh(
        [
            "pr",
            "view",
            str(pr_number),
            "--repo",
            repo,
            "--json",
            "headRefName",
        ]
    )
    branch = json.loads(raw)["headRefName"]
    _git("fetch", "origin", branch)
    _git("checkout", branch)
    _git("pull", "--ff-only", "origin", branch)
    return branch


def _generate_fix(
    issue: dict,
    *,
    failed_checks: str,
    api_key: str,
) -> dict[str, Any]:
    from openai import OpenAI

    context = read_context_files(
        ["README.md", "docs/agents.md"] + _paths_from_issue(issue),
    )
    context_block = "\n\n".join(
        f"### {path}\n```\n{content}\n```" for path, content in context.items()
    )

    user = (
        f"Issue #{issue['number']}: {issue['title']}\n\n"
        f"## Issue body\n{issue.get('body') or '(empty)'}\n\n"
        f"## Failed CI checks\n{failed_checks}\n\n"
        f"## File context\n{context_block}\n\n"
        "Fix the code so CI passes. Output JSON only with files, commit_message, pr_summary."
    )

    system = (
        "You fix failing CI on an existing pull request for the AI-sandbox monorepo. "
        "Respond with JSON: files (full content), commit_message, pr_summary. "
        "Only modify files needed to fix the failure. Same path rules as issue-bot implementation."
    )

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=os.environ.get("ISSUE_BOT_MODEL", "gpt-4o-mini"),
        temperature=0.2,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return _parse_implementation(response.choices[0].message.content or "")


def _paths_from_issue(issue: dict) -> list[str]:
    from issue_bot.paths import paths_mentioned_in_text

    text = (issue.get("body") or "") + "\n" + (issue.get("title") or "")
    return paths_mentioned_in_text(text)[:8]


def find_open_pr_for_issue(repo: str, issue_number: int) -> int | None:
    prefix = f"issue-bot/{issue_number}-"
    raw = _gh(
        [
            "pr",
            "list",
            "--repo",
            repo,
            "--state",
            "open",
            "--json",
            "number,headRefName",
            "--limit",
            "30",
        ]
    )
    for pr in json.loads(raw):
        if (pr.get("headRefName") or "").startswith(prefix):
            return int(pr["number"])
    return None


def fix_pull_request(
    repo: str,
    issue: dict,
    *,
    pr_number: int | None = None,
    dry_run: bool = False,
) -> bool:
    """Apply a fix commit on the issue-bot PR branch. Returns True on success."""
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        print("OPENAI_API_KEY required for fix mode.")
        return False

    number = issue["number"]
    pr_number = pr_number or find_open_pr_for_issue(repo, number)
    if pr_number is None:
        print(f"No open issue-bot PR for issue #{number}.")
        return False

    failed = _failed_checks_summary(repo, pr_number)
    print(f"Failed checks for PR #{pr_number}:\n{failed}")

    try:
        data = _generate_fix(issue, failed_checks=failed, api_key=api_key)
        written = apply_file_changes(data["files"])
    except (ValueError, json.JSONDecodeError, OSError) as exc:
        print(f"Fix generation failed: {exc}")
        return False

    if not written:
        print("No files to write for fix.")
        return False

    if dry_run:
        print(f"[dry-run] would fix PR #{pr_number}: {written}")
        return True

    configure_bot_git()
    branch = _checkout_pr_branch(repo, pr_number)
    commit_msg = data.get("commit_message") or f"issue-bot: fix CI for #{number}"
    commit_and_push(branch, written, commit_msg)

    attempt = _next_attempt_number(repo, number)
    _gh(
        [
            "issue",
            "comment",
            str(number),
            "--repo",
            repo,
            "--body",
            f"{FIX_MARKER_PREFIX}{attempt} -->\n"
            f"Pushed CI fix to PR #{pr_number} (`{branch}`). "
            f"Waiting for PR Check and automerge.\n\n"
            "---\n_Issue-bot fix mode_",
        ]
    )
    print(f"Fix pushed to {branch} for PR #{pr_number}.")
    return True


def _next_attempt_number(repo: str, issue_number: int) -> int:
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
        return 1
    count = sum(1 for line in bodies.splitlines() if FIX_MARKER_PREFIX in line)
    return count + 1
