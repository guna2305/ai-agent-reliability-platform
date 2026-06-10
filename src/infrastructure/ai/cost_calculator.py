"""Token cost calculator.

Ollama models are always free ($0). OpenAI / Anthropic costs are
calculated only when those providers are used.
"""
from __future__ import annotations

from decimal import Decimal

# Pricing per 1,000 tokens (USD) — updated June 2026
# Structure: {"input": cost_per_1k_input, "output": cost_per_1k_output}
_PRICING: dict[str, dict[str, float]] = {
    # Ollama (free, local)
    "ollama/llama3.2":         {"input": 0.0, "output": 0.0},
    "ollama/llama3.1":         {"input": 0.0, "output": 0.0},
    "ollama/mistral":          {"input": 0.0, "output": 0.0},
    "ollama/mixtral":          {"input": 0.0, "output": 0.0},
    "ollama/codellama":        {"input": 0.0, "output": 0.0},
    "ollama/gemma2":           {"input": 0.0, "output": 0.0},
    "ollama/phi3":             {"input": 0.0, "output": 0.0},
    "ollama/qwen2.5":          {"input": 0.0, "output": 0.0},
    # OpenAI (optional)
    "openai/gpt-4o":           {"input": 0.005,   "output": 0.015},
    "openai/gpt-4o-mini":      {"input": 0.00015, "output": 0.0006},
    "openai/gpt-4-turbo":      {"input": 0.01,    "output": 0.03},
    "openai/gpt-3.5-turbo":    {"input": 0.0005,  "output": 0.0015},
    # Anthropic (optional)
    "anthropic/claude-opus-4-8":              {"input": 0.015,  "output": 0.075},
    "anthropic/claude-sonnet-4-6":            {"input": 0.003,  "output": 0.015},
    "anthropic/claude-haiku-4-5-20251001":    {"input": 0.00025, "output": 0.00125},
}


def calculate_cost(
    provider: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
) -> Decimal:
    """Return total cost in USD as Decimal. Free for Ollama."""
    key = f"{provider.lower()}/{model.lower()}"
    pricing = _PRICING.get(key)

    if pricing is None:
        # Unknown model: assume free if Ollama, otherwise estimate gpt-4o-mini
        if provider.lower() == "ollama":
            return Decimal("0")
        fallback = _PRICING["openai/gpt-4o-mini"]
        pricing = fallback

    input_cost = Decimal(str(pricing["input"])) * Decimal(str(input_tokens)) / Decimal("1000")
    output_cost = Decimal(str(pricing["output"])) * Decimal(str(output_tokens)) / Decimal("1000")
    return (input_cost + output_cost).quantize(Decimal("0.00000001"))


def get_supported_models() -> list[dict]:
    """Return all models with their pricing."""
    result = []
    for key, pricing in _PRICING.items():
        provider, model = key.split("/", 1)
        result.append({
            "provider": provider,
            "model": model,
            "input_per_1k_tokens": pricing["input"],
            "output_per_1k_tokens": pricing["output"],
            "is_free": pricing["input"] == 0.0 and pricing["output"] == 0.0,
        })
    return result
