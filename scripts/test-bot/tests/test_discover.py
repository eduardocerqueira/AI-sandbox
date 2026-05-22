from test_bot.discover import REPO_ROOT, discover_targets


def test_repo_root_points_at_monorepo() -> None:
    assert (REPO_ROOT / "apps" / "README.md").is_file()


def test_discover_returns_bounded_list() -> None:
    targets = discover_targets(max_targets=5)
    assert len(targets) <= 5
    for t in targets:
        assert t.source_path.is_file()
        assert not t.test_path.is_file()


def test_discover_skips_templates() -> None:
    targets = discover_targets(max_targets=100)
    assert all("_template" not in t.rel_source for t in targets)
