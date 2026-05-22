# AI Sandbox

**A personal monorepo of small, runnable AI experiments** — built while learning agents, RAG, Hugging Face, LangChain, CrewAI, MCP, and inference APIs across multiple languages.

Each project under [`apps/`](apps/) is self-contained: own dependencies, env vars, and README. Clone one folder, run it, tear it down — no monorepo ceremony.

## Highlights

| Area | What's in here |
|------|----------------|
| **Agents** | Multi-tool `CodeAgent` labs, smolagents intro, example prompts + calculator |
| **RAG** | FastAPI Q&A over local knowledge + HF inference + Gradio UI |
| **Hugging Face** | Pipelines, Hub lookups, Inference API from **Python**, **Go**, and **Node** |
| **Polyglot** | Same ideas reimplemented where it matters — stdlib Go, native Node `fetch`, Python `transformers` |
| **Agent skills** | Pinned [skills.sh](https://skills.sh/) catalog for Cursor — LangChain, CrewAI, HF, FastAPI, OpenAI |

## Featured experiments

| Project | Stack | One-liner |
|---------|-------|-----------|
| [`hf-agents-lab`](apps/python/hf-agents-lab/) | Python · smolagents · Gradio | Multi-tool agent capstone (Hub, learning tips, calculator) |
| [`hf-qa-rag`](apps/python/hf-qa-rag/) | Python · FastAPI · Gradio | Q&A over `qa.txt` with HF inference |
| [`hf-qa-rag-api`](apps/node/hf-qa-rag-api/) + [`hf-qa-rag-ui`](apps/typescript/hf-qa-rag-ui/) | Node · React · assistant-ui | Same RAG API + ChatGPT-style UI (shadcn) |
| [`hf-smolagent-intro`](apps/python/hf-smolagent-intro/) | Python · smolagents | First agent: Hub + monorepo learning-path tools |
| [`hf-pipeline-hello`](apps/python/hf-pipeline-hello/) | Python · transformers | Sentiment pipeline on sample text |
| [`hf-sentiment-server`](apps/go/hf-sentiment-server/) | Go · `net/http` | `POST /v1/sentiment` via HF Inference API |
| [`hf-inference-hello`](apps/go/hf-inference-hello/) | Go | CLI sentiment via Inference API |
| [`hf-inference-hello`](apps/node/hf-inference-hello/) | Node 20+ | CLI + HTTP server for HF sentiment |

Full catalog: [`apps/README.md`](apps/README.md).

## Repo layout

```
.
├── apps/              # Experiments by language (python, typescript, node, go, java)
├── docs/              # Getting started, skills, learning catalog, experiment ideas
├── skills-lock.json   # Pinned agent skills (see docs/skills.md)
└── CONTRIBUTING.md
```

## Quick start

```bash
git clone git@github.com:eduardocerqueira/AI-sandbox.git
cd AI-sandbox
npx skills experimental_install   # optional: restore Cursor agent skills
```

Pick an app, follow its README. New project from a template:

```bash
cp -r apps/python/_template apps/python/my-experiment
```

Details: [docs/getting-started.md](docs/getting-started.md) · [CONTRIBUTING.md](CONTRIBUTING.md).

**CI:** PR checks and nightly tests in GitHub Actions. **Scheduled agents** (test, docs, CVE, issues, PR review, experiments): [docs/agents.md](docs/agents.md) — most need `OPENAI_API_KEY`.

## Documentation

| | |
|---|---|
| **Start here** | [docs/getting-started.md](docs/getting-started.md) |
| **Agent skills** | [docs/skills.md](docs/skills.md) |
| **Experiment ideas** | [docs/experiment-ideas.md](docs/experiment-ideas.md) |
| **Courses & certs** | [docs/learning-resources.md](docs/learning-resources.md) |
| **Scheduled agents** | [docs/agents.md](docs/agents.md) — test-bot, docs-bot, CVE scan, issue-bot, PR steward, experiment-agent |
| **All docs** | [docs/README.md](docs/README.md) |

## Why this exists

Learning AI tooling is easier with **working code you can grep**, not slide decks alone. This repo is a public scratchpad: small apps, honest READMEs, and a curated doc trail — useful to me, open to anyone skimming for patterns.

## Simplified Architecture

```mermaid
flowchart TD
    A[Scheduled Bots] -->|Cron| B[PR Check]
    A -->|Workflow Dispatch| C[PR Steward]
    D[Triggers] -->|Scheduled| A
    D -->|PR Triggered| B
    D -->|Auto-Approve| C
    E[For full details, see] -->|[docs/agents.md]| F[Documentation]
```
