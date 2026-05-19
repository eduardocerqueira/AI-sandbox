from hf_agents_lab.prompts import EXAMPLE_PROMPTS


def test_example_prompts_unique_names() -> None:
    names = [name for name, _ in EXAMPLE_PROMPTS]
    assert len(names) == len(set(names))
    assert len(EXAMPLE_PROMPTS) >= 3
