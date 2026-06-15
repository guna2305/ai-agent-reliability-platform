from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.entities import HallucinationReport


class HallucinationReportRepository(ABC):
    @abstractmethod
    async def save(self, report: HallucinationReport) -> HallucinationReport: ...

    @abstractmethod
    async def get_by_id(self, report_id: str) -> HallucinationReport | None: ...

    @abstractmethod
    async def list_by_execution(self, execution_id: str) -> list[HallucinationReport]: ...

    @abstractmethod
    async def update(self, report: HallucinationReport) -> HallucinationReport: ...

    @abstractmethod
    async def list_flagged_by_org(
        self,
        org_id: str,
        min_score: float = 0.7,
        limit: int = 50,
        offset: int = 0,
    ) -> list[HallucinationReport]: ...

    @abstractmethod
    async def count_flagged_by_org(self, org_id: str, min_score: float = 0.7) -> int: ...
