"""Unit tests for ExecutionTrace and ToolCall domain entities."""
from decimal import Decimal

import pytest

from src.domain.entities import ExecutionTrace, ToolCall
from src.domain.value_objects import TraceType, SpanStatus


def test_create_trace_span_defaults():
    span = ExecutionTrace.create(
        execution_id="exec-1",
        trace_type=TraceType.LLM_CALL,
        name="Generate response",
        input={"prompt": "hello"},
        sequence_order=1,
    )
    assert span.status == SpanStatus.SUCCESS
    assert span.output is None
    assert span.ended_at is None
    assert span.duration_ms is None
    assert span.parent_trace_id is None


def test_complete_span_sets_output_and_duration():
    span = ExecutionTrace.create(
        execution_id="exec-1",
        trace_type=TraceType.LLM_CALL,
        name="LLM",
        input={},
        sequence_order=0,
    )
    span.complete(
        output={"content": "answer"},
        input_tokens=100,
        output_tokens=50,
        cost_usd=Decimal("0.0001"),
    )
    assert span.output == {"content": "answer"}
    assert span.input_tokens == 100
    assert span.output_tokens == 50
    assert span.cost_usd == Decimal("0.0001")
    assert span.duration_ms is not None and span.duration_ms >= 0
    assert span.status == SpanStatus.SUCCESS


def test_fail_span():
    span = ExecutionTrace.create(
        execution_id="exec-1",
        trace_type=TraceType.TOOL_CALL,
        name="web_search",
        input={},
        sequence_order=2,
    )
    span.fail("Network timeout")
    assert span.status == SpanStatus.ERROR
    assert span.error == "Network timeout"
    assert span.ended_at is not None


def test_tool_call_lifecycle():
    call = ToolCall.create(
        execution_id="exec-1",
        tool_name="search_web",
        tool_type="search",
        input={"query": "AI trends"},
    )
    assert call.status == "running"
    assert call.output is None

    call.complete({"results": ["result1", "result2"]})
    assert call.status == "success"
    assert call.duration_ms is not None and call.duration_ms >= 0

    call2 = ToolCall.create(
        execution_id="exec-1",
        tool_name="run_code",
        tool_type="code",
        input={"code": "print('hi')"},
    )
    call2.fail("Sandbox timeout")
    assert call2.status == "error"
    assert call2.error_message == "Sandbox timeout"
