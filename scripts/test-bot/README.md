# Test bot

Automated agent that discovers source files without unit tests in CI-covered apps, generates tests with an LLM, runs the same checks as [PR Check](../../.github/workflows/pr-check.yml), and opens a pull request.

## How it works

1. **Discover** — scan `apps/python`, `apps/node`, `apps/go`, and `apps/typescript` apps listed in CI (skip `_template` and entry/UI-only files).
2. **Generate** — call OpenAI (`OPENAI_API_KEY`) to write one test file per target (mocked APIs, no live HF calls).
3. **Verify** — run `pytest`, `npm test`, or `go test` for each affected app.
4. **PR** — commit on `test-bot/<timestamp>` and open a PR with `gh`.

## Run locally

```bash
cd scripts/test-bot
python -m pip install -e ".[dev]"
export OPENAI_API_KEY=sk-...

# Preview only
TEST_BOT_DRY_RUN=1 test-bot --max-targets 1

# Full run (needs clean git state + gh auth)
test-bot --max-targets 2
```

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | — | Required for generation |
| `TEST_BOT_MODEL` | `gpt-4o-mini` | OpenAI model id |
| `TEST_BOT_MAX_TARGETS` | `2` | Max files per run |
| `TEST_BOT_DRY_RUN` | — | Set `1` to skip writes, git, and PR |
| `TEST_BOT_BASE_BRANCH` | `main` | PR base branch |

## GitHub Actions

Workflow: [`.github/workflows/test-bot.yml`](../../.github/workflows/test-bot.yml)

- **Schedule:** Sundays 07:00 UTC
- **Manual:** Actions → Test bot → Run workflow
- **Secret:** `OPENAI_API_KEY` (repository secret)

Inputs: `max_targets` (default 2), `dry_run` (default false).

## Adding a new CI app

Update `CI_APPS` in `test_bot/discover.py` and the matrices in `pr-check.yml` / `nightly.yml`.
