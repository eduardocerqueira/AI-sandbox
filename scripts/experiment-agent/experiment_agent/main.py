"""Docs-guided experiment agent: issue → work → PR."""

from __future__ import annotations

import argparse
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from experiment_agent import github_ops
from experiment_agent.apply import apply_plan
from experiment_agent.plan import WorkPlan, plan_work

REPO_ROOT = Path(__file__).resolve().parents[3]
BOT_MARKER = "<!-- experiment-agent:summary -->"


def _git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        check=check,
        text=True,
        capture_output=True,
    )


def _github_output(name: str, value: str) -> None:
    path = os.environ.get("GITHUB_OUTPUT")
    if not path:
        return
    with open(path, "a", encoding="utf-8") as handle:
        if "\n" in value:
            handle.write(f"{name}<<EOF\n{value}\nEOF\n")
        else:
            handle.write(f"{name}={value}\n")


def _proposal_issue_body(plan: WorkPlan) -> str:
    return f"""## Proposal (experiment-agent)

{plan.issue_body}

### Rationale

{plan.rationale}

### Planned deliverable

- **Type:** `{plan.kind}`
- **Doc path:** `{plan.doc_path or "—"}`
- **App slug:** `{plan.app_slug or "—"}`

### Workflow

- [x] Proposal filed by experiment-agent
- [ ] Implementation + PR
- [ ] PR reviewed / merged (PR steward, PR Check)
- [ ] Issue closed after merge

---
_Labels: `experiment-agent`, `agent-in-progress`. Closes via PR body `Closes #<issue>`._
"""


def _completion_comment(plan: WorkPlan, changed: list[str], pr_url: str | None) -> str:
    files = "\n".join(f"- `{p}`" for p in changed) or "- _(none)_"
    pr_line = f"**Pull request:** {pr_url}" if pr_url else "**Pull request:** _(opened by workflow step)_"
    return f"""{BOT_MARKER}

## Work completed

{pr_line}

### Summary

- **Type:** `{plan.kind}`
- **Title:** {plan.title}

### Files

{files}

### Next steps

- PR Check and PR steward will run on the PR.
- After merge, this issue will close automatically.

---
_[experiment-agent](scripts/experiment-agent/README.md)_
"""


def _pr_body(plan: WorkPlan, issue_number: int, changed: list[str]) -> str:
    files = "\n".join(f"- `{p}`" for p in changed)
    return f"""## Summary

{plan.rationale}

Closes #{issue_number}

### Changes

{files}

### Type

`{plan.kind}` — guided by [docs/](docs/) (learning-resources, experiment-ideas).

## Test plan

- [ ] Review content / scaffold quality
- [ ] PR Check passes
- [ ] PR steward comment reviewed

---
*Workflow: `.github/workflows/experiment-agent.yml`*
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Docs-guided experiment agent")
    parser.add_argument("--dry-run", action="store_true", help="Plan only; no issue/PR")
    args = parser.parse_args()

    repo = os.environ.get("GITHUB_REPOSITORY", "").strip()
    if not repo and not args.dry_run:
        raise SystemExit("GITHUB_REPOSITORY is required")

    if args.dry_run:
        plan = plan_work()
        print(f"[dry-run] kind={plan.kind} title={plan.title}")
        print(plan.issue_body[:500])
        return

    if github_ops.has_active_run(repo):
        print("Skip: open experiment-agent issue with agent-in-progress")
        return

    github_ops.ensure_labels(repo)
    plan = plan_work()
    issue_number = github_ops.create_proposal_issue(
        repo,
        plan.title,
        _proposal_issue_body(plan),
    )
    print(f"Created proposal issue #{issue_number}")

    slug = (plan.app_slug or plan.title.lower().replace(" ", "-"))[:40]
    slug = "".join(c if c.isalnum() or c == "-" else "-" for c in slug).strip("-")
    stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M")
    branch = f"experiment-agent/{stamp}-{slug}"

    try:
        changed = apply_plan(plan)
    except Exception as exc:
        github_ops.comment_issue(
            repo,
            issue_number,
            f"## Experiment agent failed\n\n```\n{exc}\n```\n\nIssue left open for retry.",
        )
        raise SystemExit(1) from exc

    _git("checkout", "-b", branch)
    _git("add", "-A")
    _git("commit", "-m", f"experiment-agent: {plan.title}\n\nCloses #{issue_number}")
    _git("push", "-u", "origin", branch)

    pr_body = _pr_body(plan, issue_number, changed)
    base = os.environ.get("EXPERIMENT_AGENT_BASE_BRANCH", "main")

    if os.environ.get("GITHUB_ACTIONS", "").lower() == "true":
        _github_output("branch", branch)
        _github_output("issue_number", str(issue_number))
        _github_output("pr_body", pr_body)
        _github_output("pr_title", f"experiment-agent: {plan.title}")
        github_ops.comment_issue(
            repo,
            issue_number,
            _completion_comment(plan, changed, None),
        )
        print(f"Pushed {branch}; workflow will open PR for #{issue_number}")
        return

    pr = subprocess.run(
        [
            "gh",
            "pr",
            "create",
            "--repo",
            repo,
            "--title",
            f"experiment-agent: {plan.title}",
            "--body",
            pr_body,
            "--head",
            branch,
            "--base",
            base,
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    pr_url = pr.stdout.strip()
    github_ops.comment_issue(
        repo,
        issue_number,
        _completion_comment(plan, changed, pr_url),
    )
    print(pr_url)


if __name__ == "__main__":
    main()
