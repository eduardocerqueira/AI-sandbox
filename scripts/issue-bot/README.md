# Issue worker

Works on **open issues labeled [`agent`](https://docs.github.com/en/issues/using-labels-and-milestones-to-track-work/managing-labels)**.

## v2 behavior

1. Picks the oldest open `agent` issue without `agent-in-progress` or `agent-pr-opened`.
2. Adds `agent-in-progress` and posts a **plan** comment (OpenAI).
3. **Implements** the issue via LLM-generated file updates (docs, README, scripts, apps, workflows).
4. Pushes branch `issue-bot/<number>-<slug>` and opens a PR (`Closes #<issue>` when merged).

Skips issues that already have an open `issue-bot/*` PR.

## How to use

Create an issue, add label **`agent`**, and describe acceptance criteria and target files.

Optional title prefix (no longer required for implementation):

```text
agent-fix: short description of the change
```

## Flags and env

| Flag / variable | Effect |
|-----------------|--------|
| `--dry-run` | Log only |
| `--plan-only` | Plan comment; no PR |
| `ISSUE_BOT_SKIP_IMPLEMENT=1` | Plan only |
| `ISSUE_BOT_PLAN_ONLY=1` | Plan only |
| `ISSUE_BOT_MODEL` | OpenAI model (default `gpt-4o-mini`) |
| `ISSUE_BOT_BASE_BRANCH` | PR base (default `main`) |

## Workflow

[`.github/workflows/issue-bot.yml`](../../.github/workflows/issue-bot.yml) — Fridays 08:00 UTC, `issues` labeled `agent`, manual dispatch.

Requires **`OPENAI_API_KEY`**. Optional **`ISSUE_BOT_GH_TOKEN`** if `GITHUB_TOKEN` cannot open PRs.

The workflow checks out the **default branch** before running (same pattern as PR steward).

## Local

```bash
cd scripts/issue-bot && pip install -e ".[dev]"
export OPENAI_API_KEY=sk-...
export GITHUB_REPOSITORY=owner/AI-sandbox
issue-bot --dry-run
issue-bot --plan-only   # no PR
```

## Limits

- Allowed write paths: `docs/`, `README.md`, `CONTRIBUTING.md`, `apps/`, `scripts/`, `.github/workflows/`
- No `.env`, `TODO.md`, or secrets
- Complex code changes may fail review — keep issues scoped
- Merging the PR closes the issue via `Closes #n` in the PR body
