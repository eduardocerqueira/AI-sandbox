"""Tests for path validation."""

from issue_bot.paths import is_allowed_path, normalize_path, paths_mentioned_in_text


def test_normalize_rejects_traversal() -> None:
    assert normalize_path("../etc/passwd") is None
    assert normalize_path("docs/agents.md") == "docs/agents.md"


def test_is_allowed_path() -> None:
    assert is_allowed_path("docs/agents.md")
    assert is_allowed_path("README.md")
    assert not is_allowed_path(".env")
    assert not is_allowed_path("TODO.md")


def test_paths_mentioned_in_text() -> None:
    text = "Update `docs/agents.md` and README.md"
    found = paths_mentioned_in_text(text)
    assert "docs/agents.md" in found
