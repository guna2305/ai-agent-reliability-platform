"""Dataset management use cases."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.application.interfaces.repositories.evaluation_repository import (
    DatasetRepository,
    DatasetItemRepository,
)
from src.domain.entities import Dataset, DatasetItem
from src.domain.exceptions import DomainException


class DatasetNotFoundError(DomainException):
    def __init__(self, dataset_id: str) -> None:
        super().__init__(f"Dataset '{dataset_id}' not found")


@dataclass(frozen=True)
class CreateDatasetDTO:
    org_id: str
    name: str
    created_by: str
    dataset_type: str = "golden"
    description: str | None = None


@dataclass(frozen=True)
class DatasetItemInput:
    input: dict[str, Any]
    expected_output: dict[str, Any] | None = None
    context: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class CreateDatasetUseCase:
    def __init__(self, dataset_repo: DatasetRepository) -> None:
        self._repo = dataset_repo

    async def execute(self, dto: CreateDatasetDTO) -> Dataset:
        dataset = Dataset.create(
            org_id=dto.org_id,
            name=dto.name,
            created_by=dto.created_by,
            dataset_type=dto.dataset_type,
            description=dto.description,
        )
        return await self._repo.save(dataset)


class ListDatasetsUseCase:
    def __init__(self, dataset_repo: DatasetRepository) -> None:
        self._repo = dataset_repo

    async def execute(self, org_id: str, limit: int = 50, offset: int = 0) -> tuple[list[Dataset], int]:
        datasets = await self._repo.list_by_org(org_id, limit, offset)
        total = await self._repo.count_by_org(org_id)
        return datasets, total


class GetDatasetUseCase:
    def __init__(self, dataset_repo: DatasetRepository) -> None:
        self._repo = dataset_repo

    async def execute(self, dataset_id: str, org_id: str) -> Dataset:
        dataset = await self._repo.get_by_id(dataset_id)
        if not dataset or dataset.org_id != org_id:
            raise DatasetNotFoundError(dataset_id)
        return dataset


class DeleteDatasetUseCase:
    def __init__(self, dataset_repo: DatasetRepository) -> None:
        self._repo = dataset_repo

    async def execute(self, dataset_id: str, org_id: str) -> None:
        deleted = await self._repo.delete(dataset_id, org_id)
        if not deleted:
            raise DatasetNotFoundError(dataset_id)


class AddDatasetItemsUseCase:
    def __init__(
        self,
        dataset_repo: DatasetRepository,
        item_repo: DatasetItemRepository,
    ) -> None:
        self._dataset_repo = dataset_repo
        self._item_repo = item_repo

    async def execute(
        self,
        dataset_id: str,
        org_id: str,
        items: list[DatasetItemInput],
    ) -> list[DatasetItem]:
        dataset = await self._dataset_repo.get_by_id(dataset_id)
        if not dataset or dataset.org_id != org_id:
            raise DatasetNotFoundError(dataset_id)

        entities = [
            DatasetItem.create(
                dataset_id=dataset_id,
                input=item.input,
                expected_output=item.expected_output,
                context=item.context,
                metadata=item.metadata,
            )
            for item in items
        ]
        return await self._item_repo.save_bulk(entities)


class ListDatasetItemsUseCase:
    def __init__(self, item_repo: DatasetItemRepository) -> None:
        self._repo = item_repo

    async def execute(self, dataset_id: str, limit: int = 100, offset: int = 0) -> tuple[list[DatasetItem], int]:
        items = await self._repo.list_by_dataset(dataset_id, limit, offset)
        total = await self._repo.count_by_dataset(dataset_id)
        return items, total
