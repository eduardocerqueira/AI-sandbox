"""HF Agents lab — multi-tool CodeAgent."""

from __future__ import annotations

import argparse
import os
import sys

from dotenv import load_dotenv

from hf_agents_lab.prompts import EXAMPLE_PROMPTS
from hf_agents_lab.tools import (
    AGENT_TOOLS,
    DEFAULT_HUB_TASK,
    lookup_top_model,
    resolve_learning_tip,
    safe_calculate,
)

DEFAULT_PROMPT = EXAMPLE_PROMPTS[3][1]


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


def run_agent(prompt: str, *, model_id: str | None = None, token: str | None = None) -> str:
    return build_agent(model_id=model_id, token=token).run(prompt)


def require_token(token: str | None) -> str:
    if not token:
        print(
            "HF_TOKEN required for the agent. Add to .env or run offline demos:\n"
            "  --demo-tool | --demo-tip | --demo-calc",
            file=sys.stderr,
        )
        sys.exit(1)
    return token


def list_prompts() -> None:
    for name, text in EXAMPLE_PROMPTS:
        print(f"[{name}] {text}\n")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="HF Agents lab")
    parser.add_argument("--demo-tool", action="store_true", help="Hub lookup only")
    parser.add_argument("--demo-tip", action="store_true", help="Learning tip only")
    parser.add_argument("--demo-calc", metavar="EXPR", help="Calculator only")
    parser.add_argument("--gradio", action="store_true", help="Gradio web UI")
    parser.add_argument("--share", action="store_true", help="Public Gradio link")
    parser.add_argument("--list-prompts", action="store_true", help="Show example prompts")
    parser.add_argument("--example", choices=[p[0] for p in EXAMPLE_PROMPTS], help="Run a preset prompt")
    parser.add_argument("--task", default=DEFAULT_HUB_TASK, help="Hub task for --demo-tool")
    parser.add_argument("--topic", default="agents", help="Topic for --demo-tip")
    parser.add_argument("prompt", nargs="?", default=DEFAULT_PROMPT, help="Agent task")
    args = parser.parse_args(argv)

    if args.list_prompts:
        list_prompts()
        return

    token = configure_hf_token()
    model_id = os.getenv("HF_SMOLAGENT_MODEL_ID")

    if args.demo_tool:
        print(f"Top model for {args.task}: {lookup_top_model(args.task)}")
        return
    if args.demo_tip:
        print(resolve_learning_tip(args.topic))
        return
    if args.demo_calc is not None:
        print(safe_calculate(args.demo_calc))
        return

    token = require_token(token)
    prompt = args.prompt
    if args.example:
        prompt = dict(EXAMPLE_PROMPTS)[args.example]

    if args.gradio:
        try:
            from hf_agents_lab.gradio_ui import launch as launch_gradio
        except ImportError as exc:
            print("Install UI deps: pip install -e '.[ui]'", file=sys.stderr)
            raise SystemExit(1) from exc
        launch_gradio(
            model_id=model_id,
            token=token,
            share=args.share,
            inbrowser=not os.getenv("HF_SMOLAGENT_NO_BROWSER"),
        )
        return

    print(f"Running agent (model={model_id or 'default'})…\n")
    print(run_agent(prompt, model_id=model_id, token=token))


if __name__ == "__main__":
    main()
