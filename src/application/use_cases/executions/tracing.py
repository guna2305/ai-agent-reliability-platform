"""Trace recording use cases: add spans, get trace tree, record tool calls."""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from src.application.interfaces.repositories import (
    ExecutionRepository,
    ExecutionTraceRepository,
    ToolCallRepository,
)
from src.domain.entities import ExecutionTrace, ToolCall
from src.domain.exceptions import DomainException
from src.domain.value_objects import TraceType, SpanStatus
from src.infrastructure.ai.cost_calculator import calculate_cost


class TraceNotFoundError(DomainException):
    def __init__(self, trace_id: str) -> None:
        super().__init__(f"Trace span '{trace_id}' not found")


@dataclass(frozen=True)
class OpenSpanDTO:
    """Called when a new span starts (before output is known)."""
    execution_id: str
    trace_type: TraceType
    name: str
    input: dict[str, Any]
    sequence_order: int
    parent_trace_id: str | None = None
    model: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CloseSpanDTO:
    """Called when a span completes successfully."""
    trace_id: str
    output: dict[str, Any]
    input_tokens: int = 0
    output_tokens: int = 0
    provider: str = "ollama"
    model: str = "llama3.2"


@dataclass(frozen=True)
class FailSpanDTO:
    trace_id: str
    error: str


@dataclass(frozen=True)
class RecordToolCallDTO:
    execution_id: str
    tool_name: str
    tool_type: str
    input: dict[str, Any]
    trace_id: str | None = None


class OpenSpanUseCase:
    def __init__(self, trace_repo: ExecutionTraceRepository) -> None:
        self._repo = trace_repo

    async def execute(self, dto: OpenSpanDTO) -> ExecutionTrace:
        span = ExecutionTrace.create(
            execution_id=dto.execution_id,
            trace_type=dto.trace_type,
            name=dto.name,
            input=dto.input,
            sequence_order=dto.sequence_order,
            parent_trace_id=dto.parent_trace_id,
            model=dto.model,
            metadata=dto.metadata,
        )
        return await self._repo.save(span)


class CloseSpanUseCase:
    def __init__(self, trace_repo: ExecutionTraceRepository) -> None:
        self._repo = trace_repo

    async def execute(self, dto: CloseSpanDTO) -> ExecutionTrace:
        span = await self._repo.get_by_id(dto.trace_id)
        if not span:
            raise TraceNotFoundError(dto.trace_id)

        cost = calculate_cost(dto.provider, dto.model, dto.input_tokens, dto.output_tokens)
        span.complete(
            output=dto.output,
            input_tokens=dto.input_tokens or None,
            output_tokens=dto.output_tokens or None,
            cost_usd=cost if cost > 0 else None,
        )
        return await self._repo.update(span)


class FailSpanUseCase:
    def __init__(self, trace_repo: ExecutionTraceRepository) -> None:
        self._repo = trace_repo

    async def execute(self, dto: FailSpanDTO) -> ExecutionTrace:
        span = await self._repo.get_by_id(dto.trace_id)
        if not span:
            raise TraceNotFoundError(dto.trace_id)
        span.fail(dto.error)
        return await self._repo.update(span)


class GetTraceTreeUseCase:
    def __init__(self, trace_repo: ExecutionTraceRepository) -> None:
        self._repo = trace_repo

    async def execute(self, execution_id: str) -> list[dict[str, Any]]:
        """Return spans as a nested tree ordered by sequence_order."""
        spans = await self._repo.list_by_execution(execution_id)
        # Build flat list with children embedded
        by_id: dict[str, dict] = {}
        for span in spans:
            node: dict[str, Any] = {
                "id": span.id,
                "parent_trace_id": span.parent_trace_id,
                "trace_type": span.trace_type.value,
                "name": span.name,
                "status": span.status.value,
                "started_at": span.started_at.isoformat(),
                "ended_at": span.ended_at.isoformat() if span.ended_at else None,
                "duration_ms": span.duration_ms,
                "model": span.model,
                "input_tokens": span.input_tokens,
                "output_tokens": span.output_tokens,
                "cost_usd": str(span.cost_usd) if span.cost_usd else None,
                "error": span.error,
                "sequence_order": span.sequence_order,
                "input": span.input,
                "output": span.output,
                "children": [],
            }
            by_id[span.id] = node

        roots: list[dict] = []
        for node in by_id.values():
            pid = node["parent_trace_id"]
            if pid and pid in by_id:
                by_id[pid]["children"].append(node)
            else:
                roots.append(node)

        roots.sort(key=lambda n: n["sequence_order"])
        return roots


class RecordToolCallUseCase:
    def __init__(self, tool_repo: ToolCallRepository) -> None:
        self._repo = tool_repo

    async def record_start(self, dto: RecordToolCallDTO) -> ToolCall:
        tool_call = ToolCall.create(
            execution_id=dto.execution_id,
            tool_name=dto.tool_name,
            tool_type=dto.tool_type,
            input=dto.input,
            trace_id=dto.trace_id,
        )
        return await self._repo.save(tool_call)

    async def record_complete(self, call_id: str, output: dict[str, Any]) -> ToolCall:
        call = await self._repo.get_by_id(call_id)
        if not call:
            raise DomainException(f"ToolCall '{call_id}' not found")
        call.complete(output)
        return await self._repo.update(call)

    async def record_failure(self, call_id: str, error: str) -> ToolCall:
        call = await self._repo.get_by_id(call_id)
        if not call:
            raise DomainException(f"ToolCall '{call_id}' not found")
        call.fail(error)
        return await self._repo.update(call)


class ListToolCallsUseCase:
    def __init__(self, tool_repo: ToolCallRepository) -> None:
        self._repo = tool_repo

    async def execute(self, execution_id: str) -> list[ToolCall]:
        return await self._repo.list_by_execution(execution_id)
