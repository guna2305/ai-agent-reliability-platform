"""Unit tests for the cost calculator."""
from decimal import Decimal

from src.infrastructure.ai.cost_calculator import calculate_cost, get_supported_models


def test_ollama_is_always_free():
    cost = calculate_cost("ollama", "llama3.2", input_tokens=10_000, output_tokens=5_000)
    assert cost == Decimal("0")


def test_ollama_unknown_model_is_free():
    cost = calculate_cost("ollama", "some-future-model", input_tokens=50_000, output_tokens=10_000)
    assert cost == Decimal("0")


def test_openai_gpt4o_mini_cost():
    # gpt-4o-mini: $0.00015/1K input, $0.0006/1K output
    cost = calculate_cost("openai", "gpt-4o-mini", input_tokens=1_000, output_tokens=1_000)
    expected = Decimal("0.00015") + Decimal("0.0006")
    assert cost == expected.quantize(Decimal("0.00000001"))


def test_openai_gpt4o_cost():
    # gpt-4o: $0.005/1K input, $0.015/1K output
    cost = calculate_cost("openai", "gpt-4o", input_tokens=2_000, output_tokens=500)
    expected = (Decimal("0.005") * 2 + Decimal("0.015") * Decimal("0.5")).quantize(
        Decimal("0.00000001")
    )
    assert cost == expected


def test_zero_tokens_returns_zero():
    cost = calculate_cost("openai", "gpt-4o", input_tokens=0, output_tokens=0)
    assert cost == Decimal("0")


def test_get_supported_models_includes_ollama():
    models = get_supported_models()
    ollama_models = [m for m in models if m["provider"] == "ollama"]
    assert len(ollama_models) > 0
    for m in ollama_models:
        assert m["is_free"] is True
        assert m["input_per_1k_tokens"] == 0.0


def test_get_supported_models_includes_openai():
    models = get_supported_models()
    openai_models = [m for m in models if m["provider"] == "openai"]
    assert len(openai_models) > 0
