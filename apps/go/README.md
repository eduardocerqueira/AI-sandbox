# Go apps

Small CLIs, HTTP gateways, or performance experiments. Typical pattern: call LLM/ML **APIs** from Go (no in-process PyTorch).

## Projects

| Project | Description |
|---------|-------------|
| [hf-inference-hello](hf-inference-hello/) | HF Inference API sentiment CLI (stdlib) |
| [hf-sentiment-server](hf-sentiment-server/) | HTTP `POST /v1/sentiment` wrapper around the same API |

## New project

```bash
cp -r _template my-project-name
cd my-project-name
go mod tidy
go run .
```
