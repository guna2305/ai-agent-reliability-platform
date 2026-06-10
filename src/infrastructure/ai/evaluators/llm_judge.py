"""LLM-as-judge evaluator.

Uses Ollama (llama3.2 by default) to score agent responses on
correctness, relevance, faithfulness, and helpfulness.
Forces JSON output via Ollama's format=json mode for reliable parsing.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

import httpx

from src.infrastructure.config.settings import get_settings

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are an expert AI evaluator. Evaluate the given response objectively. "
    "Always respond with a single valid JSON object. "
    "The score must be a float between 0.0 and 1.0."
)

_CORRECTNESS_TMPL = """\
Evaluate the factual correctness of an AI assistant's response.

Question: {question}
Expected Answer: {expected}
AI Response: {response}

Score 1.0 = perfectly correct and complete.
Score 0.5 = partially correct, minor errors or omissions.
Score 0.0 = completely wrong or irrelevant.

Respond with JSON: {{"score": <0.0-1.0>, "reasoning": "<one sentence>"}}"""

_RELEVANCE_TMPL = """\
Evaluate how relevant the AI response is to the question.

Question: {question}
AI Response: {response}

Score 1.0 = directly and completely answers the question.
Score 0.5 = partially relevant, drifts off topic.
Score 0.0 = completely off-topic or refuses to answer.

Respond with JSON: {{"score": <0.0-1.0>, "reasoning": "<one sentence>"}}"""

_FAITHFULNESS_TMPL = """\
Evaluate whether the AI response is grounded in the provided context.

Context: {context}
AI Response: {response}

Score 1.0 = every claim is supported by the context.
Score 0.5 = most claims supported, some unsupported assertions.
Score 0.0 = response contradicts or ignores the context (hallucination).

Respond with JSON: {{"score": <0.0-1.0>, "reasoning": "<one sentence>"}}"""

_HELPFULNESS_TMPL = """\
Evaluate how helpful the AI response is to the user.

Question: {question}
AI Response: {response}

Score 1.0 = highly helpful, actionable, clear, and complete.
Score 0.5 = somewhat helpful but incomplete or unclear.
Score 0.0 = not helpful at all.

Respond with JSON: {{"score": <0.0-1.0>, "reasoning": "<one sentence>"}}"""


@dataclass
class JudgeScore:
    score: float
    reasoning: str
    metric: str


async def _judge(prompt: str, model: str | None = None) -> JudgeScore | None:
    settings = get_settings()
    model = model or settings.eval_judge_model

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{settings.ollama_base_url}/api/chat",
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": _SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    "stream": False,
                    "format": "json",
                    "options": {"temperature": 0.1},
                },
            )
            resp.raise_for_status()
            content = resp.json()["message"]["content"]
            data = json.loads(content)
            score = max(0.0, min(1.0, float(data.get("score", 0.5))))
            return JudgeScore(
                score=round(score, 4),
                reasoning=str(data.get("reasoning", "")),
                metric="",
            )
    except Exception as e:
        logger.warning("LLM judge failed", extra={"error": str(e), "model": model})
        return None


async def score_correctness(
    question: str,
    response: str,
    expected: str,
    model: str | None = None,
) -> JudgeScore:
    prompt = _CORRECTNESS_TMPL.format(
        question=question, expected=expected, response=response
    )
    result = await _judge(prompt, model)
    if result:
        result.metric = "correctness"
        return result
    return JudgeScore(score=0.5, reasoning="Judge unavailable", metric="correctness")


async def score_relevance(
    question: str,
    response: str,
    model: str | None = None,
) -> JudgeScore:
    prompt = _RELEVANCE_TMPL.format(question=question, response=response)
    result = await _judge(prompt, model)
    if result:
        result.metric = "relevance"
        return result
    return JudgeScore(score=0.5, reasoning="Judge unavailable", metric="relevance")


async def score_faithfulness(
    context: str,
    response: str,
    model: str | None = None,
) -> JudgeScore:
    prompt = _FAITHFULNESS_TMPL.format(context=context, response=response)
    result = await _judge(prompt, model)
    if result:
        result.metric = "faithfulness"
        return result
    return JudgeScore(score=0.5, reasoning="Judge unavailable", metric="faithfulness")


async def score_helpfulness(
    question: str,
    response: str,
    model: str | None = None,
) -> JudgeScore:
    prompt = _HELPFULNESS_TMPL.format(question=question, response=response)
    result = await _judge(prompt, model)
    if result:
        result.metric = "helpfulness"
        return result
    return JudgeScore(score=0.5, reasoning="Judge unavailable", metric="helpfulness")


async def run_full_judge(
    question: str,
    response: str,
    expected: str | None = None,
    context: str | None = None,
    model: str | None = None,
) -> dict[str, JudgeScore]:
    """Run all applicable judge metrics and return a dict of results."""
    results: dict[str, JudgeScore] = {}

    results["relevance"] = await score_relevance(question, response, model)
    results["helpfulness"] = await score_helpfulness(question, response, model)

    if expected:
        results["correctness"] = await score_correctness(question, response, expected, model)

    if context:
        results["faithfulness"] = await score_faithfulness(context, response, model)

    return results
