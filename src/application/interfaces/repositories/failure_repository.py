from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.entities import FailureReport
from src.domain.value_objects import FailureType


class FailureReportRepository(ABC):
    @abstractmethod
    async def save(self, report: FailureReport) -> FailureReport: ...

    @abstractmethod
    async def get_by_id(self, report_id: str, org_id: str) -> FailureReport | None: ...

    @abstractmethod
    async def update(self, report: FailureReport) -> FailureReport: ...

    @abstractmethod
    async def list_by_org(
        self,
        org_id: str,
        failure_type: FailureType | None = None,
        cluster_id: int | None = None,
        is_resolved: bool | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[FailureReport]: ...

    @abstractmethod
    async def count_by_org(
        self,
        org_id: str,
        failure_type: FailureType | None = None,
        cluster_id: int | None = None,
        is_resolved: bool | None = None,
    ) -> int: ...

    @abstractmethod
    async def list_all_for_clustering(self, org_id: str) -> list[FailureReport]:
        """Return all org failure reports that have an embedding (for re-clustering)."""
        ...

    @abstractmethod
    async def get_type_breakdown(self, org_id: str) -> list[dict]:
        """Count of failures grouped by failure_type."""
        ...

    @abstractmethod
    async def get_cluster_summary(self, org_id: str) -> list[dict]:
        """Per-cluster size + dominant failure_type."""
        ...
