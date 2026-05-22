"""LLM planning from docs context."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Literal

from experiment_agent.docs_context import load_docs_context

WorkKind = Literal["doc", "code"]


@dataclass
class WorkPlan:
    kind: WorkKind
    title: str
    issue_body: str
    rationale: str
    doc_path: str | None
    doc_content: str | None
    app_slug: str | None
    app_description: str | None
    main_py: str | None
    readme_extra: str | None


def _parse_json_payload(text: str) -> dict:
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence:
        text = fence.group(1)
    return json.loads(text)


def plan_work() -> WorkPlan:
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise SystemExit("OPENAI_API_KEY is required for experiment-agent")

    docs = load_docs_context()
    model = os.environ.get("EXPERIMENT_AGENT_MODEL", "gpt-4o-mini")

    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        temperature=0.3,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "You plan small learning experiments for the AI-sandbox monorepo. "
                    "Use the provided docs (learning-resources, experiment-ideas, getting-started) "
                    "to pick ONE focused topic not already fully covered by existing apps. "
                    "Output JSON only with keys:\n"
                    '- kind: "doc" or "code"\n'
                    '- title: short title (no prefix)\n'
                    '- issue_body: markdown proposal for a GitHub issue (goal, scope, '
                    "acceptance criteria, links to learning resources)\n"
                    '- rationale: why this topic now\n'
                    '- doc_path: for kind=doc, path like docs/experiments/my-topic.md\n'
                    '- doc_content: full markdown file content for kind=doc\n'
                    '- app_slug: for kind=code, kebab-case under apps/python/ e.g. hf-ollama-hello\n'
                    '- app_description: one-line for apps/README\n'
                    '- main_py: for kind=code, full Python main.py module body (function main)\n'
                    '- readme_extra: for kind=code, markdown section for README (## Goal etc.)\n'
                    "Prefer kind=doc when unsure. Code must be minimal, testable, no network in tests. "
                    "Do not duplicate existing project names from apps/README."
                ),
            },
            {
                "role": "user",
                "content": f"Repository docs and catalog:\n\n{docs}",
            },
        ],
    )
    raw = (response.choices[0].message.content or "").strip()
    data = _parse_json_payload(raw)

    kind = data.get("kind", "doc")
    if kind not in ("doc", "code"):
        kind = "doc"

    return WorkPlan(
        kind=kind,
        title=str(data.get("title", "Learning experiment")).strip()[:120],
        issue_body=str(data.get("issue_body", "")).strip(),
        rationale=str(data.get("rationale", "")).strip(),
        doc_path=data.get("doc_path"),
        doc_content=data.get("doc_content"),
        app_slug=data.get("app_slug"),
        app_description=data.get("app_description"),
        main_py=data.get("main_py"),
        readme_extra=data.get("readme_extra"),
    )
