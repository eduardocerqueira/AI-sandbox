"""Run the same test commands as .github/workflows/pr-check.yml for affected apps."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from test_bot.discover import REPO_ROOT, Target

PACKAGE_JSON_TEST_SCRIPT = "node --import tsx --test src/**/*.test.ts"


def _ensure_typescript_test_script(app_dir: Path, *, dry_run: bool) -> None:
    pkg_path = app_dir / "package.json"
    data = json.loads(pkg_path.read_text(encoding="utf-8"))
    scripts = data.setdefault("scripts", {})
    if scripts.get("test"):
        return
    scripts["test"] = PACKAGE_JSON_TEST_SCRIPT
    if dry_run:
        print(f"[dry-run] would add npm test script to {pkg_path}")
        return
    dev_deps = data.setdefault("devDependencies", {})
    dev_deps.setdefault("tsx", "^4.19.0")
    pkg_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"Added test script to {pkg_path.relative_to(REPO_ROOT)}")
    subprocess.run(["npm", "install"], cwd=app_dir, check=True, text=True)


def run_single_app(
    language: str,
    app: str,
    app_dir: Path,
    *,
    dry_run: bool,
) -> None:
    """Run tests for one app (same commands as pr-check.yml)."""
    label = f"{language}/{app}"
    if language == "python":
        cmd = [
            "bash",
            "-lc",
            "python -m pip install -q --upgrade pip && "
            'pip install -q -e ".[dev]" && pytest -q',
        ]
    elif language == "node":
        cmd = ["bash", "-lc", "npm ci && npm test"]
    elif language == "go":
        cmd = ["go", "test", "./..."]
    elif language == "typescript":
        _ensure_typescript_test_script(app_dir, dry_run=dry_run)
        cmd = ["bash", "-lc", "npm ci && npm test"]
    else:
        raise ValueError(f"Unknown language: {language}")

    print(f"Running tests for {label} …")
    if dry_run:
        print(f"[dry-run] would run in {app_dir}: {' '.join(cmd)}")
        return

    result = subprocess.run(
        cmd,
        cwd=app_dir,
        check=False,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        detail = (result.stderr or "") + (result.stdout or "")
        raise subprocess.CalledProcessError(
            result.returncode,
            cmd,
            output=detail,
            stderr=result.stderr,
            stdout=result.stdout,
        )
    print(f"Passed: {label}")


def run_app_tests(targets: list[Target], *, dry_run: bool) -> None:
    apps: set[tuple[str, str, Path]] = {
        (t.language, t.app, t.app_dir) for t in targets
    }

    for language, app, app_dir in sorted(apps):
        run_single_app(language, app, app_dir, dry_run=dry_run)
