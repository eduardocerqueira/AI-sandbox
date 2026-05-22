# PR steward

Reviews **open pull requests** and posts a summary comment. Does **not** merge (by design).

## v1 behavior

- Lists open PRs (max 5 per run).
- Waits for GitHub check conclusions.
- Posts a checklist comment: checks status, size, suggested review focus.
- Optional OpenAI summary when `OPENAI_API_KEY` is set.

## Auto-merge

**Not enabled.** Merging requires a human (or a future v2 with explicit `automerge` label + branch protection).

## Workflow

[`.github/workflows/pr-bot.yml`](../../.github/workflows/pr-bot.yml) — Saturdays 08:00 UTC, and on `pull_request` synchronize.
