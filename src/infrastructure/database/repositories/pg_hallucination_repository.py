from __future__ import annotations

from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.interfaces.repositories.hallucination_repository import (
    HallucinationReportRepository,
)
from src.domain.entities import HallucinationReport
from src.domain.value_objects import DetectionMethod
from src.infrastructure.database.models.evaluation_model import HallucinationReportModel
from src.infrastructure.database.models.execution_model import ExecutionModel


class PostgresHallucinationReportRepository(HallucinationReportRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, report: HallucinationReport) -> HallucinationReport:
        self._session.add(_to_model(report))
        await self._session.flush()
        return report

    async def get_by_id(self, report_id: str) -> HallucinationReport | None:
        row = await self._session.get(HallucinationReportModel, report_id)
        return _to_entity(row) if row else None

    async def list_by_execution(self, execution_id: str) -> list[HallucinationReport]:
        stmt = (
            select(HallucinationReportModel)
            .where(HallucinationReportModel.execution_id == execution_id)
            .order_by(HallucinationReportModel.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return [_to_entity(r) for r in result.scalars().all()]

    async def update(self, report: HallucinationReport) -> HallucinationReport:
        row = await self._session.get(HallucinationReportModel, report.id)
        if row:
            row.is_confirmed = report.is_confirmed
            await self._session.flush()
        return report

    async def list_flagged_by_org(
        self,
        org_id: str,
        min_score: float = 0.7,
        limit: int = 50,
        offset: int = 0,
    ) -> list[HallucinationReport]:
        # Join to executions to scope by org
        stmt = (
            select(HallucinationReportModel)
            .join(ExecutionModel, ExecutionModel.id == HallucinationReportModel.execution_id)
            .where(
                ExecutionModel.org_id == org_id,
                HallucinationReportModel.hallucination_score >= Decimal(str(min_score)),
            )
            .order_by(HallucinationReportModel.hallucination_score.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return [_to_entity(r) for r in result.scalars().all()]

    async def count_flagged_by_org(self, org_id: str, min_score: float = 0.7) -> int:
        stmt = (
            select(func.count())
            .select_from(HallucinationReportModel)
            .join(ExecutionModel, ExecutionModel.id == HallucinationReportModel.execution_id)
            .where(
                ExecutionModel.org_id == org_id,
                HallucinationReportModel.hallucination_score >= Decimal(str(min_score)),
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()


def _to_model(r: HallucinationReport) -> HallucinationReportModel:
    return HallucinationReportModel(
        id=r.id,
        execution_id=r.execution_id,
        eval_result_id=r.eval_result_id,
        hallucination_score=r.hallucination_score,
        confidence=r.confidence,
        detection_method=r.detection_method.value,
        flagged_segments=r.flagged_segments,
        reasoning=r.reasoning,
        is_confirmed=r.is_confirmed,
        created_at=r.created_at,
    )


def _to_entity(m: HallucinationReportModel) -> HallucinationReport:
    return HallucinationReport(
        id=m.id,
        execution_id=m.execution_id,
        eval_result_id=m.eval_result_id,
        hallucination_score=m.hallucination_score,
        confidence=m.confidence,
        detection_method=DetectionMethod(m.detection_method),
        flagged_segments=m.flagged_segments or [],
        reasoning=m.reasoning,
        is_confirmed=m.is_confirmed,
        created_at=m.created_at,
    )
