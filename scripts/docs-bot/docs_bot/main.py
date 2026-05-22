"""Sync apps/README.md project table with discovered apps (LLM polishes prose)."""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
APPS_README = REPO_ROOT / "apps" / "README.md"
CI_APPS = REPO_ROOT / ".github" / "workflows" / "pr-check.yml"


def _discover_apps() -> list[tuple[str, str]]:
    """Return (language, app_name) for each app dir (skip _template)."""
    apps: list[tuple[str, str]] = []
    apps_root = REPO_ROOT / "apps"
    for lang_dir in sorted(apps_root.iterdir()):
        if not lang_dir.is_dir():
            continue
        lang = lang_dir.name
        if lang == "README.md" or lang.endswith(".md"):
            continue
        for app_dir in sorted(lang_dir.iterdir()):
            if app_dir.is_dir() and not app_dir.name.startswith("_"):
                apps.append((lang, app_dir.name))
    return apps


def _build_catalog_markdown(apps: list[tuple[str, str]]) -> str:
    lines = [
        "## Current projects (auto-synced)",
        "",
        "| Project | Language |",
        "|---------|----------|",
    ]
    for lang, name in apps:
        lines.append(f"| `{lang}/{name}` | {lang} |")
    lines.append("")
    lines.append(f"_Last synced: {datetime.now(UTC).strftime('%Y-%m-%d')}_")
    lines.append("")
    return "\n".join(lines)


def _merge_into_readme(catalog: str) -> str:
    text = APPS_README.read_text(encoding="utf-8")
    marker_start = "<!-- docs-bot:start -->"
    marker_end = "<!-- docs-bot:end -->"
    block = f"{marker_start}\n{catalog}{marker_end}"

    if marker_start in text and marker_end in text:
        return re.sub(
            rf"{re.escape(marker_start)}.*?{re.escape(marker_end)}",
            block,
            text,
            count=1,
            flags=re.DOTALL,
        )

    return text.rstrip() + "\n\n" + block + "\n"


def _maybe_polish_with_llm(catalog: str, *, dry_run: bool) -> str:
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key or dry_run:
        return catalog

    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=os.environ.get("DOCS_BOT_MODEL", "gpt-4o-mini"),
        temperature=0.2,
        messages=[
            {
                "role": "system",
                "content": (
                    "Improve the markdown table descriptions only. "
                    "Keep the same rows and paths. One short description column max. "
                    "Output markdown only."
                ),
            },
            {"role": "user", "content": catalog},
        ],
    )
    return (response.choices[0].message.content or catalog).strip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    apps = _discover_apps()
    catalog = _build_catalog_markdown(apps)
    catalog = _maybe_polish_with_llm(catalog, dry_run=args.dry_run)
    updated = _merge_into_readme(catalog)

    if updated == APPS_README.read_text(encoding="utf-8"):
        print("apps/README.md already up to date.")
        return

    if args.dry_run:
        print(updated)
        return

    APPS_README.write_text(updated, encoding="utf-8")
    print(f"Updated {APPS_README.relative_to(REPO_ROOT)}")

    branch = f"docs-bot/{datetime.now(UTC).strftime('%Y%m%d-%H%M%S')}"
    subprocess.run(["git", "config", "user.name", "github-actions[bot]"], cwd=REPO_ROOT, check=True)
    subprocess.run(
        ["git", "config", "user.email", "github-actions[bot]@users.noreply.github.com"],
        cwd=REPO_ROOT,
        check=True,
    )
    subprocess.run(["git", "checkout", "-b", branch], cwd=REPO_ROOT, check=True)
    subprocess.run(["git", "add", "apps/README.md"], cwd=REPO_ROOT, check=True)
    subprocess.run(
        ["git", "commit", "-m", "docs-bot: sync apps catalog table"],
        cwd=REPO_ROOT,
        check=True,
    )
    subprocess.run(["git", "push", "-u", "origin", branch], cwd=REPO_ROOT, check=True)
    subprocess.run(
        [
            "gh",
            "pr",
            "create",
            "--title",
            "docs-bot: sync apps catalog",
            "--body",
            "Automated sync of the apps catalog table in `apps/README.md`.\n\n"
            "See [docs/agents.md](docs/agents.md).",
            "--head",
            branch,
            "--base",
            os.environ.get("DOCS_BOT_BASE_BRANCH", "main"),
        ],
        cwd=REPO_ROOT,
        check=True,
    )


if __name__ == "__main__":
    main()
