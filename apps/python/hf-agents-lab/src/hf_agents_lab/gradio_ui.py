"""Gradio web UI for the agents lab."""

from __future__ import annotations

import os

from smolagents import GradioUI

from hf_agents_lab.main import build_agent, configure_hf_token, require_token


def launch(
    *,
    model_id: str | None = None,
    token: str | None = None,
    share: bool = False,
    inbrowser: bool = True,
) -> None:
    agent = build_agent(model_id=model_id, token=token)
    print(
        "\nOpen http://127.0.0.1:7860 in your browser (Ctrl+C to stop).\n"
    )
    GradioUI(agent, reset_agent_memory=True).launch(
        share=share,
        inbrowser=inbrowser,
    )


def main() -> None:
    token = require_token(configure_hf_token())
    launch(
        model_id=os.getenv("HF_SMOLAGENT_MODEL_ID"),
        token=token,
    )
