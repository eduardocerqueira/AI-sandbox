"""Post review-steward comments on open PRs (no auto-merge)."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
BOT_MARKER = "<!-- pr-bot:steward -->"


def _gh(args: list[str]) -> str:
    return subprocess.check_output(["gh", *args], cwd=REPO_ROOT, text=True)


def _summarize_checks(repo: str, pr_number: int) -> str:
    try:
        raw = _gh(
            [
                "pr",
                "checks",
                str(pr_number),
                "--repo",
                repo,
                "--json",
                "name,state,conclusion",
            ]
        )
        checks = json.loads(raw)
    except subprocess.CalledProcessError:
        return "_Could not load checks._"

    if not checks:
        return "No checks reported yet."

    lines = []
    for check in checks:
        state = check.get("conclusion") or check.get("state") or "?"
        lines.append(f"- **{check.get('name', '?')}**: {state}")
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


def _build_comment(
    repo: str,
    pr: dict,
) -> str:
    number = pr["number"]
    checks = _summarize_checks(repo, number)
    diff_stat = _gh(
        ["pr", "diff", str(number), "--repo", repo, "--stat"]
    ).strip()[:4000]

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
    parts.extend(
        [
            "",
            "### Merge",
            "Human merge only — PR bot does not auto-merge.",
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--max-prs", type=int, default=5)
    args = parser.parse_args()

    repo = os.environ.get("GITHUB_REPOSITORY", "")
    if not repo and not args.dry_run:
        raise SystemExit("GITHUB_REPOSITORY required")

    if args.dry_run:
        print("[dry-run] would review open PRs")
        return

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
            str(args.max_prs),
        ]
    )
    prs = json.loads(raw)

    for pr in prs:
        n = pr["number"]
        if _already_commented(repo, n):
            print(f"Skip PR #{n} (steward comment exists)")
            continue
        comment = _build_comment(repo, pr)
        _gh(["pr", "comment", str(n), "--repo", repo, "--body", comment])
        print(f"Commented on PR #{n}")


if __name__ == "__main__":
    main()
