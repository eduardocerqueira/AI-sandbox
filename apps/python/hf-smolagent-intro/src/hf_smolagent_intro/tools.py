"""Custom tools for the smolagents intro agent."""

from __future__ import annotations

from huggingface_hub import list_models
from smolagents import tool

DEFAULT_HUB_TASK = "text-classification"

# Topics aligned with docs/learning-resources.md in this monorepo
LEARNING_TIPS: dict[str, str] = {
    "agents": "P1: Hugging Face AI Agents Course + OpenAI Agents SDK (docs/learning-resources.md)",
    "mcp": "P1: MCP for Beginners (Microsoft) + Anthropic MCP courses",
    "rag": "P1: NVIDIA Building RAG Agents with LLMs + langchain-rag skill",
    "langchain": "P2: LangChain Academy — Intro to LangChain → LangGraph → LangSmith",
    "huggingface": "P1: HF AI Agents Course; P2: LLM Course + smol-course",
    "cursor": "P1: Cursor Learn (agents, rules, MCP) + Claude Code in Action",
}


@tool
def top_hub_model_for_task(task: str) -> str:
    """
    Return the most downloaded model on the Hugging Face Hub for a pipeline task.

    Args:
        task: Hub pipeline tag, e.g. text-classification, summarization, text-generation.
    """
    return lookup_top_model(task)


@tool
def learning_path_tip(topic: str) -> str:
    """
    Return a suggested learning path from the AI-training monorepo catalog for a topic.

    Args:
        topic: Subject keyword such as agents, rag, mcp, langchain, huggingface, or cursor.
    """
    return resolve_learning_tip(topic)


def lookup_top_model(task: str = DEFAULT_HUB_TASK) -> str:
    """Hub lookup without the agent loop (for tests and --demo-tool)."""
    most_downloaded = next(
        iter(list_models(pipeline_tag=task, sort="downloads", limit=1))
    )
    return most_downloaded.id


def resolve_learning_tip(topic: str) -> str:
    """Match a topic string to a learning tip (for tests and tool)."""
    normalized = topic.lower().strip()
    for keyword, tip in LEARNING_TIPS.items():
        if keyword in normalized:
            return tip
    options = ", ".join(sorted(LEARNING_TIPS))
    return f"No tip matched '{topic}'. Try keywords: {options}"


AGENT_TOOLS = [top_hub_model_for_task, learning_path_tip]
