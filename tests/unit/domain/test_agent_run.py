import pytest

from src.domain.entities import AgentRun
from src.domain.exceptions import InvalidRunTransitionError
from src.domain.value_objects import RunStatus


def test_create_run_is_pending():
    run = AgentRun.create(agent_id="agent-1")
    assert run.status == RunStatus.PENDING
    assert run.completed_at is None
    assert run.duration_ms is None


def test_run_start_transitions_to_running():
    run = AgentRun.create(agent_id="agent-1")
    run.start()
    assert run.status == RunStatus.RUNNING


def test_run_complete_sets_duration_and_tokens():
    run = AgentRun.create(agent_id="agent-1")
    run.start()
    run.complete(input_tokens=100, output_tokens=200)

    assert run.status == RunStatus.SUCCEEDED
    assert run.completed_at is not None
    assert run.duration_ms is not None and run.duration_ms >= 0
    assert run.input_tokens == 100
    assert run.output_tokens == 200


def test_run_fail_captures_error():
    run = AgentRun.create(agent_id="agent-1")
    run.start()
    run.fail(error_message="timeout connecting to model")

    assert run.status == RunStatus.FAILED
    assert run.error_message == "timeout connecting to model"
    assert run.completed_at is not None


def test_run_timeout():
    run = AgentRun.create(agent_id="agent-1")
    run.start()
    run.timeout()
    assert run.status == RunStatus.TIMED_OUT


def test_run_cannot_complete_from_pending():
    run = AgentRun.create(agent_id="agent-1")
    with pytest.raises(InvalidRunTransitionError):
        run.complete()


def test_run_is_terminal_after_failure():
    run = AgentRun.create(agent_id="agent-1")
    run.start()
    run.fail("err")
    assert run.is_terminal is True


def test_run_not_terminal_while_running():
    run = AgentRun.create(agent_id="agent-1")
    run.start()
    assert run.is_terminal is False
