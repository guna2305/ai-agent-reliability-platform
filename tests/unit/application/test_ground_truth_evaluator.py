"""Unit tests for the ground-truth evaluator (pure, no Ollama)."""
import pytest

from src.infrastructure.ai.evaluators.ground_truth import (
    exact_match_score,
    token_f1_score,
    evaluate_ground_truth,
)


def test_exact_match_identical():
    assert exact_match_score("The answer is 42", "the answer is 42") == 1.0


def test_exact_match_normalizes_punctuation():
    assert exact_match_score("Hello, world!", "hello world") == 1.0


def test_exact_match_different():
    assert exact_match_score("cat", "dog") == 0.0


def test_token_f1_perfect_overlap():
    assert token_f1_score("the quick brown fox", "the quick brown fox") == 1.0


def test_token_f1_partial_overlap():
    # expected={the,quick,brown,fox}, actual={the,quick,red,fox}
    # common={the,quick,fox}=3; precision=3/4, recall=3/4, f1=0.75
    score = token_f1_score("the quick brown fox", "the quick red fox")
    assert score == 0.75


def test_token_f1_no_overlap():
    assert token_f1_score("cat dog", "fish bird") == 0.0


def test_token_f1_empty():
    assert token_f1_score("", "something") == 0.0


@pytest.mark.asyncio
async def test_evaluate_ground_truth_exact_match_no_semantic():
    result = await evaluate_ground_truth("Paris", "paris", use_semantic=False)
    assert result.exact_match == 1.0
    assert result.overall == 1.0
    assert result.semantic_similarity is None


@pytest.mark.asyncio
async def test_evaluate_ground_truth_partial_no_semantic():
    result = await evaluate_ground_truth(
        "the capital of France is Paris",
        "Paris is the capital city of France",
        use_semantic=False,
    )
    # No exact match, semantic disabled -> overall == token_f1
    assert result.exact_match == 0.0
    assert result.overall == result.token_f1
    assert 0.0 < result.overall <= 1.0
