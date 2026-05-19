# hf-smolagent-intro

Second Hugging Face experiment: a **smolagents** `CodeAgent` with custom tools and an optional Gradio chat UI.

Follows the [Hugging Face AI Agents Course](https://huggingface.co/learn/agents-course) and [smolagents guided tour](https://huggingface.co/docs/smolagents/guided_tour).

**Previous step:** [hf-pipeline-hello](../hf-pipeline-hello/)

## Tools

| Tool | Purpose |
|------|---------|
| `top_hub_model_for_task` | Most downloaded Hub model for a pipeline tag |
| `learning_path_tip` | Suggests a study topic from this monorepo’s [learning catalog](../../../docs/learning-resources.md) |

## Prerequisites

- Python 3.11+
- `HF_TOKEN` for the agent and Gradio UI ([Inference Providers](https://huggingface.co/docs/inference-providers))
- Completed [hf-pipeline-hello](../hf-pipeline-hello/) or equivalent

## Setup

```bash
cd apps/python/hf-smolagent-intro
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env
```

For the Gradio UI:

```bash
pip install -e ".[ui]"
```

### Hugging Face token

Add your token to `.env`:

```env
HF_TOKEN=hf_your_token_here
```

Create a token at [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) (Read access is enough for Hub tools; Inference API uses the same token).

For the `hf` CLI:

```bash
hf auth login
hf auth whoami
```

## Run

**1. Offline tool demos (no LLM / no Inference credits)**

```bash
python -m hf_smolagent_intro --demo-tool
python -m hf_smolagent_intro --demo-tool --task summarization
python -m hf_smolagent_intro --demo-tip --topic rag
```

**2. Full agent (Inference API + both tools)**

```bash
python -m hf_smolagent_intro
```

Custom prompt:

```bash
python -m hf_smolagent_intro "What should I study for MCP, and what is the top summarization model on the Hub?"
```

**3. Gradio chat UI (web app in your browser — not a native desktop window)**

```bash
pip install -e ".[ui]"
python -m hf_smolagent_intro --gradio
```

When you see `Running on local URL: http://127.0.0.1:7860`, open that link in your browser (it may open automatically). The terminal stays running — use **Ctrl+C** to stop.

Add `--share` for a temporary public Gradio link. Set `HF_SMOLAGENT_NO_BROWSER=1` to skip auto-opening the browser.

Optional model override in `.env`:

```env
HF_SMOLAGENT_MODEL_ID=Qwen/Qwen2.5-Coder-32B-Instruct
```

## Test

```bash
pytest
```

Tests mock Hub calls and do not run the agent or Gradio.

## What you’ll learn

- Multiple `@tool` functions on one `CodeAgent`
- Tool-only checks vs full agent runs
- Optional `GradioUI` from smolagents

## Next steps

- Continue to [hf-agents-lab](../hf-agents-lab/) (calculator + example prompts)
- [hf-pipeline-hello](../hf-pipeline-hello/) — swap pipeline tasks (NER, summarization)
