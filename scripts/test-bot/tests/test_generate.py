from __future__ import annotations

from pathlib import Path

import pytest

import test_bot.discover as discover_mod
import test_bot.prompts as prompts_mod
from test_bot.discover import Target
from test_bot import generate


@pytest.fixture(autouse=True)
def _patch_repo_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(discover_mod, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(prompts_mod, "REPO_ROOT", tmp_path)


def _target(tmp_path: Path, language: str = "python") -> Target:
    app_dir = tmp_path / "app"
    source_path = app_dir / "src" / "module.py"
    test_path = app_dir / "tests" / "test_module.py"
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
    return Target(
        language=language,
        app="demo",
        app_dir=app_dir,
        source_path=source_path,
        test_path=test_path,
    )


def test_extract_code_block_returns_fenced_content() -> None:
    text = "intro\n```python\nassert 1 == 1\n```\noutro"
    assert generate.extract_code_block(text) == "assert 1 == 1"


def test_extract_code_block_returns_trimmed_plain_text() -> None:
    assert generate.extract_code_block("  a = 1  \n") == "a = 1"


def test_find_example_test_for_python(tmp_path: Path) -> None:
    target = _target(tmp_path, language="python")
    (target.app_dir / "tests").mkdir(parents=True, exist_ok=True)
    example = target.app_dir / "tests" / "test_example.py"
    example.write_text("def test_x(): pass\n", encoding="utf-8")

    assert generate._find_example_test(target) == "def test_x(): pass\n"


def test_find_example_test_for_node(tmp_path: Path) -> None:
    target = _target(tmp_path, language="node")
    node_source = target.app_dir / "src" / "module.js"
    node_source.write_text("export const x = 1;\n", encoding="utf-8")
    target = Target(
        language="node",
        app=target.app,
        app_dir=target.app_dir,
        source_path=node_source,
        test_path=target.app_dir / "src" / "module.test.js",
    )
    example = target.app_dir / "src" / "alpha.test.js"
    example.write_text("test('x', () => {});\n", encoding="utf-8")

    assert generate._find_example_test(target) == "test('x', () => {});\n"


def test_generate_test_content_requires_api_key(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = _target(tmp_path)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="OPENAI_API_KEY is not set"):
        generate.generate_test_content(target)


def test_generate_test_content_uses_client_and_returns_newline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = _target(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "dummy")
    monkeypatch.setenv("TEST_BOT_MODEL", "model-x")
    monkeypatch.setattr(generate, "build_user_prompt", lambda *args, **kwargs: "prompt")

    captured: dict[str, object] = {}

    class _FakeResponse:
        class _Choices:
            class _Message:
                content = "```python\ndef test_ok():\n    assert True\n```"

            message = _Message()

        choices = [_Choices()]

    class _FakeClient:
        def __init__(self, *, api_key: str):
            captured["api_key"] = api_key
            self.chat = self
            self.completions = self

        def create(self, **kwargs: object) -> _FakeResponse:
            captured["kwargs"] = kwargs
            return _FakeResponse()

    monkeypatch.setattr(generate, "OpenAI", _FakeClient)

    out = generate.generate_test_content(target)

    assert out.endswith("\n")
    assert "def test_ok" in out
    assert captured["api_key"] == "dummy"
    assert captured["kwargs"]["model"] == "model-x"


def test_generate_test_content_rejects_empty_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = _target(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "dummy")
    monkeypatch.setattr(generate, "build_user_prompt", lambda *args, **kwargs: "prompt")

    class _FakeResponse:
        class _Choices:
            class _Message:
                content = "   "

            message = _Message()

        choices = [_Choices()]

    class _FakeClient:
        def __init__(self, *, api_key: str):
            self.chat = self
            self.completions = self

        def create(self, **kwargs: object) -> _FakeResponse:
            return _FakeResponse()

    monkeypatch.setattr(generate, "OpenAI", _FakeClient)

    with pytest.raises(RuntimeError, match="Empty test generation"):
        generate.generate_test_content(target)


def test_write_test_file_writes_file(tmp_path: Path) -> None:
    target = _target(tmp_path)
    generate.write_test_file(target, "def test_a():\n    pass\n", dry_run=False)
    assert target.test_path.read_text(encoding="utf-8").startswith("def test_a")


def test_write_test_file_dry_run_does_not_write(tmp_path: Path) -> None:
    target = _target(tmp_path)
    generate.write_test_file(target, "x", dry_run=True)
    assert not target.test_path.exists()
