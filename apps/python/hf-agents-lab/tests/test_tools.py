from unittest.mock import MagicMock, patch

from hf_agents_lab.tools import lookup_top_model, resolve_learning_tip, safe_calculate


@patch("hf_agents_lab.tools.list_models")
def test_lookup_top_model(mock_list_models: MagicMock) -> None:
    model = MagicMock()
    model.id = "test-model"
    mock_list_models.return_value = iter([model])
    assert lookup_top_model("summarization") == "test-model"


def test_resolve_learning_tip() -> None:
    assert "Agents" in resolve_learning_tip("agents") or "agents" in resolve_learning_tip("agents")


def test_safe_calculate() -> None:
    assert safe_calculate("(10 + 5) * 2") == "30"
    assert safe_calculate("1/0").startswith("Error:")
