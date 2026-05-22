"""Triage and optionally work agent-labeled GitHub issues."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
LABEL_AGENT = "agent"
LABEL_PROGRESS = "agent-in-progress"
FIX_PREFIX = "agent-fix:"


def _gh(args: list[str]) -> str:
    return subprocess.check_output(["gh", *args], cwd=REPO_ROOT, text=True)


def _pick_issue(repo: str) -> dict | None:
    raw = _gh(
        [
            "issue",
            "list",
            "--repo",
            repo,
            "--label",
            LABEL_AGENT,
            "--state",
            "open",
            "--json",
            "number,title,body,labels,url",
            "--limit",
            "20",
        ]
    )
    issues = json.loads(raw)
    for issue in issues:
        labels = {lb["name"] for lb in issue.get("labels", [])}
        if LABEL_PROGRESS in labels:
            continue
        return issue
    return None


def _plan_comment(issue: dict) -> str:
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    base = (
        f"## Agent plan for #{issue['number']}\n\n"
        f"**Title:** {issue['title']}\n\n"
    )
    if not api_key:
        return (
            base
            + "No `OPENAI_API_KEY` — manual triage only.\n\n"
            "- [ ] Confirm scope\n"
            "- [ ] Implement + tests\n"
            "- [ ] Open PR and link here\n"
        )

    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=os.environ.get("ISSUE_BOT_MODEL", "gpt-4o-mini"),
        temperature=0.2,
        messages=[
            {
                "role": "system",
                "content": (
                    "You triage GitHub issues for a polyglot monorepo (Python/Node/Go/TS). "
                    "Output markdown: summary, suggested files, steps, risks. "
                    "Do not claim work is done."
                ),
            },
            {
                "role": "user",
                "content": f"Title: {issue['title']}\n\n{issue.get('body') or ''}",
            },
        ],
    )
    plan = (response.choices[0].message.content or "").strip()
    return base + plan + "\n\n---\n_Automated by issue-bot v1 (plan only)._"


def _try_fix_pr(repo: str, issue: dict) -> None:
    """Best-effort: only runs for agent-fix: titles; posts result comment."""
    title = issue["title"]
    if not title.lower().startswith(FIX_PREFIX):
        return

    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        _gh(
            [
                "issue",
                "comment",
                str(issue["number"]),
                "--repo",
                repo,
                "--body",
                "Skipping auto-fix: `OPENAI_API_KEY` not configured.",
            ]
        )
        return

    comment = (
        f"Auto-fix for `{FIX_PREFIX}` issues is not fully implemented yet. "
        f"Use the plan above, or run test-bot / open a PR manually.\n\n"
        f"_Issue bot v1 — see [docs/agents.md](docs/agents.md)._"
    )
    _gh(
        [
            "issue",
            "comment",
            str(issue["number"]),
            "--repo",
            repo,
            "--body",
            comment,
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    repo = os.environ.get("GITHUB_REPOSITORY", "")
    if not repo and not args.dry_run:
        print("GITHUB_REPOSITORY required", file=sys.stderr)
        sys.exit(1)

    if args.dry_run:
        print("[dry-run] would pick an agent-labeled issue and comment")
        return

    issue = _pick_issue(repo)
    if not issue:
        print("No open agent issues to process.")
        return

    number = issue["number"]
    print(f"Processing issue #{number}: {issue['title']}")

    _gh(
        [
            "issue",
            "edit",
            str(number),
            "--repo",
            repo,
            "--add-label",
            LABEL_PROGRESS,
        ]
    )

    body = _plan_comment(issue)
    _gh(["issue", "comment", str(number), "--repo", repo, "--body", body])
    _try_fix_pr(repo, issue)
    print(f"Updated issue #{number}")


if __name__ == "__main__":
    main()
