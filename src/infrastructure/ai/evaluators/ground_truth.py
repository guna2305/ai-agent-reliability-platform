"""Ground truth evaluator.

Compares AI responses against expected answers using:
- Exact match
- Token-level F1 (SQUAD-style)
- Semantic similarity (Ollama embeddings cosine similarity)
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Any


@dataclass
class GroundTruthScore:
    exact_match: float
    token_f1: float
    semantic_similarity: float | None
    overall: float
    reasoning: str


def _normalize(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def _token_set(text: str) -> set[str]:
    return set(_normalize(text).split())


def exact_match_score(expected: str, actual: str) -> float:
    return 1.0 if _normalize(expected) == _normalize(actual) else 0.0


def token_f1_score(expected: str, actual: str) -> float:
    exp_tokens = _token_set(expected)
    act_tokens = _token_set(actual)
    if not exp_tokens or not act_tokens:
        return 0.0
    common = exp_tokens & act_tokens
    if not common:
        return 0.0
    precision = len(common) / len(act_tokens)
    recall = len(common) / len(exp_tokens)
    return round(2 * precision * recall / (precision + recall), 4)


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return round(dot / (mag_a * mag_b), 4)


async def semantic_similarity_score(expected: str, actual: str) -> float | None:
    """Cosine similarity between Ollama embedding vectors. Returns None if Ollama unavailable."""
    try:
        from src.infrastructure.ai.providers import embed_ollama
        emb_exp = await embed_ollama(expected)
        emb_act = await embed_ollama(actual)
        return _cosine_similarity(emb_exp, emb_act)
    except Exception:
        return None


async def evaluate_ground_truth(
    expected: str,
    actual: str,
    use_semantic: bool = True,
) -> GroundTruthScore:
    em = exact_match_score(expected, actual)
    f1 = token_f1_score(expected, actual)
    sem = await semantic_similarity_score(expected, actual) if use_semantic else None

    # Weight: exact_match has highest priority, then semantic, then F1
    if em == 1.0:
        overall = 1.0
    elif sem is not None:
        overall = round((f1 * 0.3 + sem * 0.7), 4)
    else:
        overall = f1

    reasoning = (
        f"Exact match: {em}, Token F1: {f1}"
        + (f", Semantic similarity: {sem}" if sem is not None else "")
    )
    return GroundTruthScore(
        exact_match=em,
        token_f1=f1,
        semantic_similarity=sem,
        overall=overall,
        reasoning=reasoning,
    )
