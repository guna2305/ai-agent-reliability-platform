from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from src.domain.value_objects import TraceType, SpanStatus


@dataclass
class ExecutionTrace:
    id: str
    execution_id: str
    parent_trace_id: str | None
    span_id: str
    trace_type: TraceType
    name: str
    input: dict[str, Any]
    output: dict[str, Any] | None
    started_at: datetime
    ended_at: datetime | None
    duration_ms: int | None
    model: str | None
    input_tokens: int | None
    output_tokens: int | None
    cost_usd: Decimal | None
    error: str | None
    status: SpanStatus
    sequence_order: int
    metadata: dict[str, Any]
    created_at: datetime

    @classmethod
    def create(
        cls,
        execution_id: str,
        trace_type: TraceType,
        name: str,
        input: dict[str, Any],
        sequence_order: int,
        parent_trace_id: str | None = None,
        model: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ExecutionTrace:
        now = datetime.now(timezone.utc)
        return cls(
            id=str(uuid.uuid4()),
            execution_id=execution_id,
            parent_trace_id=parent_trace_id,
            span_id=str(uuid.uuid4()),
            trace_type=trace_type,
            name=name,
            input=input,
            output=None,
            started_at=now,
            ended_at=None,
            duration_ms=None,
            model=model,
            input_tokens=None,
            output_tokens=None,
            cost_usd=None,
            error=None,
            status=SpanStatus.SUCCESS,
            sequence_order=sequence_order,
            metadata=metadata or {},
            created_at=now,
        )

    def complete(
        self,
        output: dict[str, Any],
        input_tokens: int | None = None,
        output_tokens: int | None = None,
        cost_usd: Decimal | None = None,
    ) -> None:
        self.output = output
        self.ended_at = datetime.now(timezone.utc)
        self.duration_ms = int((self.ended_at - self.started_at).total_seconds() * 1000)
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.cost_usd = cost_usd
        self.status = SpanStatus.SUCCESS

    def fail(self, error: str) -> None:
        self.error = error
        self.ended_at = datetime.now(timezone.utc)
        self.duration_ms = int((self.ended_at - self.started_at).total_seconds() * 1000)
        self.status = SpanStatus.ERROR


@dataclass
class ToolCall:
    id: str
    execution_id: str
    trace_id: str | None
    tool_name: str
    tool_type: str
    input: dict[str, Any]
    output: dict[str, Any] | None
    status: str
    error_message: str | None
    duration_ms: int | None
    started_at: datetime
    created_at: datetime

    @classmethod
    def create(
        cls,
        execution_id: str,
        tool_name: str,
        tool_type: str,
        input: dict[str, Any],
        trace_id: str | None = None,
    ) -> ToolCall:
        now = datetime.now(timezone.utc)
        return cls(
            id=str(uuid.uuid4()),
            execution_id=execution_id,
            trace_id=trace_id,
            tool_name=tool_name,
            tool_type=tool_type,
            input=input,
            output=None,
            status="running",
            error_message=None,
            duration_ms=None,
            started_at=now,
            created_at=now,
        )

    def complete(self, output: dict[str, Any]) -> None:
        self.output = output
        self.status = "success"
        ended = datetime.now(timezone.utc)
        self.duration_ms = int((ended - self.started_at).total_seconds() * 1000)

    def fail(self, error_message: str) -> None:
        self.error_message = error_message
        self.status = "error"
        ended = datetime.now(timezone.utc)
        self.duration_ms = int((ended - self.started_at).total_seconds() * 1000)
