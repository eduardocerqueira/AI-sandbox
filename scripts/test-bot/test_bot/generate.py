"""Generate test file content with an OpenAI-compatible chat model."""

from __future__ import annotations

import os
import re
from pathlib import Path

from openai import OpenAI

from test_bot.discover import REPO_ROOT, Target
from test_bot.prompts import SYSTEM_PROMPT, build_user_prompt

FENCE_RE = re.compile(
    r"```(?:python|javascript|js|typescript|ts|go|golang)?\s*\n(.*?)```",
    re.DOTALL | re.IGNORECASE,
)


def _find_example_test(target: Target) -> str | None:
    if target.language == "python":
        tests_dir = target.app_dir / "tests"
        if tests_dir.is_dir():
            for path in sorted(tests_dir.glob("test_*.py")):
                return path.read_text(encoding="utf-8")
    if target.language == "node":
        for path in sorted((target.app_dir / "src").glob("*.test.js")):
            return path.read_text(encoding="utf-8")
    if target.language == "go":
        out_stem = target.test_path.stem
        for path in sorted(target.app_dir.glob("*_test.go")):
            if path.stem == out_stem:
                continue
            return path.read_text(encoding="utf-8")
    if target.language == "typescript":
        for path in sorted((target.app_dir / "src").rglob("*.test.ts")):
            return path.read_text(encoding="utf-8")
    return None


def extract_code_block(text: str) -> str:
    match = FENCE_RE.search(text)
    if match:
        return match.group(1).strip()
    return text.strip()


def generate_test_content(target: Target, *, fix_error: str | None = None) -> str:
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")

    model = os.environ.get("TEST_BOT_MODEL", "gpt-4o-mini")
    source_code = target.source_path.read_text(encoding="utf-8")
    example = _find_example_test(target)

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        temperature=0.2,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": build_user_prompt(
                    target, source_code, example, fix_error=fix_error
                ),
            },
        ],
    )

    raw = response.choices[0].message.content or ""
    content = extract_code_block(raw)
    if not content:
        raise RuntimeError(f"Empty test generation for {target.rel_source}")
    return content + "\n"


def write_test_file(target: Target, content: str, *, dry_run: bool) -> None:
    target.test_path.parent.mkdir(parents=True, exist_ok=True)
    if dry_run:
        print(f"[dry-run] would write {target.rel_test} ({len(content)} bytes)")
        return
    target.test_path.write_text(content, encoding="utf-8")
    print(f"Wrote {target.rel_test}")
