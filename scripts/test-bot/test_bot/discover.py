"""Find source files in CI-covered apps that lack a matching unit test."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

SKIP_DIR_NAMES = {"_template", "node_modules", "dist", "target", ".venv", "__pycache__"}

SKIP_SOURCE_NAMES = {
    "__init__.py",
    "__main__.py",
    "main.tsx",
    "App.tsx",
    "main.ts",
    "index.ts",
    "vite-env.d.ts",
}

# UI / entrypoints — prefer testing pure modules first
SKIP_SOURCE_STEMS = {
    "gradio_ui",
    "server",
    "main",
    "cli",
}

CI_APPS: dict[str, list[str]] = {
    "python": [
        "hf-pipeline-hello",
        "hf-smolagent-intro",
        "hf-agents-lab",
        "hf-qa-rag",
    ],
    "node": ["hf-inference-hello", "hf-qa-rag-api"],
    "go": ["hf-inference-hello", "hf-sentiment-server"],
    "typescript": ["hf-qa-rag-ui"],
}


@dataclass(frozen=True)
class Target:
    language: str
    app: str
    app_dir: Path
    source_path: Path
    test_path: Path

    @property
    def rel_source(self) -> str:
        return self.source_path.relative_to(REPO_ROOT).as_posix()

    @property
    def rel_test(self) -> str:
        return self.test_path.relative_to(REPO_ROOT).as_posix()


def _is_skipped_path(path: Path) -> bool:
    return any(part in SKIP_DIR_NAMES for part in path.parts)


def _python_test_exists(app_dir: Path, stem: str) -> bool:
    tests_dir = app_dir / "tests"
    if not tests_dir.is_dir():
        return False
    direct = tests_dir / f"test_{stem}.py"
    if direct.is_file():
        return True
    pattern = re.compile(rf"test_.*{re.escape(stem)}.*\.py$")
    return any(pattern.match(p.name) for p in tests_dir.glob("test_*.py"))


def _node_test_exists(source: Path) -> bool:
    colocated = source.with_suffix(".test.js")
    if colocated.is_file():
        return True
    stem = source.stem
    return any(
        p.name in {f"{stem}.test.js", f"{stem}.test.ts"}
        for p in source.parent.glob("*.test.*")
    )


def _go_test_exists(source: Path) -> bool:
    test_file = source.parent / f"{source.stem}_test.go"
    return test_file.is_file()


def _typescript_test_exists(source: Path) -> bool:
    colocated = source.with_suffix(".test.ts")
    if colocated.is_file():
        return True
    tests_dir = source.parent.parent / "tests"
    if tests_dir.is_dir():
        return (tests_dir / f"{source.stem}.test.ts").is_file()
    return False


def _python_targets(app_dir: Path, app: str) -> list[Target]:
    src_root = app_dir / "src"
    if not src_root.is_dir():
        return []
    out: list[Target] = []
    for source in sorted(src_root.rglob("*.py")):
        if source.name in SKIP_SOURCE_NAMES or source.stem in SKIP_SOURCE_STEMS:
            continue
        if _python_test_exists(app_dir, source.stem):
            continue
        test_path = app_dir / "tests" / f"test_{source.stem}.py"
        out.append(
            Target(
                language="python",
                app=app,
                app_dir=app_dir,
                source_path=source,
                test_path=test_path,
            )
        )
    return out


def _node_targets(app_dir: Path, app: str) -> list[Target]:
    src_root = app_dir / "src"
    if not src_root.is_dir():
        return []
    out: list[Target] = []
    for source in sorted(src_root.rglob("*.js")):
        if source.name.endswith(".test.js") or source.stem in SKIP_SOURCE_STEMS:
            continue
        if _node_test_exists(source):
            continue
        test_path = source.with_suffix(".test.js")
        out.append(
            Target(
                language="node",
                app=app,
                app_dir=app_dir,
                source_path=source,
                test_path=test_path,
            )
        )
    return out


def _go_targets(app_dir: Path, app: str) -> list[Target]:
    out: list[Target] = []
    for source in sorted(app_dir.glob("*.go")):
        if source.name.endswith("_test.go") or source.stem in SKIP_SOURCE_STEMS:
            continue
        if _go_test_exists(source):
            continue
        test_path = source.parent / f"{source.stem}_test.go"
        out.append(
            Target(
                language="go",
                app=app,
                app_dir=app_dir,
                source_path=source,
                test_path=test_path,
            )
        )
    return out


def _typescript_targets(app_dir: Path, app: str) -> list[Target]:
    src_root = app_dir / "src"
    if not src_root.is_dir():
        return []
    out: list[Target] = []
    for source in sorted(src_root.rglob("*.ts")):
        if source.name.endswith(".test.ts") or source.suffix != ".ts":
            continue
        if source.name in SKIP_SOURCE_NAMES or source.stem in SKIP_SOURCE_STEMS:
            continue
        if _typescript_test_exists(source):
            continue
        test_path = source.with_suffix(".test.ts")
        out.append(
            Target(
                language="typescript",
                app=app,
                app_dir=app_dir,
                source_path=source,
                test_path=test_path,
            )
        )
    return out


def discover_targets(
    *,
    repo_root: Path = REPO_ROOT,
    max_targets: int = 2,
) -> list[Target]:
    """Return up to max_targets files without tests, stable sort for reproducibility."""
    candidates: list[Target] = []

    for app in CI_APPS["python"]:
        app_dir = repo_root / "apps" / "python" / app
        if app_dir.is_dir() and not _is_skipped_path(app_dir):
            candidates.extend(_python_targets(app_dir, app))

    for app in CI_APPS["node"]:
        app_dir = repo_root / "apps" / "node" / app
        if app_dir.is_dir() and not _is_skipped_path(app_dir):
            candidates.extend(_node_targets(app_dir, app))

    for app in CI_APPS["go"]:
        app_dir = repo_root / "apps" / "go" / app
        if app_dir.is_dir() and not _is_skipped_path(app_dir):
            candidates.extend(_go_targets(app_dir, app))

    for app in CI_APPS["typescript"]:
        app_dir = repo_root / "apps" / "typescript" / app
        if app_dir.is_dir() and not _is_skipped_path(app_dir):
            candidates.extend(_typescript_targets(app_dir, app))

    candidates.sort(key=lambda t: (t.language, t.app, t.rel_source))
    return candidates[:max_targets]
