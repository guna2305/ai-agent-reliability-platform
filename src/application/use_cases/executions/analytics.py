"""Analytics use cases: execution stats, cost summary, performance metrics."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from src.application.interfaces.repositories import ExecutionRepository


@dataclass(frozen=True)
class AnalyticsQuery:
    org_id: str
    days: int = 30
    agent_id: str | None = None


class GetExecutionStatsUseCase:
    def __init__(self, exec_repo: ExecutionRepository) -> None:
        self._repo = exec_repo

    async def execute(self, query: AnalyticsQuery) -> dict[str, Any]:
        end_dt = datetime.now(timezone.utc)
        start_dt = end_dt - timedelta(days=query.days)
        return await self._repo.get_stats(
            org_id=query.org_id,
            start_dt=start_dt,
            end_dt=end_dt,
            agent_id=query.agent_id,
        )


class GetCostSummaryUseCase:
    def __init__(self, exec_repo: ExecutionRepository) -> None:
        self._repo = exec_repo

    async def execute(self, query: AnalyticsQuery) -> dict[str, Any]:
        end_dt = datetime.now(timezone.utc)
        start_dt = end_dt - timedelta(days=query.days)

        by_model = await self._repo.get_cost_by_model(
            org_id=query.org_id,
            start_dt=start_dt,
            end_dt=end_dt,
        )
        daily = await self._repo.get_daily_costs(
            org_id=query.org_id,
            start_dt=start_dt,
            end_dt=end_dt,
        )

        total_cost = sum(r["cost_usd"] for r in by_model)
        total_tokens = sum(r["tokens"] for r in by_model)
        total_executions = sum(r["executions"] for r in by_model)

        return {
            "total_cost_usd": round(total_cost, 6),
            "total_tokens": total_tokens,
            "total_executions": total_executions,
            "avg_cost_per_execution": round(total_cost / total_executions, 6) if total_executions else 0.0,
            "by_model": by_model,
            "daily": daily,
            "period_days": query.days,
        }
