"""Load ./docs for LLM context."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DOCS_DIR = REPO_ROOT / "docs"
MAX_CHARS_PER_FILE = 14_000
MAX_TOTAL_CHARS = 72_000


def load_docs_context() -> str:
    """Return concatenated markdown from docs/ (bounded size)."""
    if not DOCS_DIR.is_dir():
        return ""

    parts: list[str] = []
    total = 0
    for path in sorted(DOCS_DIR.rglob("*.md")):
        if not path.is_file():
            continue
        rel = path.relative_to(REPO_ROOT).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        if len(text) > MAX_CHARS_PER_FILE:
            text = text[:MAX_CHARS_PER_FILE] + "\n\n…(truncated)…\n"
        chunk = f"\n\n---\n## File: {rel}\n\n{text}"
        if total + len(chunk) > MAX_TOTAL_CHARS:
            parts.append("\n\n…(remaining docs omitted for token limit)…\n")
            break
        parts.append(chunk)
        total += len(chunk)

    apps_readme = REPO_ROOT / "apps" / "README.md"
    if apps_readme.is_file() and total < MAX_TOTAL_CHARS:
        text = apps_readme.read_text(encoding="utf-8", errors="replace")[:MAX_CHARS_PER_FILE]
        parts.append(f"\n\n---\n## File: apps/README.md\n\n{text}")

    return "".join(parts).strip()
