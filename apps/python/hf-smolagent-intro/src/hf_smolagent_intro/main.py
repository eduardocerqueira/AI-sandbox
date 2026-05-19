"""smolagents CodeAgent with custom Hugging Face Hub and learning-path tools."""

from __future__ import annotations

import argparse
import os
import sys

from dotenv import load_dotenv

from hf_smolagent_intro.tools import (
    AGENT_TOOLS,
    DEFAULT_HUB_TASK,
    lookup_top_model,
    resolve_learning_tip,
)

DEFAULT_PROMPT = (
    "Use top_hub_model_for_task to find the most downloaded model for "
    f"'{DEFAULT_HUB_TASK}' on the Hub, then use learning_path_tip with topic "
    "'huggingface' to suggest what to study next in this monorepo. "
    "Reply in two short paragraphs."
)


def configure_hf_token() -> str | None:
    load_dotenv()
    token = os.getenv("HF_TOKEN")
    if token:
        os.environ.setdefault("HUGGINGFACE_HUB_TOKEN", token)
    return token


def build_agent(*, model_id: str | None = None, token: str | None = None):
    from smolagents import CodeAgent, InferenceClientModel

    kwargs: dict = {}
    if model_id:
        kwargs["model_id"] = model_id
    if token:
        kwargs["token"] = token

    model = InferenceClientModel(**kwargs)
    return CodeAgent(tools=AGENT_TOOLS, model=model)


def run_demo_tool(task: str = DEFAULT_HUB_TASK) -> str:
    model_id = lookup_top_model(task)
    print(f"Task: {task}")
    print(f"Top model: {model_id}")
    return model_id


def run_demo_tip(topic: str = "agents") -> str:
    tip = resolve_learning_tip(topic)
    print(f"Topic: {topic}")
    print(f"Tip: {tip}")
    return tip


def run_agent(
    prompt: str = DEFAULT_PROMPT,
    *,
    model_id: str | None = None,
    token: str | None = None,
) -> str:
    agent = build_agent(model_id=model_id, token=token)
    return agent.run(prompt)


def require_token(token: str | None) -> str:
    if not token:
        print(
            "HF_TOKEN is not set. Add it to .env (see .env.example) or run:\n"
            "  hf auth login\n"
            "Offline checks:\n"
            "  python -m hf_smolagent_intro --demo-tool\n"
            "  python -m hf_smolagent_intro --demo-tip",
            file=sys.stderr,
        )
        sys.exit(1)
    return token


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="HF smolagents intro")
    parser.add_argument(
        "--demo-tool",
        action="store_true",
        help="Run Hub lookup tool only (no LLM)",
    )
    parser.add_argument(
        "--demo-tip",
        action="store_true",
        help="Run learning_path_tip tool only (no LLM)",
    )
    parser.add_argument(
        "--gradio",
        action="store_true",
        help="Launch Gradio chat UI (requires gradio: pip install -e '.[ui]')",
    )
    parser.add_argument(
        "--share",
        action="store_true",
        help="Create a public Gradio link (with --gradio)",
    )
    parser.add_argument(
        "--task",
        default=DEFAULT_HUB_TASK,
        help=f"Hub pipeline task for --demo-tool (default: {DEFAULT_HUB_TASK})",
    )
    parser.add_argument(
        "--topic",
        default="agents",
        help="Topic keyword for --demo-tip (default: agents)",
    )
    parser.add_argument(
        "prompt",
        nargs="?",
        default=DEFAULT_PROMPT,
        help="Task for the agent (default: built-in multi-tool question)",
    )
    args = parser.parse_args(argv)

    token = configure_hf_token()
    model_id = os.getenv("HF_SMOLAGENT_MODEL_ID")

    if args.demo_tool:
        run_demo_tool(args.task)
        return

    if args.demo_tip:
        run_demo_tip(args.topic)
        return

    token = require_token(token)

    if args.gradio:
        try:
            from hf_smolagent_intro.gradio_ui import launch as launch_gradio
        except ImportError as exc:
            print(
                "Gradio is not installed. Run: pip install -e '.[ui]'",
                file=sys.stderr,
            )
            raise SystemExit(1) from exc
        print(f"Launching Gradio web UI (model={model_id or 'default'})…")
        launch_gradio(
            model_id=model_id,
            token=token,
            share=args.share,
            inbrowser=not os.getenv("HF_SMOLAGENT_NO_BROWSER"),
        )
        return

    print(f"Running agent (model={model_id or 'default'})…\n")
    result = run_agent(args.prompt, model_id=model_id, token=token)
    print(result)


if __name__ == "__main__":
    main()
