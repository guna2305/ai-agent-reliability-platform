"""Unit tests for the rule-based failure classifier."""
from decimal import Decimal

from src.domain.value_objects import ExecutionStatus, FailureSeverity, FailureType
from src.infrastructure.ai.failure_classifier import FailureSignals, classify_failure


def test_healthy_execution_returns_none():
    signals = FailureSignals(status=ExecutionStatus.SUCCEEDED)
    assert classify_failure(signals) is None


def test_hallucination_takes_priority():
    # Even a "succeeded" run is a failure if hallucinated
    signals = FailureSignals(status=ExecutionStatus.SUCCEEDED, hallucination_score=0.85)
    result = classify_failure(signals)
    assert result is not None
    assert result.failure_type == FailureType.HALLUCINATION
    assert result.severity == FailureSeverity.HIGH


def test_timeout_classification():
    signals = FailureSignals(status=ExecutionStatus.TIMED_OUT, duration_ms=30000)
    result = classify_failure(signals)
    assert result.failure_type == FailureType.TIMEOUT


def test_error_keyword_retrieval():
    signals = FailureSignals(
        status=ExecutionStatus.FAILED,
        error_message="Retrieval returned no documents for the query",
    )
    result = classify_failure(signals)
    assert result.failure_type == FailureType.RETRIEVAL
    assert result.severity == FailureSeverity.HIGH


def test_error_keyword_output_parse():
    signals = FailureSignals(
        status=ExecutionStatus.FAILED,
        error_message="Failed to parse JSON response from model",
    )
    result = classify_failure(signals)
    assert result.failure_type == FailureType.OUTPUT


def test_tool_call_errors():
    signals = FailureSignals(
        status=ExecutionStatus.SUCCEEDED,
        tool_call_errors=["search_web returned 500", "db_query timed out"],
    )
    result = classify_failure(signals)
    assert result.failure_type == FailureType.TOOL


def test_empty_output():
    signals = FailureSignals(status=ExecutionStatus.SUCCEEDED, empty_output=True)
    result = classify_failure(signals)
    assert result.failure_type == FailureType.OUTPUT


def test_cost_overrun():
    signals = FailureSignals(
        status=ExecutionStatus.SUCCEEDED,
        total_cost_usd=Decimal("2.50"),
        cost_threshold_usd=1.0,
    )
    result = classify_failure(signals)
    assert result.failure_type == FailureType.COST
    assert result.severity == FailureSeverity.LOW


def test_generic_failure_no_message():
    signals = FailureSignals(status=ExecutionStatus.FAILED)
    result = classify_failure(signals)
    assert result.failure_type == FailureType.UNKNOWN


def test_unmatched_error_is_unknown_medium():
    signals = FailureSignals(
        status=ExecutionStatus.FAILED,
        error_message="Something weird happened that matches no keyword",
    )
    result = classify_failure(signals)
    assert result.failure_type == FailureType.UNKNOWN
    assert result.severity == FailureSeverity.MEDIUM
