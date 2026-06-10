"""RAG evaluation metrics — all powered by Ollama (no paid APIs).

Implements RAGAS-inspired metrics:
- Context Precision:  Are the retrieved chunks relevant to the question?
- Context Recall:     Does the context cover all facts in the expected answer?
- Faithfulness:       Is the response grounded in the context (no hallucination)?
- Answer Relevancy:   Does the answer address the question?
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass

import httpx

from src.infrastructure.config.settings import get_settings

logger = logging.getLogger(__name__)

_SYSTEM = (
    "You are an expert evaluator for retrieval-augmented generation (RAG) systems. "
    "Respond only with valid JSON."
)

_CONTEXT_PRECISION_TMPL = """\
Given a question and a list of retrieved context passages, determine what fraction
of the retrieved passages are actually relevant to answering the question.

Question: {question}
Retrieved context:
{context_chunks}

For each passage, mark it as relevant (true) or irrelevant (false).
Then compute precision = relevant_count / total_count.

Respond with JSON:
{{"relevant_passages": [true/false, ...], "precision": <0.0-1.0>, "reasoning": "<one sentence>"}}"""

_CONTEXT_RECALL_TMPL = """\
Determine what fraction of the key facts in the expected answer are covered by the context.

Expected Answer: {expected}
Retrieved context: {context}

List each key fact from the expected answer and whether it is supported by the context.
Compute recall = supported_facts / total_facts.

Respond with JSON:
{{"supported_facts": <int>, "total_facts": <int>, "recall": <0.0-1.0>, "reasoning": "<one sentence>"}}"""

_FAITHFULNESS_TMPL = """\
Evaluate whether every claim in the AI response is directly supported by the context.

Context: {context}
AI Response: {response}

List the main claims in the response and mark each as supported or unsupported.
Compute faithfulness = supported_claims / total_claims.

Respond with JSON:
{{"supported_claims": <int>, "total_claims": <int>, "faithfulness": <0.0-1.0>, "reasoning": "<one sentence>"}}"""

_ANSWER_RELEVANCY_TMPL = """\
Evaluate whether the AI response directly answers the question asked.

Question: {question}
AI Response: {response}

Consider:
- Does it address what was asked?
- Is there unnecessary information that obscures the answer?
- Is it complete?

Respond with JSON:
{{"relevancy": <0.0-1.0>, "reasoning": "<one sentence>"}}"""


@dataclass
class RAGScores:
    context_precision: float | None
    context_recall: float | None
    faithfulness: float | None
    answer_relevancy: float | None


async def _llm_eval(prompt: str, model: str | None = None) -> dict | None:
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
            return json.loads(resp.json()["message"]["content"])
    except Exception as e:
        logger.warning("RAG evaluator LLM call failed", extra={"error": str(e)})
        return None


async def score_context_precision(
    question: str,
    context_chunks: list[str],
    model: str | None = None,
) -> float | None:
    if not context_chunks:
        return None
    chunks_text = "\n".join(f"[{i+1}] {c}" for i, c in enumerate(context_chunks))
    prompt = _CONTEXT_PRECISION_TMPL.format(question=question, context_chunks=chunks_text)
    data = await _llm_eval(prompt, model)
    if data and "precision" in data:
        return round(max(0.0, min(1.0, float(data["precision"]))), 4)
    return None


async def score_context_recall(
    expected: str,
    context: str,
    model: str | None = None,
) -> float | None:
    if not expected or not context:
        return None
    prompt = _CONTEXT_RECALL_TMPL.format(expected=expected, context=context)
    data = await _llm_eval(prompt, model)
    if data and "recall" in data:
        return round(max(0.0, min(1.0, float(data["recall"]))), 4)
    return None


async def score_faithfulness(
    context: str,
    response: str,
    model: str | None = None,
) -> float | None:
    if not context:
        return None
    prompt = _FAITHFULNESS_TMPL.format(context=context, response=response)
    data = await _llm_eval(prompt, model)
    if data and "faithfulness" in data:
        return round(max(0.0, min(1.0, float(data["faithfulness"]))), 4)
    return None


async def score_answer_relevancy(
    question: str,
    response: str,
    model: str | None = None,
) -> float | None:
    prompt = _ANSWER_RELEVANCY_TMPL.format(question=question, response=response)
    data = await _llm_eval(prompt, model)
    if data and "relevancy" in data:
        return round(max(0.0, min(1.0, float(data["relevancy"]))), 4)
    return None


async def evaluate_rag(
    question: str,
    response: str,
    context_chunks: list[str],
    expected: str | None = None,
    model: str | None = None,
) -> RAGScores:
    context_text = "\n\n".join(context_chunks)
    cp = await score_context_precision(question, context_chunks, model)
    cr = await score_context_recall(expected, context_text, model) if expected else None
    faith = await score_faithfulness(context_text, response, model)
    ar = await score_answer_relevancy(question, response, model)
    return RAGScores(
        context_precision=cp,
        context_recall=cr,
        faithfulness=faith,
        answer_relevancy=ar,
    )
