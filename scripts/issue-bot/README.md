# Issue worker

Works on **open issues labeled [`agent`](https://docs.github.com/en/issues/using-labels-and-milestones-to-track-work/managing-labels)**.

## v1 behavior

1. Picks the oldest open `agent` issue without label `agent-in-progress`.
2. Adds `agent-in-progress` and posts a short plan comment (OpenAI if `OPENAI_API_KEY` is set).
3. If the issue title starts with **`agent-fix:`**, attempts a minimal code + PR flow (best-effort; may skip on failure).

## How to use

Create an issue and add label **`agent`**. For auto-fix attempts, use title:

```text
agent-fix: short description of the change
```

Describe files, expected behavior, and acceptance criteria in the body.

## Workflow

[`.github/workflows/issue-bot.yml`](../../.github/workflows/issue-bot.yml) — Fridays 08:00 UTC, and when issues are opened/labeled.

## v2 (TODO)

- Close issue when linked PR merges (`pull_request` closed event).
- Richer code edits via dedicated prompts per language.
