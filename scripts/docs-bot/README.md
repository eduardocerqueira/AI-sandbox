# Docs bot

Keeps [`apps/README.md`](../../apps/README.md) in sync with folders under `apps/` (auto-generated table between HTML comment markers).

Optional OpenAI pass polishes the table when `OPENAI_API_KEY` is set.

## Workflow

[`.github/workflows/docs-bot.yml`](../../.github/workflows/docs-bot.yml) — Mondays 08:00 UTC.

## Local

```bash
cd scripts/docs-bot && pip install -e .
DOCS_BOT_DRY_RUN=1 docs-bot --dry-run
```
