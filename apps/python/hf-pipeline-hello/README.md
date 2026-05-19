# hf-pipeline-hello

First Hugging Face experiment: run **sentiment analysis** on a few hardcoded sentences using a `transformers` pipeline.

## Prerequisites

- Python 3.11+
- ~500 MB disk for model weights (downloaded on first run)
- Optional: `HF_TOKEN` in `.env` for gated models or higher Hub rate limits (not required for the default model)

## Setup

```bash
cd apps/python/hf-pipeline-hello
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env        # optional
```

### Hugging Face token

Add your token to `.env` (create the file from `.env.example`):

```env
HF_TOKEN=hf_your_token_here
```

Create a token at [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) (Read access is enough for this project). Never commit `.env`.

For the `hf` CLI (separate from this app, but useful for downloads and Hub commands):

```bash
hf auth login
hf auth whoami
```

## Run

```bash
python -m hf_pipeline_hello
# or
hf-pipeline-hello
```

First run downloads `distilbert-base-uncased-finetuned-sst-2-english` from the Hub.

## Test

```bash
pytest
```

Tests mock the pipeline so they do not download the model.

## Learning

- [Hugging Face AI Agents Course](https://huggingface.co/learn/agents-course) — next step after this
- [Transformers pipelines docs](https://huggingface.co/docs/transformers/main_classes/pipelines)

## Next steps

- Swap in another pipeline task (summarization, NER)
- Continue with [hf-smolagent-intro](../hf-smolagent-intro/) (smolagents + custom tool)
