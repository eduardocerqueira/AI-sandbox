from __future__ import annotations

from test_bot.discover import REPO_ROOT, Target

SYSTEM_PROMPT = """You are a senior engineer writing minimal unit tests for the AI-sandbox monorepo.

Rules:
- Output ONLY the complete test file in a single markdown fenced code block (language tag matching the test file).
- Do not call real Hugging Face, OpenAI, or external HTTP APIs. Mock fetch, InferenceClient, and env vars.
- Prefer testing pure functions, parsing, validation, and error paths.
- Match existing style in the example test file when provided.
- Keep tests fast and deterministic — no sleeps, no network.
- Python: use pytest and unittest.mock.
- Node: use node:test and node:assert/strict; ESM imports with .js extensions for local modules.
- Go: use testing package in the same package.
- TypeScript: use node:test with tsx-compatible imports; mock fetch with global stubs if needed.
- Do not add explanations outside the code fence.
"""


def build_user_prompt(
    target: Target,
    source_code: str,
    example_test: str | None,
) -> str:
    lines = [
        f"Language: {target.language}",
        f"App directory: {target.app_dir.relative_to(REPO_ROOT)}",
        f"Source file: {target.rel_source}",
        f"Write tests to: {target.rel_test}",
        "",
        "Source file content:",
        "```",
        source_code.strip(),
        "```",
    ]
    if example_test:
        lines.extend(
            [
                "",
                "Example test from the same app (match style):",
                "```",
                example_test.strip(),
                "```",
            ]
        )
    return "\n".join(lines)
