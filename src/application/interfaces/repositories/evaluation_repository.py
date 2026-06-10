from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.entities import Dataset, DatasetItem, EvaluationResult, EvaluationRun


class DatasetRepository(ABC):
    @abstractmethod
    async def save(self, dataset: Dataset) -> Dataset: ...

    @abstractmethod
    async def get_by_id(self, dataset_id: str) -> Dataset | None: ...

    @abstractmethod
    async def list_by_org(self, org_id: str, limit: int = 50, offset: int = 0) -> list[Dataset]: ...

    @abstractmethod
    async def count_by_org(self, org_id: str) -> int: ...

    @abstractmethod
    async def delete(self, dataset_id: str, org_id: str) -> bool: ...


class DatasetItemRepository(ABC):
    @abstractmethod
    async def save(self, item: DatasetItem) -> DatasetItem: ...

    @abstractmethod
    async def save_bulk(self, items: list[DatasetItem]) -> list[DatasetItem]: ...

    @abstractmethod
    async def get_by_id(self, item_id: str) -> DatasetItem | None: ...

    @abstractmethod
    async def list_by_dataset(
        self, dataset_id: str, limit: int = 100, offset: int = 0
    ) -> list[DatasetItem]: ...

    @abstractmethod
    async def count_by_dataset(self, dataset_id: str) -> int: ...


class EvaluationRunRepository(ABC):
    @abstractmethod
    async def save(self, run: EvaluationRun) -> EvaluationRun: ...

    @abstractmethod
    async def get_by_id(self, run_id: str) -> EvaluationRun | None: ...

    @abstractmethod
    async def update(self, run: EvaluationRun) -> EvaluationRun: ...

    @abstractmethod
    async def list_by_org(
        self,
        org_id: str,
        agent_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[EvaluationRun]: ...

    @abstractmethod
    async def count_by_org(self, org_id: str, agent_id: str | None = None) -> int: ...


class EvaluationResultRepository(ABC):
    @abstractmethod
    async def save(self, result: EvaluationResult) -> EvaluationResult: ...

    @abstractmethod
    async def save_bulk(self, results: list[EvaluationResult]) -> None: ...

    @abstractmethod
    async def list_by_run(
        self,
        run_id: str,
        passed: bool | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[EvaluationResult]: ...

    @abstractmethod
    async def count_by_run(self, run_id: str, passed: bool | None = None) -> int: ...

    @abstractmethod
    async def get_aggregate_scores(self, run_id: str) -> dict: ...
