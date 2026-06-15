from __future__ import annotations

import json

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.interfaces.repositories.failure_repository import FailureReportRepository
from src.domain.entities import FailureReport
from src.domain.value_objects import FailureSeverity, FailureType
from src.infrastructure.database.models.evaluation_model import FailureReportModel


class PostgresFailureReportRepository(FailureReportRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, report: FailureReport) -> FailureReport:
        self._session.add(_to_model(report))
        await self._session.flush()
        return report

    async def get_by_id(self, report_id: str, org_id: str) -> FailureReport | None:
        stmt = select(FailureReportModel).where(
            FailureReportModel.id == report_id, FailureReportModel.org_id == org_id
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return _to_entity(row) if row else None

    async def update(self, report: FailureReport) -> FailureReport:
        row = await self._session.get(FailureReportModel, report.id)
        if row:
            row.cluster_id = report.cluster_id
            row.embedding_vector = (
                json.dumps(report.embedding_vector) if report.embedding_vector else None
            )
            row.is_resolved = report.is_resolved
            row.resolution_notes = report.resolution_notes
            await self._session.flush()
        return report

    async def list_by_org(
        self,
        org_id: str,
        failure_type: FailureType | None = None,
        cluster_id: int | None = None,
        is_resolved: bool | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[FailureReport]:
        stmt = (
            select(FailureReportModel)
            .where(FailureReportModel.org_id == org_id)
            .order_by(FailureReportModel.created_at.desc())
        )
        if failure_type:
            stmt = stmt.where(FailureReportModel.failure_type == failure_type.value)
        if cluster_id is not None:
            stmt = stmt.where(FailureReportModel.cluster_id == cluster_id)
        if is_resolved is not None:
            stmt = stmt.where(FailureReportModel.is_resolved == is_resolved)
        stmt = stmt.limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return [_to_entity(r) for r in result.scalars().all()]

    async def count_by_org(
        self,
        org_id: str,
        failure_type: FailureType | None = None,
        cluster_id: int | None = None,
        is_resolved: bool | None = None,
    ) -> int:
        stmt = select(func.count()).select_from(FailureReportModel).where(
            FailureReportModel.org_id == org_id
        )
        if failure_type:
            stmt = stmt.where(FailureReportModel.failure_type == failure_type.value)
        if cluster_id is not None:
            stmt = stmt.where(FailureReportModel.cluster_id == cluster_id)
        if is_resolved is not None:
            stmt = stmt.where(FailureReportModel.is_resolved == is_resolved)
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def list_all_for_clustering(self, org_id: str) -> list[FailureReport]:
        stmt = (
            select(FailureReportModel)
            .where(
                FailureReportModel.org_id == org_id,
                FailureReportModel.embedding_vector.isnot(None),
            )
            .order_by(FailureReportModel.created_at)
        )
        result = await self._session.execute(stmt)
        return [_to_entity(r) for r in result.scalars().all()]

    async def get_type_breakdown(self, org_id: str) -> list[dict]:
        stmt = (
            select(FailureReportModel.failure_type, func.count().label("count"))
            .where(FailureReportModel.org_id == org_id)
            .group_by(FailureReportModel.failure_type)
            .order_by(func.count().desc())
        )
        result = await self._session.execute(stmt)
        return [{"failure_type": r.failure_type, "count": r.count} for r in result.all()]

    async def get_cluster_summary(self, org_id: str) -> list[dict]:
        stmt = (
            select(
                FailureReportModel.cluster_id,
                func.count().label("size"),
                func.mode().within_group(FailureReportModel.failure_type).label("dominant_type"),
            )
            .where(
                FailureReportModel.org_id == org_id,
                FailureReportModel.cluster_id.isnot(None),
            )
            .group_by(FailureReportModel.cluster_id)
            .order_by(func.count().desc())
        )
        result = await self._session.execute(stmt)
        return [
            {"cluster_id": r.cluster_id, "size": r.size, "dominant_type": r.dominant_type}
            for r in result.all()
        ]


def _to_model(r: FailureReport) -> FailureReportModel:
    return FailureReportModel(
        id=r.id,
        org_id=r.org_id,
        execution_id=r.execution_id,
        eval_result_id=r.eval_result_id,
        failure_type=r.failure_type.value,
        severity=r.severity.value,
        title=r.title,
        description=r.description,
        root_cause=r.root_cause,
        embedding_vector=json.dumps(r.embedding_vector) if r.embedding_vector else None,
        cluster_id=r.cluster_id,
        is_resolved=r.is_resolved,
        resolution_notes=r.resolution_notes,
        created_at=r.created_at,
    )


def _to_entity(m: FailureReportModel) -> FailureReport:
    return FailureReport(
        id=m.id,
        org_id=m.org_id,
        execution_id=m.execution_id,
        eval_result_id=m.eval_result_id,
        failure_type=FailureType(m.failure_type),
        severity=FailureSeverity(m.severity),
        title=m.title,
        description=m.description,
        root_cause=m.root_cause,
        embedding_vector=json.loads(m.embedding_vector) if m.embedding_vector else None,
        cluster_id=m.cluster_id,
        is_resolved=m.is_resolved,
        resolution_notes=m.resolution_notes,
        created_at=m.created_at,
    )
