"""Apply doc or code changes from a work plan."""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

from experiment_agent.plan import WorkPlan

REPO_ROOT = Path(__file__).resolve().parents[3]
PYTHON_TEMPLATE = REPO_ROOT / "apps" / "python" / "_template"
PR_CHECK = REPO_ROOT / ".github" / "workflows" / "pr-check.yml"
APPS_README = REPO_ROOT / "apps" / "README.md"
EXPERIMENTS_INDEX = REPO_ROOT / "docs" / "experiments" / "README.md"

_SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def _safe_doc_path(rel: str) -> Path:
    path = (REPO_ROOT / rel).resolve()
    if not str(path).startswith(str((REPO_ROOT / "docs").resolve())):
        raise ValueError(f"doc_path must stay under docs/: {rel}")
    if path.suffix != ".md":
        raise ValueError("doc_path must be a .md file")
    return path


def _slug_to_module(slug: str) -> str:
    return slug.replace("-", "_")


def apply_doc(plan: WorkPlan) -> list[str]:
    if not plan.doc_path or not plan.doc_content:
        raise ValueError("doc plan missing doc_path or doc_content")
    path = _safe_doc_path(plan.doc_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(plan.doc_content.strip() + "\n", encoding="utf-8")
    changed = [path.relative_to(REPO_ROOT).as_posix()]

    EXPERIMENTS_INDEX.parent.mkdir(parents=True, exist_ok=True)
    if not EXPERIMENTS_INDEX.is_file():
        EXPERIMENTS_INDEX.write_text(
            "# Experiments (agent-written)\n\nNotes and research produced by "
            "[experiment-agent](../../scripts/experiment-agent/README.md).\n\n",
            encoding="utf-8",
        )
        changed.append(EXPERIMENTS_INDEX.relative_to(REPO_ROOT).as_posix())

    rel = path.relative_to(REPO_ROOT / "docs").as_posix()
    index_text = EXPERIMENTS_INDEX.read_text(encoding="utf-8")
    link_line = f"- [{path.stem}]({rel}) — {plan.title}"
    if link_line not in index_text:
        EXPERIMENTS_INDEX.write_text(index_text.rstrip() + "\n" + link_line + "\n", encoding="utf-8")
        if EXPERIMENTS_INDEX.relative_to(REPO_ROOT).as_posix() not in changed:
            changed.append(EXPERIMENTS_INDEX.relative_to(REPO_ROOT).as_posix())

    return changed


def _replace_in_tree(root: Path, old: str, new: str) -> None:
    for path in root.rglob("*"):
        if path.is_file():
            text = path.read_text(encoding="utf-8", errors="replace")
            if old in text:
                path.write_text(text.replace(old, new), encoding="utf-8")


def _add_apps_readme_row(slug: str, description: str) -> None:
    row = f"| `python/{slug}` | {description} |"
    text = APPS_README.read_text(encoding="utf-8")
    if slug in text:
        return
    marker = "## Current projects"
    if marker not in text:
        return
    insert_at = text.find(marker)
    table_end = text.find("\n\n", insert_at)
    if table_end == -1:
        table_end = len(text)
    new_text = text[:table_end] + "\n" + row + text[table_end:]
    APPS_README.write_text(new_text, encoding="utf-8")


def _add_pr_check_app(slug: str) -> None:
    text = PR_CHECK.read_text(encoding="utf-8")
    needle = f"          - {slug}\n"
    if needle in text:
        return
    anchor = "          - hf-qa-rag\n"
    if anchor not in text:
        raise ValueError("Could not find python matrix anchor in pr-check.yml")
    PR_CHECK.write_text(text.replace(anchor, anchor + f"          - {slug}\n"), encoding="utf-8")


def apply_code(plan: WorkPlan) -> list[str]:
    slug = (plan.app_slug or "").strip()
    if not _SLUG_RE.match(slug):
        raise ValueError(f"invalid app_slug: {slug!r}")
    if not PYTHON_TEMPLATE.is_dir():
        raise FileNotFoundError("apps/python/_template missing")

    dest = REPO_ROOT / "apps" / "python" / slug
    if dest.exists():
        raise FileExistsError(f"app already exists: {dest}")

    shutil.copytree(PYTHON_TEMPLATE, dest)
    module = _slug_to_module(slug)
    _replace_in_tree(dest, "my_project_name", module)
    _replace_in_tree(dest, "my-project-name", slug)

    if plan.main_py:
        main_path = dest / "src" / module / "main.py"
        main_path.write_text(plan.main_py.strip() + "\n", encoding="utf-8")

    if plan.readme_extra:
        readme = dest / "README.md"
        readme.write_text(
            readme.read_text(encoding="utf-8").rstrip()
            + "\n\n"
            + plan.readme_extra.strip()
            + "\n",
            encoding="utf-8",
        )

    desc = (plan.app_description or plan.title).strip()
    _add_apps_readme_row(slug, desc)
    _add_pr_check_app(slug)

    subprocess.run(
        ["python", "-m", "pip", "install", "-e", ".[dev]"],
        cwd=dest,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["pytest", "-q"],
        cwd=dest,
        check=True,
        capture_output=True,
        text=True,
    )

    return [
        f"apps/python/{slug}",
        "apps/README.md",
        ".github/workflows/pr-check.yml",
    ]


def apply_plan(plan: WorkPlan) -> list[str]:
    if plan.kind == "doc":
        return apply_doc(plan)
    return apply_code(plan)
