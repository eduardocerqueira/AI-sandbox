from hf_pipeline_hello.main import format_prediction, run_sentiment


def test_format_prediction() -> None:
    line = format_prediction("great", {"label": "POSITIVE", "score": 0.99})
    assert "POSITIVE" in line
    assert "0.990" in line


def test_run_sentiment_with_mock_classifier() -> None:
    def fake_classifier(texts: list[str]) -> list[dict[str, float | str]]:
        return [{"label": "POSITIVE", "score": 0.9} for _ in texts]

    lines = run_sentiment(["a", "b"], classifier=fake_classifier)
    assert len(lines) == 2
    assert all("POSITIVE" in line for line in lines)
