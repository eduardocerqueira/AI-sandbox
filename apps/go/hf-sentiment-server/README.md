# hf-sentiment-server

Second **Go** experiment: a small **`net/http`** service that exposes sentiment analysis via the Hugging Face Inference API.

**Previous:** [hf-inference-hello](../hf-inference-hello/) (CLI)

## Prerequisites

- Go 1.22+
- `HF_TOKEN`

## Setup

```bash
cd apps/go/hf-sentiment-server
export HF_TOKEN=hf_your_token_here
# optional:
# export PORT=8080
# export HF_MODEL=distilbert/distilbert-base-uncased-finetuned-sst-2-english
```

## Run

```bash
go run .
```

## API

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Liveness check |
| `POST` | `/v1/sentiment` | Classify text |

**Request**

```json
{ "text": "I love learning Go!" }
```

**Response**

```json
{
  "model": "distilbert/distilbert-base-uncased-finetuned-sst-2-english",
  "text": "I love learning Go!",
  "labels": [
    { "label": "POSITIVE", "score": 0.999 },
    { "label": "NEGATIVE", "score": 0.001 }
  ]
}
```

**Try it**

```bash
curl -s http://127.0.0.1:8080/health | jq

curl -s -X POST http://127.0.0.1:8080/v1/sentiment \
  -H "Content-Type: application/json" \
  -d '{"text":"Hugging Face Inference from Go works!"}' | jq
```

Use full Hub model ids (`org/model`) supported by [hf-inference](https://huggingface.co/models?inference_provider=hf-inference&pipeline_tag=text-classification).

## Test

```bash
go test ./...
```

## Next steps

- Add request logging and timeouts on the HTTP client
- Call this service from a Python agent as a custom tool
- Deploy behind Docker / Fly.io for a public demo
