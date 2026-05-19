from unittest.mock import MagicMock, patch

from hf_smolagent_intro.main import configure_hf_token, run_demo_tip, run_demo_tool


def test_configure_hf_token(monkeypatch) -> None:
    monkeypatch.setenv("HF_TOKEN", "hf_test")
    assert configure_hf_token() == "hf_test"


@patch("hf_smolagent_intro.tools.list_models")
def test_run_demo_tool(mock_list_models, capsys) -> None:
    model = MagicMock()
    model.id = "test-model"
    mock_list_models.return_value = iter([model])

    assert run_demo_tool("summarization") == "test-model"
    out = capsys.readouterr().out
    assert "summarization" in out
    assert "test-model" in out


def test_run_demo_tip(capsys) -> None:
    assert "agents" in run_demo_tip("agents").lower() or "Agents" in run_demo_tip("agents")
    out = capsys.readouterr().out
    assert "agents" in out
