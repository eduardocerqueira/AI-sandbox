# hf-agents-lab

Capstone lab for the Hugging Face agents track: a **multi-tool** `CodeAgent` you can run from the CLI or a **Gradio web UI**.

**Builds on:** [hf-pipeline-hello](../hf-pipeline-hello/) → [hf-smolagent-intro](../hf-smolagent-intro/)

**Course:** [Hugging Face AI Agents Course](https://huggingface.co/learn/agents-course)

## Tools

| Tool | Purpose |
|------|---------|
| `top_hub_model_for_task` | Top downloaded Hub model for a pipeline tag |
| `learning_path_tip` | Study suggestion from this monorepo’s catalog |
| `calculator` | Safe arithmetic (`+ - * / ** %`, parentheses) |

## Setup

```bash
cd apps/python/hf-agents-lab
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # HF_TOKEN=hf_...
```

Gradio UI: `pip install -e ".[ui]"`

### Hugging Face token

```env
HF_TOKEN=hf_your_token_here
```

```bash
hf auth login
hf auth whoami
```

## Run

**Offline demos (no Inference API)**

```bash
python -m hf_agents_lab --demo-tool --task text-generation
python -m hf_agents_lab --demo-tip --topic rag
python -m hf_agents_lab --demo-calc "(42 + 8) * 2"
```

**Example prompts**

```bash
python -m hf_agents_lab --list-prompts
python -m hf_agents_lab --example hub      # needs HF_TOKEN
python -m hf_agents_lab --example combo
```

**Full agent**

```bash
python -m hf_agents_lab
```

**Gradio (browser at http://127.0.0.1:7860)**

```bash
pip install -e ".[ui]"
python -m hf_agents_lab --gradio
```

Press **Ctrl+C** in the terminal to stop. Use `--share` for a temporary public link.

## Test

```bash
pytest
```

## Suggested exercises (Agents Course)

1. Add a fourth tool (read a local `.txt` file under this app folder).
2. Change `CodeAgent` to `ToolCallingAgent` and compare behavior.
3. Submit a Gradio Space combining your best prompt + tools.
