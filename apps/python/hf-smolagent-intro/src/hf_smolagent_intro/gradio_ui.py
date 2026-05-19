"""Gradio chat UI for the smolagents CodeAgent."""

from __future__ import annotations

import os

from smolagents import GradioUI

from hf_smolagent_intro.main import build_agent, configure_hf_token, require_token


def launch(
    *,
    model_id: str | None = None,
    token: str | None = None,
    share: bool = False,
    inbrowser: bool = True,
) -> None:
    agent = build_agent(model_id=model_id, token=token)
    ui = GradioUI(agent, reset_agent_memory=True)
    print(
        "\nGradio is a web UI — open the local URL in your browser if it does not open automatically.\n"
        "Press Ctrl+C in this terminal to stop the server.\n"
    )
    ui.launch(share=share, inbrowser=inbrowser)


def main() -> None:
    """Entry point for `hf-smolagent-gradio` console script."""
    token = require_token(configure_hf_token())
    model_id = os.getenv("HF_SMOLAGENT_MODEL_ID")
    launch(model_id=model_id, token=token)
