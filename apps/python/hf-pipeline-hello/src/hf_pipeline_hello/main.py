"""Sentiment analysis with a Hugging Face transformers pipeline."""

from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv

DEFAULT_MODEL = "distilbert-base-uncased-finetuned-sst-2-english"

SAMPLE_TEXTS = [
    "I love learning about transformers!",
    "This setup is confusing and frustrating.",
    "Hugging Face pipelines make inference simple.",
]


def format_prediction(text: str, prediction: dict[str, Any]) -> str:
    label = prediction["label"]
    score = prediction["score"]
    return f"{text!r} -> {label} ({score:.3f})"


def run_sentiment(
    texts: list[str],
    *,
    model: str = DEFAULT_MODEL,
    classifier: Any | None = None,
) -> list[str]:
    if classifier is None:
        from transformers import pipeline

        classifier = pipeline("sentiment-analysis", model=model)

    lines: list[str] = []
    for text, prediction in zip(texts, classifier(texts), strict=True):
        lines.append(format_prediction(text, prediction))
    return lines


def main() -> None:
    load_dotenv()
    token = os.getenv("HF_TOKEN")
    if token:
        os.environ.setdefault("HUGGINGFACE_HUB_TOKEN", token)

    print(f"Model: {DEFAULT_MODEL}\n")
    for line in run_sentiment(SAMPLE_TEXTS):
        print(line)


if __name__ == "__main__":
    main()
