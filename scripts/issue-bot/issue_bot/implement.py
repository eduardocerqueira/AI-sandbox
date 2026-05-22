"""Generate and apply file changes for an agent issue, then open a PR."""

from __future__ import annotations

import json
import os
import re
from typing import Any

from issue_bot.git_ops import (
    branch_name,
    commit_and_push,
    configure_bot_git,
    create_branch,
    emit_pr_outputs,
    pr_body,
)
from issue_bot.paths import (
    apply_file_changes,
    paths_mentioned_in_text,
    read_context_files,
)

IMPLEMENT_SYSTEM = """You implement GitHub issues for the AI-sandbox monorepo.

Respond with JSON only (no markdown fence), shape:
{
  "files": [{"path": "repo-relative/path", "content": "full new file content"}],
  "commit_message": "short imperative commit subject",
  "pr_summary": "1-3 sentence markdown summary for the PR body"
}

Rules:
- Modify only files required by the issue; prefer editing existing files over creating many new ones.
- Each path is relative to the repo root (e.g. docs/agents.md, README.md).
- Provide COMPLETE file content for every path listed (not a diff).
- Allowed areas: docs/, README.md, CONTRIBUTING.md, apps/, scripts/, .github/workflows/
- Never write: .env, TODO.md, secrets, credentials, or binary content.
- Match existing markdown style and relative link conventions.
- If the issue is documentation-only, do not change application runtime code unless explicitly requested.
"""


def _default_context_paths(issue_body: str, plan: str) -> list[str]:
    hinted = paths_mentioned_in_text(issue_body + "\n" + plan)
    defaults = ["README.md", "docs/README.md", "docs/agents.md", "CONTRIBUTING.md"]
    seen: set[str] = set()
    out: list[str] = []
    for p in hinted + defaults:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


def _parse_implementation(raw: str) -> dict[str, Any]:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    data = json.loads(text)
    if not isinstance(data.get("files"), list) or not data["files"]:
        raise ValueError("LLM response missing non-empty files array")
    return data


def generate_implementation(
    issue: dict,
    plan: str,
    *,
    api_key: str,
) -> dict[str, Any]:
    from openai import OpenAI

    context_paths = _default_context_paths(issue.get("body") or "", plan)
    context = read_context_files(context_paths)

    context_block = "\n\n".join(
        f"### {path}\n```\n{content}\n```" for path, content in context.items()
    )

    user = (
        f"Issue #{issue['number']}: {issue['title']}\n\n"
        f"## Issue body\n{issue.get('body') or '(empty)'}\n\n"
        f"## Plan\n{plan}\n\n"
        f"## Current file context\n{context_block or '(no files loaded)'}\n\n"
        "Implement the issue. Output JSON only."
    )

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=os.environ.get("ISSUE_BOT_MODEL", "gpt-4o-mini"),
        temperature=0.2,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": IMPLEMENT_SYSTEM},
            {"role": "user", "content": user},
        ],
    )
    raw = response.choices[0].message.content or ""
    return _parse_implementation(raw)


def open_implementation_pr(
    repo: str,
    issue: dict,
    plan: str,
    *,
    dry_run: bool = False,
) -> str | None:
    """Apply changes and push branch. Returns PR URL on local gh create, else branch name."""
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None
    if os.environ.get("ISSUE_BOT_SKIP_IMPLEMENT", "").lower() in {"1", "true", "yes"}:
        print("ISSUE_BOT_SKIP_IMPLEMENT set; skipping implementation.")
        return None

    number = issue["number"]
    title = issue["title"]
    base = os.environ.get("ISSUE_BOT_BASE_BRANCH", "main")

    print(f"Generating implementation for issue #{number} …")
    try:
        data = generate_implementation(issue, plan, api_key=api_key)
        written = apply_file_changes(data["files"])
    except (ValueError, json.JSONDecodeError, OSError) as exc:
        print(f"Implementation failed: {exc}")
        return None

    if not written:
        print("No files written.")
        return None

    branch = branch_name(number, title)
    commit_msg = data.get("commit_message") or f"issue-bot: implement #{number}"
    summary = data.get("pr_summary") or f"Implements issue #{number}."
    body = pr_body(number, title, summary, plan)

    if dry_run:
        print(f"[dry-run] would commit {written} on {branch}")
        return None

    configure_bot_git()
    create_branch(branch, base)
    commit_and_push(branch, written, commit_msg)

    pr_title = f"issue-bot: {title[:72]}"
    if os.environ.get("GITHUB_ACTIONS", "").lower() == "true":
        emit_pr_outputs(branch, pr_title, body)
        print(f"Pushed {branch}; workflow will open PR.")
        return branch

    import subprocess

    from issue_bot.paths import REPO_ROOT

    subprocess.run(
        [
            "gh",
            "pr",
            "create",
            "--repo",
            repo,
            "--title",
            pr_title,
            "--body",
            body,
            "--head",
            branch,
            "--base",
            base,
        ],
        cwd=REPO_ROOT,
        check=True,
        text=True,
    )
    return branch
