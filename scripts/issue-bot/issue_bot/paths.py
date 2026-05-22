"""Validate and apply LLM-proposed file changes under the repo root."""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

DENY_PARTS = {".env", "TODO.md", ".git", "node_modules", ".venv", "venv"}
ALLOWED_PREFIXES = (
    "docs/",
    "README.md",
    "CONTRIBUTING.md",
    "apps/",
    "scripts/",
    ".github/workflows/",
    ".github/",
)

PATH_HINT_RE = re.compile(
    r"(?:^|[\s(])([\w./-]+\.(?:md|py|yml|yaml|js|ts|tsx|go|json|toml))(?:[\s),]|$)",
    re.MULTILINE,
)


def normalize_path(raw: str) -> str | None:
    path = raw.strip().lstrip("./")
    if not path or path.startswith("/") or ".." in path.split("/"):
        return None
    return path


def is_allowed_path(path: str) -> bool:
    if any(part in path for part in DENY_PARTS):
        return False
    if path in DENY_PARTS:
        return False
    return path.startswith(ALLOWED_PREFIXES) or path == "README.md"


def paths_mentioned_in_text(text: str) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for match in PATH_HINT_RE.finditer(text):
        norm = normalize_path(match.group(1))
        if norm and norm not in seen and (norm.startswith("docs/") or norm.endswith(".md")):
            seen.add(norm)
            out.append(norm)
    return out[:12]


def read_context_files(paths: list[str], *, max_bytes: int = 48_000) -> dict[str, str]:
    context: dict[str, str] = {}
    total = 0
    for rel in paths:
        full = REPO_ROOT / rel
        if not full.is_file():
            continue
        data = full.read_text(encoding="utf-8", errors="replace")
        if total + len(data) > max_bytes:
            data = data[: max_bytes - total] + "\n…(truncated)"
        context[rel] = data
        total += len(data)
        if total >= max_bytes:
            break
    return context


def apply_file_changes(files: list[dict[str, str]]) -> list[str]:
    """Write files; return list of relative paths written."""
    written: list[str] = []
    for entry in files:
        rel = normalize_path(entry.get("path", ""))
        if not rel or not is_allowed_path(rel):
            raise ValueError(f"Disallowed or invalid path: {entry.get('path')!r}")
        content = entry.get("content")
        if content is None:
            raise ValueError(f"Missing content for {rel}")
        target = REPO_ROOT / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content if content.endswith("\n") else content + "\n", encoding="utf-8")
        written.append(rel)
    return written
