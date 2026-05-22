# Contributing (personal sandbox)

This repo is for your own experiments. These conventions keep the monorepo easy to navigate as it grows.

Setup and run commands: [docs/getting-started.md](docs/getting-started.md).  
Agent skills (lockfile, `.agents/`): [docs/skills.md](docs/skills.md).

## CI

GitHub Actions run on every PR ([`.github/workflows/pr-check.yml`](.github/workflows/pr-check.yml)) and nightly ([`.github/workflows/nightly.yml`](.github/workflows/nightly.yml)). When you add an app with tests, extend the matching job matrix in both workflows.

**Test bot** ([`scripts/test-bot/README.md`](scripts/test-bot/README.md)) runs weekly or on demand ([`.github/workflows/test-bot.yml`](.github/workflows/test-bot.yml)): it discovers files without tests, generates them via OpenAI, runs app test suites, and opens a PR. Requires the `OPENAI_API_KEY` repository secret.

## Adding a new app

1. **Choose a home** under `apps/<language>/` (or add a new top-level language folder if needed).
2. **Create a folder** with a `kebab-case` name, e.g. `apps/python/crewai-hello`.
3. **Copy a template** from `apps/<language>/_template/` when one exists.
4. **Add a README** in the app folder with:
   - What it demonstrates (one paragraph)
   - Prerequisites (runtime version, GPU, API keys)
   - Setup (`install` commands)
   - Run (`how to execute`)
   - Optional: link to a course or doc you are following
5. **Add `.env.example`** if the app needs API keys or config.
6. **Keep dependencies local** — `pyproject.toml`, `package.json`, `go.mod`, or `pom.xml` inside the app, not at repo root (unless you later adopt a workspace tool on purpose).

## What not to commit

- `.env` files with real keys
- `.agents/` (restore from root `skills-lock.json` — see [docs/skills.md](docs/skills.md))
- Large model weights, datasets, or checkpoints (use `.gitignore` patterns or download scripts)
- `node_modules/`, virtualenvs, `target/`, compiled binaries
- Extra `skills-lock.json` files inside apps or templates (only the repo root lockfile)

## Optional: shared code

If multiple apps need the same utility, introduce `packages/` or `libs/` only when duplication becomes painful. Until then, copy-paste is fine for learning.

## Language-specific notes

| Language | Default package manager | Template location |
|----------|-------------------------|-------------------|
| Python | `uv` or `pip` + venv | `apps/python/_template/` |
| TypeScript | `npm` / `pnpm` | `apps/typescript/_template/` |
| Node (JS) | `npm` | `apps/node/_template/` |
| Go | `go mod` | `apps/go/_template/` |
| Java | Maven or Gradle | `apps/java/_template/` |
