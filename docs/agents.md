# Scheduled repository agents

Automation that runs **at least once per week** (staggered cron) or on demand. Same pattern as [test-bot](../scripts/test-bot/README.md): GitHub Actions + scripts + `gh` CLI.

## Overview

| Agent | Workflow | Schedule (UTC) | Secret(s) | Opens |
|-------|----------|----------------|-----------|--------|
| [Docs bot](../scripts/docs-bot/README.md) | [`docs-bot.yml`](../.github/workflows/docs-bot.yml) | Mon 08:00 | `OPENAI_API_KEY` | PR |
| [CVE scan](../scripts/cve-scan/README.md) | [`cve-scan.yml`](../.github/workflows/cve-scan.yml) | Wed 08:00 | — | Issue (if HIGH/CRITICAL) |
| [Issue worker](../scripts/issue-bot/README.md) | [`issue-bot.yml`](../.github/workflows/issue-bot.yml) | Fri 08:00 | `OPENAI_API_KEY` | PR (label `agent`) |
| [PR steward](../scripts/pr-bot/README.md) | [`pr-bot.yml`](../.github/workflows/pr-bot.yml) | Sat 08:00 | `OPENAI_API_KEY` (optional) | Comment / labels |
| Test bot | [`test-bot.yml`](../.github/workflows/test-bot.yml) | Sun 07:00 | `OPENAI_API_KEY` | PR |

Manual run: **Actions** → pick workflow → **Run workflow**.

## Safety defaults

- **No auto-merge** in PR steward v1 — human merge only.
- **Issue worker** only picks issues with label [`agent`](https://github.com/eduardocerqueira/ai-sandbox/issues?q=is%3Aissue+label%3Aagent) (you add it).
- **CVE scan** opens at most one tracking issue per run; skips if an open CVE issue already exists.
- Bots use `github-actions[bot]` for git commits.

## Setup checklist

1. Enable Actions on the repo.
2. Add repository secret **`OPENAI_API_KEY`** (docs, test, issue bots; optional for PR steward).
3. For issue bot: create label **`agent`** and open issues you want automated (keep scope small).
4. Optional: branch protection requiring **PR Check** before merge.

## Adding a new agent

1. Add `scripts/<name>/` with README and entrypoint.
2. Add `.github/workflows/<name>.yml` with `schedule` + `workflow_dispatch`.
3. Document here and in root [TODO.md](../TODO.md).

## Limits (honest)

| Goal | v1 support | Notes |
|------|------------|--------|
| Update all docs from code | Partial | Docs bot syncs app catalog tables; deep rewrites need review |
| CVE → issue | Yes | Trivy filesystem scan; dev dependency noise possible |
| Fix issues end-to-end | Best-effort | Needs clear issue text + `agent` label; may skip hard tasks |
| Review + merge PR | Review only | Comments and checklist; **you** merge |

Hugging Face Jobs can run batch Python but do not replace GitHub for issues/PRs — keep orchestration in Actions.
