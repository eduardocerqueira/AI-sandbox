# PR steward

Reviews **open pull requests** and posts a summary comment. With the **`automerge`** label on the linked issue, can **squash-merge** when checks pass or **dispatch issue-bot** to fix CI failures.

## v1 behavior

- **After PR Check finishes** on a PR (`workflow_run`): comments on **that PR** — steward + automerge logic when applicable.
- **On schedule / manual run**: reviews up to 5 open PRs.
- Posts a checklist comment: checks status, diff stat, optional OpenAI summary (`<!-- pr-bot:steward -->`).
- Skips duplicate steward comments unless the linked issue has **`automerge`** (then refreshes each run).

## Automerge (`automerge` issue label)

Requires the PR body to include `Closes #<issue>` and the issue to have label **`automerge`** (in addition to **`agent`** for issue-bot PRs).

| PR Check result | Action |
|-----------------|--------|
| All pass | Squash-merge PR, delete branch; issue closes via `Closes #n` |
| Failure | Dispatch **Issue bot** fix workflow (up to **3** attempts) |
| Pending | Wait for next PR Check completion |

Uses **`BOT_GH_TOKEN`** (or legacy bot PAT secrets) for merge and workflow dispatch. Branch protection may still require the PAT account to be allowed to bypass or satisfy rules.

## Workflow

[`.github/workflows/pr-bot.yml`](../../.github/workflows/pr-bot.yml) — Saturdays 08:00 UTC, and after [`pr-check.yml`](../../.github/workflows/pr-check.yml) completes on a PR.

Pending runs from other workflows are auto-approved by [`approve-pending-actions.yml`](../../.github/workflows/approve-pending-actions.yml) when possible.

The workflow checks out the **default branch** before `pip install -e ./scripts/pr-bot`, so steward logic always matches `main` even when reviewing an older PR branch.
