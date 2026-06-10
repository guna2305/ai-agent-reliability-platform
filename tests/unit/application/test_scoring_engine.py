"""Unit tests for the scoring engine (pure aggregation + ground-truth path)."""
from decimal import Decimal

import pytest

from src.application.use_cases.evaluations import (
    ScoringInput,
    ScoringConfig,
    score_item,
    aggregate_results,
)
from src.domain.entities import EvaluationResult
from src.domain.value_objects import EvaluationType


def _make_result(passed: bool, correctness: float | None = None, relevance: float | None = None):
    return EvaluationResult.create(
        eval_run_id="run-1",
        passed=passed,
        correctness_score=correctness,
        relevance_score=relevance,
    )


def test_aggregate_empty():
    agg = aggregate_results([])
    assert agg["total"] == 0
    assert agg["pass_rate"] == 0.0


def test_aggregate_pass_rate():
    results = [_make_result(True), _make_result(True), _make_result(False)]
    agg = aggregate_results(results)
    assert agg["total"] == 3
    assert agg["passed"] == 2
    assert agg["pass_rate"] == round(2 / 3, 4)


def test_aggregate_mean_metric():
    results = [
        _make_result(True, correctness=1.0),
        _make_result(True, correctness=0.5),
        _make_result(False, correctness=0.0),
    ]
    agg = aggregate_results(results)
    assert agg["correctness"] == round(1.5 / 3, 4)


def test_aggregate_ignores_none_metrics():
    # Only one result has relevance set; mean should be over present values only
    results = [
        _make_result(True, relevance=0.8),
        _make_result(True),  # no relevance
    ]
    agg = aggregate_results(results)
    assert agg["relevance"] == 0.8


@pytest.mark.asyncio
async def test_score_item_ground_truth_pass():
    item = ScoringInput(
        dataset_item_id="item-1",
        execution_id=None,
        question="What is the capital of France?",
        response="Paris",
        expected_output="Paris",
    )
    config = ScoringConfig(
        eval_type=EvaluationType.GROUND_TRUTH,
        pass_threshold=0.6,
        use_semantic=False,  # keep pure, no Ollama
    )
    result = await score_item("run-1", item, config)
    assert result.passed is True
    assert result.correctness_score == Decimal("1.0")
    assert result.dataset_item_id == "item-1"


@pytest.mark.asyncio
async def test_score_item_ground_truth_fail():
    item = ScoringInput(
        dataset_item_id="item-2",
        execution_id=None,
        question="What is 2+2?",
        response="five",
        expected_output="4",
    )
    config = ScoringConfig(
        eval_type=EvaluationType.GROUND_TRUTH,
        pass_threshold=0.6,
        use_semantic=False,
    )
    result = await score_item("run-1", item, config)
    assert result.passed is False
