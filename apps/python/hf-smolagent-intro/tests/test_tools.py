from unittest.mock import MagicMock, patch

from hf_smolagent_intro.tools import lookup_top_model, resolve_learning_tip


@patch("hf_smolagent_intro.tools.list_models")
def test_lookup_top_model(mock_list_models: MagicMock) -> None:
    model = MagicMock()
    model.id = "distilbert-base-uncased-finetuned-sst-2-english"
    mock_list_models.return_value = iter([model])

    assert lookup_top_model("text-classification") == "distilbert-base-uncased-finetuned-sst-2-english"
    mock_list_models.assert_called_once_with(
        pipeline_tag="text-classification",
        sort="downloads",
        limit=1,
    )


def test_resolve_learning_tip_known() -> None:
    tip = resolve_learning_tip("I want to learn about RAG")
    assert "NVIDIA" in tip or "RAG" in tip


def test_resolve_learning_tip_unknown() -> None:
    tip = resolve_learning_tip("quantum-computing-xyz")
    assert "No tip matched" in tip
    assert "agents" in tip
