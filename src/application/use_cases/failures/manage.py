"""Failure analytics use cases: record, list, search, resolve, analytics."""
from __future__ import annotations

from dataclasses import dataclass

from src.application.interfaces.repositories import FailureReportRepository
from src.domain.entities import FailureReport
from src.domain.exceptions import DomainException
from src.infrastructure.ai.failure_classifier import FailureSignals, classify_failure


class FailureReportNotFoundError(DomainException):
    def __init__(self, report_id: str) -> None:
        super().__init__(f"Failure report '{report_id}' not found")


@dataclass(frozen=True)
class RecordFailureFromSignalsDTO:
    org_id: str
    execution_id: str
    signals: FailureSignals
    eval_result_id: str | None = None


class RecordFailureUseCase:
    """Classify an execution's failure signals and persist a report if it failed."""

    def __init__(self, repo: FailureReportRepository) -> None:
        self._repo = repo

    async def execute(self, dto: RecordFailureFromSignalsDTO) -> FailureReport | None:
        classification = classify_failure(dto.signals)
        if classification is None:
            return None  # Not a failure — nothing to record

        report = FailureReport.create(
            org_id=dto.org_id,
            execution_id=dto.execution_id,
            failure_type=classification.failure_type,
            severity=classification.severity,
            title=classification.title,
            description=classification.description,
            root_cause=classification.root_cause,
            eval_result_id=dto.eval_result_id,
        )
        return await self._repo.save(report)


class ListFailuresUseCase:
    def __init__(self, repo: FailureReportRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        org_id: str,
        failure_type=None,
        cluster_id: int | None = None,
        is_resolved: bool | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[FailureReport], int]:
        items = await self._repo.list_by_org(
            org_id, failure_type, cluster_id, is_resolved, limit, offset
        )
        total = await self._repo.count_by_org(org_id, failure_type, cluster_id, is_resolved)
        return items, total


class GetFailureUseCase:
    def __init__(self, repo: FailureReportRepository) -> None:
        self._repo = repo

    async def execute(self, report_id: str, org_id: str) -> FailureReport:
        report = await self._repo.get_by_id(report_id, org_id)
        if not report:
            raise FailureReportNotFoundError(report_id)
        return report


class ResolveFailureUseCase:
    def __init__(self, repo: FailureReportRepository) -> None:
        self._repo = repo

    async def execute(self, report_id: str, org_id: str, notes: str) -> FailureReport:
        report = await self._repo.get_by_id(report_id, org_id)
        if not report:
            raise FailureReportNotFoundError(report_id)
        report.resolve(notes)
        return await self._repo.update(report)


class FailureAnalyticsUseCase:
    def __init__(self, repo: FailureReportRepository) -> None:
        self._repo = repo

    async def type_breakdown(self, org_id: str) -> list[dict]:
        return await self._repo.get_type_breakdown(org_id)

    async def cluster_summary(self, org_id: str) -> list[dict]:
        return await self._repo.get_cluster_summary(org_id)
