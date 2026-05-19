# Apps

Each subdirectory is a **language workspace**. Projects are sibling folders inside that language directory.

| Directory | Runtime | Use for |
|-----------|---------|---------|
| [python/](python/) | Python 3.11+ | LangChain, CrewAI, Hugging Face, FastAPI, NeMo, notebooks |
| [typescript/](typescript/) | Node 20+ | MCP servers, LangChain.js, agent SDKs |
| [node/](node/) | Node 20+ | Plain JavaScript experiments |
| [go/](go/) | Go 1.22+ | CLIs, small services, performance probes |
| [java/](java/) | JDK 21+ | JVM integrations, enterprise-style spikes |

## Current projects

| Project | Description |
|---------|-------------|
| `python/hf-pipeline-hello` | Hugging Face `transformers` sentiment pipeline on sample text |
| `python/hf-smolagent-intro` | smolagents agent, Hub + learning-path tools, optional Gradio UI |
| `python/hf-agents-lab` | Multi-tool agents lab + calculator + example prompts |
| `go/hf-inference-hello` | HF Inference API sentiment CLI (stdlib `net/http`) |

## Creating a project

See [../docs/getting-started.md](../docs/getting-started.md) and [../CONTRIBUTING.md](../CONTRIBUTING.md).
