"""Tools for the HF agents lab."""

from __future__ import annotations

import ast
import operator
from typing import Any

from huggingface_hub import list_models
from smolagents import tool

DEFAULT_HUB_TASK = "text-classification"

LEARNING_TIPS: dict[str, str] = {
    "agents": "P1: Hugging Face AI Agents Course + OpenAI Agents SDK",
    "mcp": "P1: MCP for Beginners (Microsoft) + Anthropic MCP courses",
    "rag": "P1: NVIDIA Building RAG Agents with LLMs",
    "langchain": "P2: LangChain Academy (LangChain → LangGraph → LangSmith)",
    "huggingface": "P1: HF AI Agents Course; P2: LLM Course + smol-course",
    "cursor": "P1: Cursor Learn + Claude Code in Action",
}

_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,
}


def lookup_top_model(task: str = DEFAULT_HUB_TASK) -> str:
    model = next(iter(list_models(pipeline_tag=task, sort="downloads", limit=1)))
    return model.id


def resolve_learning_tip(topic: str) -> str:
    normalized = topic.lower().strip()
    for keyword, tip in LEARNING_TIPS.items():
        if keyword in normalized:
            return tip
    return f"No tip matched '{topic}'. Keywords: {', '.join(sorted(LEARNING_TIPS))}"


def safe_calculate(expression: str) -> str:
    """Evaluate + - * / ** % and parentheses on numeric literals only."""
    try:
        tree = ast.parse(expression.strip(), mode="eval")
        value = _eval_ast(tree.body)
    except (SyntaxError, TypeError, ValueError, ZeroDivisionError) as exc:
        return f"Error: {exc}"
    return str(value)


def _eval_ast(node: ast.AST) -> Any:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.UnaryOp) and type(node.op) in _BIN_OPS:
        return _BIN_OPS[type(node.op)](_eval_ast(node.operand))
    if isinstance(node, ast.BinOp) and type(node.op) in _BIN_OPS:
        return _BIN_OPS[type(node.op)](_eval_ast(node.left), _eval_ast(node.right))
    raise ValueError("Only basic arithmetic expressions are allowed")


@tool
def top_hub_model_for_task(task: str) -> str:
    """
    Return the most downloaded Hugging Face Hub model for a pipeline task.

    Args:
        task: Pipeline tag such as text-classification, summarization, or text-generation.
    """
    return lookup_top_model(task)


@tool
def learning_path_tip(topic: str) -> str:
    """
    Suggest what to study in the AI-training monorepo for a given topic.

    Args:
        topic: Keyword like agents, rag, mcp, langchain, huggingface, or cursor.
    """
    return resolve_learning_tip(topic)


@tool
def calculator(expression: str) -> str:
    """
    Evaluate a basic arithmetic expression.

    Args:
        expression: Math expression using digits, +, -, *, /, **, %, and parentheses.
    """
    return safe_calculate(expression)


AGENT_TOOLS = [top_hub_model_for_task, learning_path_tip, calculator]
