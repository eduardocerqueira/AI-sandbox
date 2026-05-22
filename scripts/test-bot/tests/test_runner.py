from __future__ import annotations

import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from test_bot import runner


@pytest.fixture(autouse=True)
def _patch_repo_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(runner, "REPO_ROOT", tmp_path)


def test_ensure_typescript_test_script_adds_script_and_tsx(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    app_dir = tmp_path / "ui"
    app_dir.mkdir()
    pkg = app_dir / "package.json"
    pkg.write_text(json.dumps({"name": "ui", "scripts": {}}), encoding="utf-8")

    calls: list[tuple[list[str], Path]] = []

    def _fake_run(cmd: list[str], cwd: Path, check: bool, text: bool) -> SimpleNamespace:
        assert check is True
        assert text is True
        calls.append((cmd, cwd))
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(runner.subprocess, "run", _fake_run)

    runner._ensure_typescript_test_script(app_dir, dry_run=False)
    data = json.loads(pkg.read_text(encoding="utf-8"))

    assert data["scripts"]["test"] == runner.PACKAGE_JSON_TEST_SCRIPT
    assert "tsx" in data["devDependencies"]
    assert calls == [(["npm", "install"], app_dir)]


def test_ensure_typescript_test_script_dry_run_does_not_modify(tmp_path: Path) -> None:
    app_dir = tmp_path / "ui"
    app_dir.mkdir()
    pkg = app_dir / "package.json"
    original = {"name": "ui", "scripts": {}}
    pkg.write_text(json.dumps(original), encoding="utf-8")

    runner._ensure_typescript_test_script(app_dir, dry_run=True)

    assert json.loads(pkg.read_text(encoding="utf-8")) == original


def test_ensure_typescript_test_script_noop_if_test_script_exists(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    app_dir = tmp_path / "ui"
    app_dir.mkdir()
    pkg = app_dir / "package.json"
    pkg.write_text(
        json.dumps({"name": "ui", "scripts": {"test": "node --test"}}),
        encoding="utf-8",
    )

    def _fail_if_called(*args: object, **kwargs: object) -> None:
        raise AssertionError("subprocess.run should not be called")

    monkeypatch.setattr(runner.subprocess, "run", _fail_if_called)
    runner._ensure_typescript_test_script(app_dir, dry_run=False)
    data = json.loads(pkg.read_text(encoding="utf-8"))
    assert data["scripts"]["test"] == "node --test"


def test_run_single_app_unknown_language(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Unknown language"):
        runner.run_single_app("ruby", "x", tmp_path, dry_run=False)


def test_run_single_app_dry_run_skips_subprocess(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    called = False

    def _fake_run(*args: object, **kwargs: object) -> None:
        nonlocal called
        called = True

    monkeypatch.setattr(runner.subprocess, "run", _fake_run)
    runner.run_single_app("node", "demo", tmp_path, dry_run=True)
    assert called is False


def test_run_single_app_raises_called_process_error_on_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def _fake_run(
        cmd: list[str],
        cwd: Path,
        check: bool,
        text: bool,
        capture_output: bool,
    ) -> SimpleNamespace:
        return SimpleNamespace(returncode=1, stdout="out", stderr="err")

    monkeypatch.setattr(runner.subprocess, "run", _fake_run)

    with pytest.raises(subprocess.CalledProcessError) as exc:
        runner.run_single_app("go", "demo", tmp_path, dry_run=False)

    assert exc.value.stdout == "out"
    assert exc.value.stderr == "err"


def test_run_single_app_passes_on_success(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, object] = {}

    def _fake_run(
        cmd: list[str],
        cwd: Path,
        check: bool,
        text: bool,
        capture_output: bool,
    ) -> SimpleNamespace:
        seen["cmd"] = cmd
        seen["cwd"] = cwd
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(runner.subprocess, "run", _fake_run)
    runner.run_single_app("go", "demo", tmp_path, dry_run=False)

    assert seen["cmd"] == ["go", "test", "./..."]
    assert seen["cwd"] == tmp_path
