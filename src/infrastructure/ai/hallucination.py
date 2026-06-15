"""Hallucination detection — all Ollama-powered, no paid APIs.

Three complementary strategies (mirrors the DetectionMethod value object):

  REFERENCE_BASED        Compare the response against a known-good reference
                         answer; unsupported claims are hallucinations.
  RETRIEVAL_CONSISTENCY  Check the response is grounded in the retrieved
                         context; claims absent from context are flagged.
  LLM_JUDGE              Ask the model to self-critique and list any
                         fabricated / unverifiable statements.

Each detector returns a HallucinationSignal:
  score      0.0 = fully grounded, 1.0 = entirely hallucinated
  confidence 0.0–1.0 how sure the detector is
  segments   list of {"text", "reason"} for flagged spans
  reasoning  one-line human summary

combine_signals() fuses multiple signals into one confidence-weighted score.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field

import httpx

from src.domain.value_objects import DetectionMethod
from src.infrastructure.config.settings import get_settings

logger = logging.getLogger(__name__)

_SYSTEM = (
    "You are a meticulous fact-checking system that detects hallucinations in "
    "AI-generated text. A hallucination is any statement that is fabricated, "
    "unverifiable, or unsupported by the provided reference material. "
    "Respond only with a single valid JSON object."
)

_REFERENCE_TMPL = """\
Compare the AI response against the reference answer. Identify any statements in
the response that are NOT supported by — or that contradict — the reference.

Reference answer:
{reference}

AI response:
{response}

Return JSON:
{{"hallucination_score": <0.0-1.0>, "confidence": <0.0-1.0>,
  "flagged_segments": [{{"text": "<quote>", "reason": "<why>"}}],
  "reasoning": "<one sentence>"}}
Where hallucination_score 0.0 = fully supported, 1.0 = entirely fabricated."""

_RETRIEVAL_TMPL = """\
Determine whether the AI response is grounded in the retrieved context.
Flag any claim that does not appear in, or cannot be inferred from, the context.

Retrieved context:
{context}

AI response:
{response}

Return JSON:
{{"hallucination_score": <0.0-1.0>, "confidence": <0.0-1.0>,
  "flagged_segments": [{{"text": "<quote>", "reason": "<why>"}}],
  "reasoning": "<one sentence>"}}
Where hallucination_score 0.0 = fully grounded in context, 1.0 = ungrounded."""

_SELF_JUDGE_TMPL = """\
Critically review the AI response below for hallucinations: fabricated facts,
invented citations, made-up numbers, or confident claims that cannot be verified.

Question: {question}
AI response:
{response}

Return JSON:
{{"hallucination_score": <0.0-1.0>, "confidence": <0.0-1.0>,
  "flagged_segments": [{{"text": "<quote>", "reason": "<why>"}}],
  "reasoning": "<one sentence>"}}"""


@dataclass
class HallucinationSignal:
    method: DetectionMethod
    score: float
    confidence: float
    flagged_segments: list[dict[str, str]] = field(default_factory=list)
    reasoning: str = ""


def _clamp(v: float) -> float:
    return max(0.0, min(1.0, v))


async def _detect(prompt: str, method: DetectionMethod, model: str | None) -> HallucinationSignal:
    settings = get_settings()
    model = model or settings.eval_judge_model
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{settings.ollama_base_url}/api/chat",
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": _SYSTEM},
                        {"role": "user", "content": prompt},
                    ],
                    "stream": False,
                    "format": "json",
                    "options": {"temperature": 0.0},
                },
            )
            resp.raise_for_status()
            data = json.loads(resp.json()["message"]["content"])
            return HallucinationSignal(
                method=method,
                score=round(_clamp(float(data.get("hallucination_score", 0.0))), 4),
                confidence=round(_clamp(float(data.get("confidence", 0.5))), 4),
                flagged_segments=data.get("flagged_segments", []) or [],
                reasoning=str(data.get("reasoning", "")),
            )
    except Exception as e:
        logger.warning(
            "Hallucination detector failed",
            extra={"error": str(e), "method": method.value, "model": model},
        )
        # Low-confidence neutral signal so a dead detector doesn't skew the score
        return HallucinationSignal(
            method=method, score=0.0, confidence=0.0,
            reasoning="Detector unavailable",
        )


async def detect_reference_based(
    response: str,
    reference: str,
    model: str | None = None,
) -> HallucinationSignal:
    prompt = _REFERENCE_TMPL.format(reference=reference, response=response)
    return await _detect(prompt, DetectionMethod.REFERENCE_BASED, model)


async def detect_retrieval_consistency(
    response: str,
    context_chunks: list[str],
    model: str | None = None,
) -> HallucinationSignal:
    context = "\n\n".join(context_chunks)
    prompt = _RETRIEVAL_TMPL.format(context=context, response=response)
    return await _detect(prompt, DetectionMethod.RETRIEVAL_CONSISTENCY, model)


async def detect_llm_judge(
    question: str,
    response: str,
    model: str | None = None,
) -> HallucinationSignal:
    prompt = _SELF_JUDGE_TMPL.format(question=question, response=response)
    return await _detect(prompt, DetectionMethod.LLM_JUDGE, model)


def combine_signals(signals: list[HallucinationSignal]) -> HallucinationSignal:
    """Confidence-weighted fusion of multiple detector signals.

    A detector with confidence 0 (unavailable) contributes nothing. The combined
    confidence is the mean of contributing confidences. flagged_segments are
    concatenated. The dominant method is the highest-confidence contributor.
    """
    contributing = [s for s in signals if s.confidence > 0]
    if not contributing:
        return HallucinationSignal(
            method=DetectionMethod.LLM_JUDGE, score=0.0, confidence=0.0,
            reasoning="No detector produced a usable signal",
        )

    weight_sum = sum(s.confidence for s in contributing)
    weighted_score = sum(s.score * s.confidence for s in contributing) / weight_sum
    mean_confidence = weight_sum / len(contributing)

    segments: list[dict[str, str]] = []
    for s in contributing:
        segments.extend(s.flagged_segments)

    dominant = max(contributing, key=lambda s: s.confidence)
    reasoning = "; ".join(f"{s.method.value}={s.score}" for s in contributing)

    return HallucinationSignal(
        method=dominant.method,
        score=round(_clamp(weighted_score), 4),
        confidence=round(_clamp(mean_confidence), 4),
        flagged_segments=segments,
        reasoning=reasoning,
    )
