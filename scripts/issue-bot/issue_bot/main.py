"""Triage agent-labeled issues, post a plan, and open an implementation PR (v2)."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from issue_bot.fix import fix_pull_request
from issue_bot.implement import open_implementation_pr

REPO_ROOT = Path(__file__).resolve().parents[3]
LABEL_AGENT = "agent"
LABEL_PROGRESS = "agent-in-progress"
LABEL_DONE = "agent-pr-opened"


def _gh(args: list[str]) -> str:
    return subprocess.check_output(["gh", *args], cwd=REPO_ROOT, text=True)


def _load_issue(repo: str, number: int) -> dict | None:
    try:
        raw = _gh(
            [
                "issue",
                "view",
                str(number),
                "--repo",
                repo,
                "--json",
                "number,title,body,labels,url",
            ]
        )
        return json.loads(raw)
    except subprocess.CalledProcessError:
        return None


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
        if LABEL_PROGRESS in labels or LABEL_DONE in labels:
            continue
        return issue
    return None


def _has_open_bot_pr(repo: str, issue_number: int) -> bool:
    prefix = f"issue-bot/{issue_number}-"
    try:
        raw = _gh(
            [
                "pr",
                "list",
                "--repo",
                repo,
                "--state",
                "open",
                "--json",
                "headRefName",
                "--limit",
                "30",
            ]
        )
        return any(
            (pr.get("headRefName") or "").startswith(prefix) for pr in json.loads(raw)
        )
    except subprocess.CalledProcessError:
        return False


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
    return base + plan + "\n\n---\n_Automated by issue-bot (plan + implementation PR)._"


def _comment(repo: str, number: int, body: str) -> None:
    _gh(["issue", "comment", str(number), "--repo", repo, "--body", body])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--plan-only",
        action="store_true",
        help="Post plan comment only; do not generate a PR",
    )
    parser.add_argument(
        "--issue",
        type=int,
        default=None,
        help="Process a specific issue number (for fix mode or manual runs)",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Push a CI fix to the open issue-bot PR for --issue",
    )
    parser.add_argument(
        "--pr",
        type=int,
        default=None,
        help="PR number to fix (optional; inferred from issue branch)",
    )
    args = parser.parse_args()

    repo = os.environ.get("GITHUB_REPOSITORY", "")
    if not repo and not args.dry_run:
        print("GITHUB_REPOSITORY required", file=sys.stderr)
        sys.exit(1)

    if args.dry_run:
        print("[dry-run] would pick an agent-labeled issue, plan, and open PR")
        return

    if args.fix:
        if args.issue is None:
            print("--fix requires --issue", file=sys.stderr)
            sys.exit(1)
        issue = _load_issue(repo, args.issue)
        if not issue:
            print(f"Issue #{args.issue} not found.", file=sys.stderr)
            sys.exit(1)
        ok = fix_pull_request(repo, issue, pr_number=args.pr, dry_run=args.dry_run)
        sys.exit(0 if ok else 1)

    issue = _load_issue(repo, args.issue) if args.issue else _pick_issue(repo)
    if not issue:
        print("No open agent issues to process.")
        return

    number = issue["number"]
    print(f"Processing issue #{number}: {issue['title']}")

    if _has_open_bot_pr(repo, number):
        print(f"Skip #{number}: open issue-bot PR already exists")
        return

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

    plan = _plan_comment(issue)
    _comment(repo, number, plan)

    if args.plan_only or os.environ.get("ISSUE_BOT_PLAN_ONLY", "").lower() in {"1", "true"}:
        print(f"Plan posted for #{number} (implementation skipped).")
        return

    result = open_implementation_pr(repo, issue, plan, dry_run=False)
    if result:
        _gh(
            [
                "issue",
                "edit",
                str(number),
                "--repo",
                repo,
                "--add-label",
                LABEL_DONE,
            ]
        )
        follow = (
            f"Opened implementation branch `{result}` for this issue.\n\n"
            "A pull request should appear shortly (or was created by `gh pr create` locally).\n\n"
            f"_Issue-bot v2 — closes #{number} when the PR merges._"
        )
        _comment(repo, number, follow)
        print(f"Implementation pushed for #{number}")
    else:
        skip = (
            "Could not auto-implement this issue (missing API key, invalid LLM output, "
            "or disallowed paths). Use the plan above and open a PR manually.\n\n"
            f"_Issue-bot v2 — see [docs/agents.md](docs/agents.md)._"
        )
        _comment(repo, number, skip)

    print(f"Updated issue #{number}")


if __name__ == "__main__":
    main()
