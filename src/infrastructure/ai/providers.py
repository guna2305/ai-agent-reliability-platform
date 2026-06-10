"""AI provider abstraction.

Ollama is the default (free, local). OpenAI and Anthropic are optional
integrations enabled only when their API keys are configured.
"""
from __future__ import annotations

import logging
from typing import Any

import httpx

from src.infrastructure.config.settings import get_settings

logger = logging.getLogger(__name__)


class LLMResponse:
    __slots__ = ("content", "input_tokens", "output_tokens", "model", "provider")

    def __init__(
        self,
        content: str,
        input_tokens: int,
        output_tokens: int,
        model: str,
        provider: str,
    ) -> None:
        self.content = content
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.model = model
        self.provider = provider


# ── Ollama (default, free) ────────────────────────────────────────────────────

async def call_ollama(
    prompt: str,
    system: str | None = None,
    model: str | None = None,
    temperature: float = 0.1,
    max_tokens: int = 2048,
) -> LLMResponse:
    settings = get_settings()
    model = model or settings.ollama_default_model
    messages: list[dict[str, str]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            f"{settings.ollama_base_url}/api/chat",
            json={
                "model": model,
                "messages": messages,
                "stream": False,
                "options": {"temperature": temperature, "num_predict": max_tokens},
            },
        )
        resp.raise_for_status()
        data = resp.json()

    content: str = data["message"]["content"]
    # Ollama returns prompt_eval_count / eval_count
    input_tokens: int = data.get("prompt_eval_count", 0)
    output_tokens: int = data.get("eval_count", 0)

    return LLMResponse(
        content=content,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        model=model,
        provider="ollama",
    )


async def embed_ollama(text: str, model: str | None = None) -> list[float]:
    settings = get_settings()
    model = model or settings.ollama_embed_model
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"{settings.ollama_base_url}/api/embeddings",
            json={"model": model, "prompt": text},
        )
        resp.raise_for_status()
        return resp.json()["embedding"]


# ── OpenAI (optional) ─────────────────────────────────────────────────────────

async def call_openai(
    prompt: str,
    system: str | None = None,
    model: str | None = None,
    temperature: float = 0.1,
    max_tokens: int = 2048,
) -> LLMResponse:
    settings = get_settings()
    if not settings.openai_enabled:
        raise RuntimeError("OpenAI API key is not configured. Set OPENAI_API_KEY or use Ollama.")

    try:
        from openai import AsyncOpenAI  # type: ignore[import]
    except ImportError:
        raise RuntimeError("openai package not installed. Run: pip install openai")

    model = model or settings.openai_default_model
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    messages: list[dict[str, str]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    resp = await client.chat.completions.create(
        model=model, messages=messages,  # type: ignore[arg-type]
        temperature=temperature, max_tokens=max_tokens,
    )
    choice = resp.choices[0]
    return LLMResponse(
        content=choice.message.content or "",
        input_tokens=resp.usage.prompt_tokens if resp.usage else 0,
        output_tokens=resp.usage.completion_tokens if resp.usage else 0,
        model=model,
        provider="openai",
    )


# ── Anthropic (optional) ─────────────────────────────────────────────────────

async def call_anthropic(
    prompt: str,
    system: str | None = None,
    model: str | None = None,
    temperature: float = 0.1,
    max_tokens: int = 2048,
) -> LLMResponse:
    settings = get_settings()
    if not settings.anthropic_enabled:
        raise RuntimeError("Anthropic API key is not configured. Set ANTHROPIC_API_KEY or use Ollama.")

    try:
        import anthropic  # type: ignore[import]
    except ImportError:
        raise RuntimeError("anthropic package not installed. Run: pip install anthropic")

    model = model or settings.anthropic_default_model
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    kwargs: dict[str, Any] = {
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system:
        kwargs["system"] = system

    resp = await client.messages.create(**kwargs)
    content = resp.content[0].text if resp.content else ""
    return LLMResponse(
        content=content,
        input_tokens=resp.usage.input_tokens,
        output_tokens=resp.usage.output_tokens,
        model=model,
        provider="anthropic",
    )


# ── Router: picks provider automatically ─────────────────────────────────────

async def call_llm(
    prompt: str,
    system: str | None = None,
    provider: str | None = None,
    model: str | None = None,
    temperature: float = 0.1,
    max_tokens: int = 2048,
) -> LLMResponse:
    """Route to the correct provider. Defaults to Ollama."""
    settings = get_settings()
    provider = provider or settings.default_provider

    if provider == "openai":
        return await call_openai(prompt, system, model, temperature, max_tokens)
    if provider == "anthropic":
        return await call_anthropic(prompt, system, model, temperature, max_tokens)
    return await call_ollama(prompt, system, model, temperature, max_tokens)
