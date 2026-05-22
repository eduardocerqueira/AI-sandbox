# Experiment agent

Uses [`docs/`](../../docs/) (learning resources, experiment ideas, getting started) to pick a topic **every other day**, then:

1. **Opens a GitHub issue** with the proposal (`experiment-agent`, `agent-in-progress` labels).
2. **Does the work** — new research doc under `docs/experiments/` or a minimal Python app from `apps/python/_template`.
3. **Comments on the issue** and **opens a PR** with `Closes #<issue>`.
4. **Closes the issue** when the PR is merged ([`experiment-agent-close.yml`](../../.github/workflows/experiment-agent-close.yml)).

## Schedule

[`.github/workflows/experiment-agent.yml`](../../.github/workflows/experiment-agent.yml) — **08:00 UTC on odd calendar days** (`1-31/2`), plus manual **workflow_dispatch**.

Skips a run if another open issue has `experiment-agent` + `agent-in-progress`.

## Secrets

- **`OPENAI_API_KEY`** (required)
- **`GITHUB_TOKEN`** — default; needs permission to create issues and PRs

## Local

```bash
cd scripts/experiment-agent && pip install -e .
export OPENAI_API_KEY=...
experiment-agent --dry-run
```

## Review flow

PR Check and PR steward run on the PR. **No auto-merge** — merge when ready; the close workflow finishes the issue.
