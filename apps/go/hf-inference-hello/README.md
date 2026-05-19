# hf-inference-hello

First **Go** experiment: call the [Hugging Face Inference API](https://huggingface.co/docs/inference-providers) for sentiment analysis — same idea as [hf-pipeline-hello](../../python/hf-pipeline-hello/) but with the standard library only (no ML runtime in-process).

**Note:** Inference API model ids are often `organization/model` (e.g. `distilbert/distilbert-base-uncased-finetuned-sst-2-english`), not the short name alone.

## Prerequisites

- Go 1.22+
- `HF_TOKEN` ([create a token](https://huggingface.co/settings/tokens))

## Setup

```bash
cd apps/go/hf-inference-hello
export HF_TOKEN=hf_your_token_here
# optional: hf auth login  (CLI stores token; you still need HF_TOKEN in env for this app)
```

## Run

```bash
go run .                    # three sample sentences
go run . -text "Go is fun!" # one sentence
go run . -model distilbert/distilbert-base-uncased-finetuned-sst-2-english
```

Use a model id listed for [hf-inference](https://huggingface.co/models?inference_provider=hf-inference&pipeline_tag=text-classification) (usually `org/model` form).

```bash
# alternate model
go run . -model cardiffnlp/twitter-roberta-base-sentiment-latest
```

Build a binary:

```bash
go build -o bin/hf-inference-hello .
./bin/hf-inference-hello
```

## Test

```bash
go test ./...
```

Tests cover JSON parsing only (no live API calls).

## Hugging Face token

```bash
hf auth login
hf auth whoami
export HF_TOKEN=hf_...   # this app reads HF_TOKEN from the environment
```

## Learning

- [Inference Providers docs](https://huggingface.co/docs/inference-providers)
- Compare with Python [hf-pipeline-hello](../../python/hf-pipeline-hello/) (local `transformers` vs remote API)

## Next steps

- Continue with [hf-sentiment-server](../hf-sentiment-server/) (HTTP API)
- Try a text-generation model with a different request body
- New app: `apps/go/hf-hub-cli` to list Hub models (like your Python Hub tool)
