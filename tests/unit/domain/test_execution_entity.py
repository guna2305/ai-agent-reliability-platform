from decimal import Decimal

import pytest

from src.domain.entities import Execution
from src.domain.exceptions import InvalidRunTransitionError
from src.domain.value_objects import ExecutionStatus


def test_create_execution_defaults_to_queued():
    ex = Execution.create(org_id="o", agent_id="a", input={"q": "hello"})
    assert ex.status == ExecutionStatus.QUEUED
    assert ex.output is None
    assert ex.is_terminal is False


def test_execution_happy_path():
    ex = Execution.create(org_id="o", agent_id="a", input={"q": "hello"})
    ex.start()
    assert ex.status == ExecutionStatus.RUNNING

    ex.complete(
        output={"answer": "world"},
        input_tokens=100,
        output_tokens=50,
        cost_usd=Decimal("0.0001"),
    )
    assert ex.status == ExecutionStatus.SUCCEEDED
    assert ex.total_tokens == 150
    assert ex.duration_ms is not None and ex.duration_ms >= 0
    assert ex.is_terminal is True


def test_execution_fail():
    ex = Execution.create(org_id="o", agent_id="a", input={})
    ex.start()
    ex.fail("LLM returned error")
    assert ex.status == ExecutionStatus.FAILED
    assert ex.error_message == "LLM returned error"
    assert ex.is_terminal is True


def test_execution_cancel_from_queued():
    ex = Execution.create(org_id="o", agent_id="a", input={})
    ex.cancel()
    assert ex.status == ExecutionStatus.CANCELLED


def test_execution_invalid_transition():
    ex = Execution.create(org_id="o", agent_id="a", input={})
    ex.start()
    ex.complete(output={})
    with pytest.raises(InvalidRunTransitionError):
        ex.fail("too late")
