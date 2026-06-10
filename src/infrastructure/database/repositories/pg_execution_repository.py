from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.interfaces.repositories import (
    ExecutionRepository,
    ExecutionTraceRepository,
    ToolCallRepository,
)
from src.domain.entities import Execution, ExecutionTrace, ToolCall
from src.domain.value_objects import ExecutionStatus, TriggerType, TraceType, SpanStatus
from src.infrastructure.database.models.execution_model import (
    ExecutionModel,
    ExecutionTraceModel,
    ToolCallModel,
)


class PostgresExecutionRepository(ExecutionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, execution: Execution) -> Execution:
        self._session.add(_exec_to_model(execution))
        await self._session.flush()
        return execution

    async def get_by_id(self, exec_id: str) -> Execution | None:
        row = await self._session.get(ExecutionModel, exec_id)
        return _model_to_exec(row) if row else None

    async def update(self, execution: Execution) -> Execution:
        row = await self._session.get(ExecutionModel, execution.id)
        if row:
            row.status = execution.status.value
            row.output_ = execution.output
            row.error_message = execution.error_message
            row.completed_at = execution.completed_at
            row.duration_ms = execution.duration_ms
            row.total_tokens = execution.total_tokens
            row.input_tokens = execution.input_tokens
            row.output_tokens = execution.output_tokens
            row.total_cost_usd = execution.total_cost_usd
            row.model_provider = execution.model_provider
            row.model_name = execution.model_name
            await self._session.flush()
        return execution

    async def list_by_org(
        self,
        org_id: str,
        agent_id: str | None = None,
        status: ExecutionStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Execution]:
        stmt = (
            select(ExecutionModel)
            .where(ExecutionModel.org_id == org_id)
            .order_by(ExecutionModel.started_at.desc())
        )
        if agent_id:
            stmt = stmt.where(ExecutionModel.agent_id == agent_id)
        if status:
            stmt = stmt.where(ExecutionModel.status == status.value)
        stmt = stmt.limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return [_model_to_exec(r) for r in result.scalars().all()]

    async def count_by_org(
        self,
        org_id: str,
        agent_id: str | None = None,
        status: ExecutionStatus | None = None,
    ) -> int:
        stmt = select(func.count()).select_from(ExecutionModel).where(
            ExecutionModel.org_id == org_id
        )
        if agent_id:
            stmt = stmt.where(ExecutionModel.agent_id == agent_id)
        if status:
            stmt = stmt.where(ExecutionModel.status == status.value)
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def get_stats(
        self,
        org_id: str,
        start_dt: datetime,
        end_dt: datetime,
        agent_id: str | None = None,
    ) -> dict:
        where = [
            ExecutionModel.org_id == org_id,
            ExecutionModel.started_at >= start_dt,
            ExecutionModel.started_at < end_dt,
        ]
        if agent_id:
            where.append(ExecutionModel.agent_id == agent_id)

        stmt = select(
            func.count().label("total"),
            func.count().filter(ExecutionModel.status == "succeeded").label("succeeded"),
            func.count().filter(ExecutionModel.status == "failed").label("failed"),
            func.avg(ExecutionModel.duration_ms).label("avg_duration_ms"),
            func.sum(ExecutionModel.total_tokens).label("total_tokens"),
            func.sum(ExecutionModel.total_cost_usd).label("total_cost_usd"),
        ).select_from(ExecutionModel).where(*where)

        result = await self._session.execute(stmt)
        row = result.one()
        total = row.total or 0
        return {
            "total": total,
            "succeeded": row.succeeded or 0,
            "failed": row.failed or 0,
            "success_rate": round((row.succeeded or 0) / total * 100, 2) if total else 0.0,
            "avg_duration_ms": round(float(row.avg_duration_ms or 0), 2),
            "total_tokens": row.total_tokens or 0,
            "total_cost_usd": float(row.total_cost_usd or 0),
        }

    async def get_cost_by_model(
        self,
        org_id: str,
        start_dt: datetime,
        end_dt: datetime,
    ) -> list[dict]:
        stmt = (
            select(
                ExecutionModel.model_provider,
                ExecutionModel.model_name,
                func.sum(ExecutionModel.total_cost_usd).label("cost_usd"),
                func.sum(ExecutionModel.total_tokens).label("tokens"),
                func.count().label("executions"),
            )
            .where(
                ExecutionModel.org_id == org_id,
                ExecutionModel.started_at >= start_dt,
                ExecutionModel.started_at < end_dt,
                ExecutionModel.model_name.isnot(None),
            )
            .group_by(ExecutionModel.model_provider, ExecutionModel.model_name)
            .order_by(func.sum(ExecutionModel.total_cost_usd).desc())
        )
        result = await self._session.execute(stmt)
        return [
            {
                "provider": r.model_provider,
                "model": r.model_name,
                "cost_usd": float(r.cost_usd or 0),
                "tokens": r.tokens or 0,
                "executions": r.executions,
            }
            for r in result.all()
        ]

    async def get_daily_costs(
        self,
        org_id: str,
        start_dt: datetime,
        end_dt: datetime,
    ) -> list[dict]:
        stmt = text("""
            SELECT
                DATE_TRUNC('day', started_at AT TIME ZONE 'UTC') AS day,
                COALESCE(SUM(total_cost_usd), 0)  AS cost_usd,
                COALESCE(SUM(total_tokens), 0)     AS tokens,
                COUNT(*)                           AS executions,
                COUNT(*) FILTER (WHERE status = 'succeeded') AS succeeded,
                COUNT(*) FILTER (WHERE status = 'failed')    AS failed
            FROM executions
            WHERE org_id = :org_id
              AND started_at >= :start_dt
              AND started_at <  :end_dt
            GROUP BY 1
            ORDER BY 1
        """)
        result = await self._session.execute(
            stmt, {"org_id": org_id, "start_dt": start_dt, "end_dt": end_dt}
        )
        return [
            {
                "date": str(r.day.date()),
                "cost_usd": float(r.cost_usd),
                "tokens": int(r.tokens),
                "executions": r.executions,
                "succeeded": r.succeeded,
                "failed": r.failed,
            }
            for r in result.all()
        ]


class PostgresExecutionTraceRepository(ExecutionTraceRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, trace: ExecutionTrace) -> ExecutionTrace:
        self._session.add(_trace_to_model(trace))
        await self._session.flush()
        return trace

    async def get_by_id(self, trace_id: str) -> ExecutionTrace | None:
        row = await self._session.get(ExecutionTraceModel, trace_id)
        return _model_to_trace(row) if row else None

    async def list_by_execution(self, exec_id: str) -> list[ExecutionTrace]:
        stmt = (
            select(ExecutionTraceModel)
            .where(ExecutionTraceModel.execution_id == exec_id)
            .order_by(ExecutionTraceModel.sequence_order)
        )
        result = await self._session.execute(stmt)
        return [_model_to_trace(r) for r in result.scalars().all()]

    async def update(self, trace: ExecutionTrace) -> ExecutionTrace:
        row = await self._session.get(ExecutionTraceModel, trace.id)
        if row:
            row.output_ = trace.output
            row.ended_at = trace.ended_at
            row.duration_ms = trace.duration_ms
            row.input_tokens = trace.input_tokens
            row.output_tokens = trace.output_tokens
            row.cost_usd = trace.cost_usd
            row.error = trace.error
            row.status = trace.status.value
            await self._session.flush()
        return trace


class PostgresToolCallRepository(ToolCallRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, tool_call: ToolCall) -> ToolCall:
        self._session.add(_tool_to_model(tool_call))
        await self._session.flush()
        return tool_call

    async def get_by_id(self, call_id: str) -> ToolCall | None:
        row = await self._session.get(ToolCallModel, call_id)
        return _model_to_tool(row) if row else None

    async def list_by_execution(self, exec_id: str) -> list[ToolCall]:
        stmt = (
            select(ToolCallModel)
            .where(ToolCallModel.execution_id == exec_id)
            .order_by(ToolCallModel.started_at)
        )
        result = await self._session.execute(stmt)
        return [_model_to_tool(r) for r in result.scalars().all()]

    async def update(self, tool_call: ToolCall) -> ToolCall:
        row = await self._session.get(ToolCallModel, tool_call.id)
        if row:
            row.output_ = tool_call.output
            row.status = tool_call.status
            row.error_message = tool_call.error_message
            row.duration_ms = tool_call.duration_ms
            await self._session.flush()
        return tool_call


# ── Mapping helpers ───────────────────────────────────────────────────────────

def _exec_to_model(e: Execution) -> ExecutionModel:
    return ExecutionModel(
        id=e.id, org_id=e.org_id, agent_id=e.agent_id,
        agent_version_id=e.agent_version_id,
        status=e.status.value, trigger_type=e.trigger_type.value,
        input_=e.input, output_=e.output, error_message=e.error_message,
        started_at=e.started_at, completed_at=e.completed_at, duration_ms=e.duration_ms,
        total_tokens=e.total_tokens, input_tokens=e.input_tokens, output_tokens=e.output_tokens,
        total_cost_usd=e.total_cost_usd, model_provider=e.model_provider,
        model_name=e.model_name, tags=e.tags, metadata_=e.metadata,
        initiated_by=e.initiated_by, created_at=e.created_at,
    )


def _model_to_exec(m: ExecutionModel) -> Execution:
    return Execution(
        id=m.id, org_id=m.org_id, agent_id=m.agent_id,
        agent_version_id=m.agent_version_id,
        status=ExecutionStatus(m.status), trigger_type=TriggerType(m.trigger_type),
        input=m.input_ or {}, output=m.output_,
        error_message=m.error_message,
        started_at=m.started_at, completed_at=m.completed_at, duration_ms=m.duration_ms,
        total_tokens=m.total_tokens, input_tokens=m.input_tokens, output_tokens=m.output_tokens,
        total_cost_usd=m.total_cost_usd, model_provider=m.model_provider,
        model_name=m.model_name, tags=m.tags or [], metadata=m.metadata_ or {},
        initiated_by=m.initiated_by, created_at=m.created_at,
    )


def _trace_to_model(t: ExecutionTrace) -> ExecutionTraceModel:
    return ExecutionTraceModel(
        id=t.id, execution_id=t.execution_id, parent_trace_id=t.parent_trace_id,
        span_id=t.span_id, trace_type=t.trace_type.value, name=t.name,
        input_=t.input, output_=t.output,
        started_at=t.started_at, ended_at=t.ended_at, duration_ms=t.duration_ms,
        model=t.model, input_tokens=t.input_tokens, output_tokens=t.output_tokens,
        cost_usd=t.cost_usd, error=t.error, status=t.status.value,
        sequence_order=t.sequence_order, metadata_=t.metadata, created_at=t.created_at,
    )


def _model_to_trace(m: ExecutionTraceModel) -> ExecutionTrace:
    return ExecutionTrace(
        id=m.id, execution_id=m.execution_id, parent_trace_id=m.parent_trace_id,
        span_id=m.span_id, trace_type=TraceType(m.trace_type), name=m.name,
        input=m.input_ or {}, output=m.output_,
        started_at=m.started_at, ended_at=m.ended_at, duration_ms=m.duration_ms,
        model=m.model, input_tokens=m.input_tokens, output_tokens=m.output_tokens,
        cost_usd=m.cost_usd, error=m.error, status=SpanStatus(m.status),
        sequence_order=m.sequence_order, metadata=m.metadata_ or {}, created_at=m.created_at,
    )


def _tool_to_model(t: ToolCall) -> ToolCallModel:
    return ToolCallModel(
        id=t.id, execution_id=t.execution_id, trace_id=t.trace_id,
        tool_name=t.tool_name, tool_type=t.tool_type,
        input_=t.input, output_=t.output,
        status=t.status, error_message=t.error_message, duration_ms=t.duration_ms,
        started_at=t.started_at, created_at=t.created_at,
    )


def _model_to_tool(m: ToolCallModel) -> ToolCall:
    return ToolCall(
        id=m.id, execution_id=m.execution_id, trace_id=m.trace_id,
        tool_name=m.tool_name, tool_type=m.tool_type,
        input=m.input_ or {}, output=m.output_,
        status=m.status, error_message=m.error_message, duration_ms=m.duration_ms,
        started_at=m.started_at, created_at=m.created_at,
    )
