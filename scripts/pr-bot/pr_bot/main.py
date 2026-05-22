"""Post review-steward comments; optional automerge when the linked issue has label automerge."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path

from pr_bot.automerge import (
    LABEL_AUTOMERGE,
    closes_issue_number,
    issue_has_automerge,
    run_automerge,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
BOT_MARKER = "<!-- pr-bot:steward -->"


def _gh(args: list[str]) -> str:
    return subprocess.check_output(["gh", *args], cwd=REPO_ROOT, text=True)


def _summarize_checks(repo: str, pr_number: int) -> str:
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
            return "No checks reported yet."
        return "_Could not load checks._"

    checks = json.loads(result.stdout)

    if not checks:
        return "No checks reported yet."

    lines = []
    for check in checks:
        state = check.get("state") or check.get("bucket") or "?"
        lines.append(f"- **{check.get('name', '?')}**: {state}")
    return "\n".join(lines)


def _diff_summary(repo: str, pr_number: int) -> str:
    try:
        raw = _gh(
            [
                "pr",
                "view",
                str(pr_number),
                "--repo",
                repo,
                "--json",
                "additions,deletions,changedFiles,files",
            ]
        )
        data = json.loads(raw)
    except subprocess.CalledProcessError:
        return "(could not load diff summary)"

    lines = [
        f"{data.get('changedFiles', 0)} files changed, "
        f"+{data.get('additions', 0)}, -{data.get('deletions', 0)}",
    ]
    for entry in data.get("files") or []:
        path = entry.get("path", "?")
        adds = entry.get("additions", 0)
        dels = entry.get("deletions", 0)
        lines.append(f" {path} | +{adds} -{dels}")
    return "\n".join(lines)


def _ai_summary(title: str, body: str, diff_stat: str) -> str | None:
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None

    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=os.environ.get("PR_BOT_MODEL", "gpt-4o-mini"),
        temperature=0.2,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a code review steward. Short markdown: risk areas, "
                    "what to test, merge readiness. No fluff."
                ),
            },
            {
                "role": "user",
                "content": f"PR: {title}\n\n{body}\n\nDiff stat:\n{diff_stat}",
            },
        ],
    )
    return (response.choices[0].message.content or "").strip()


def _build_comment(repo: str, pr: dict) -> str:
    number = pr["number"]
    checks = _summarize_checks(repo, number)
    diff_stat = _diff_summary(repo, number)[:4000]

    ai = _ai_summary(pr.get("title", ""), pr.get("body") or "", diff_stat)

    parts = [
        BOT_MARKER,
        "## PR steward (automated)",
        "",
        f"**PR:** #{number} — {pr.get('title', '')}",
        "",
        "### Checks",
        checks,
        "",
        "### Diff stat",
        "```",
        diff_stat or "(empty)",
        "```",
    ]
    if ai:
        parts.extend(["", "### Review notes", ai])

    issue_num = closes_issue_number(pr.get("body"))
    automerge = issue_num is not None and issue_has_automerge(repo, issue_num)
    if automerge:
        merge_line = (
            f"**Automerge enabled** — issue #{issue_num} has `{LABEL_AUTOMERGE}`. "
            "PR bot will squash-merge when all checks pass, or dispatch issue-bot to fix CI failures."
        )
    else:
        merge_line = "Human merge only — add label `automerge` on the linked issue to enable auto-merge."

    parts.extend(
        [
            "",
            "### Merge",
            merge_line,
            "",
            "---",
            "_[pr-bot](scripts/pr-bot/README.md)_",
        ]
    )
    return "\n".join(parts)


def _already_commented(repo: str, pr_number: int) -> bool:
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
    return BOT_MARKER in bodies


def _prs_from_event() -> list[dict] | None:
    """When started by pull_request (local/tests), return only the triggering PR."""
    if os.environ.get("GITHUB_EVENT_NAME") != "pull_request":
        return None
    event_path = os.environ.get("GITHUB_EVENT_PATH", "")
    if not event_path:
        return None
    event = json.loads(Path(event_path).read_text(encoding="utf-8"))
    pr = event.get("pull_request")
    if not pr:
        return None
    return [
        {
            "number": pr["number"],
            "title": pr.get("title", ""),
            "body": pr.get("body") or "",
        }
    ]


def _list_open_prs(repo: str, limit: int) -> list[dict]:
    raw = _gh(
        [
            "pr",
            "list",
            "--repo",
            repo,
            "--state",
            "open",
            "--json",
            "number,title,body",
            "--limit",
            str(limit),
        ]
    )
    return json.loads(raw)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--max-prs", type=int, default=5)
    parser.add_argument(
        "--pr",
        type=int,
        default=None,
        help="Review a single PR number (overrides list; set from GITHUB_EVENT)",
    )
    parser.add_argument(
        "--automerge-only",
        action="store_true",
        help="Skip steward comment; only run automerge / fix dispatch",
    )
    args = parser.parse_args()

    repo = os.environ.get("GITHUB_REPOSITORY", "")
    if not repo and not args.dry_run:
        raise SystemExit("GITHUB_REPOSITORY required")

    if args.dry_run:
        print("[dry-run] would review open PRs")
        return

    if args.pr is not None:
        raw = _gh(
            [
                "pr",
                "view",
                str(args.pr),
                "--repo",
                repo,
                "--json",
                "number,title,body",
            ]
        )
        prs = [json.loads(raw)]
    else:
        prs = _prs_from_event()
        if prs is None:
            prs = _list_open_prs(repo, args.max_prs)

    for pr in prs:
        n = pr["number"]
        issue_num = closes_issue_number(pr.get("body"))
        automerge = issue_num is not None and issue_has_automerge(repo, issue_num)
        if _already_commented(repo, n) and not automerge:
            print(f"Skip PR #{n} (steward comment exists)")
        else:
            comment = _build_comment(repo, pr)
            _gh(["pr", "comment", str(n), "--repo", repo, "--body", comment])
            print(f"Commented on PR #{n}")

        if args.automerge_only:
            run_automerge(repo, n, pr.get("body"))
        elif automerge:
            run_automerge(repo, n, pr.get("body"))


if __name__ == "__main__":
    main()
