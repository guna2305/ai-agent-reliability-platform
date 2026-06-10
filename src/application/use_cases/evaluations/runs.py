"""Evaluation run lifecycle use cases."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.application.interfaces.repositories.evaluation_repository import (
    EvaluationResultRepository,
    EvaluationRunRepository,
)
from src.domain.entities import EvaluationResult, EvaluationRun
from src.domain.exceptions import DomainException
from src.domain.value_objects import EvaluationType


class EvaluationRunNotFoundError(DomainException):
    def __init__(self, run_id: str) -> None:
        super().__init__(f"Evaluation run '{run_id}' not found")


@dataclass(frozen=True)
class CreateEvaluationRunDTO:
    org_id: str
    agent_id: str
    created_by: str
    name: str
    eval_type: str
    agent_version_id: str | None = None
    dataset_id: str | None = None
    description: str | None = None
    config: dict[str, Any] = field(default_factory=dict)


class CreateEvaluationRunUseCase:
    def __init__(self, run_repo: EvaluationRunRepository) -> None:
        self._repo = run_repo

    async def execute(self, dto: CreateEvaluationRunDTO) -> EvaluationRun:
        run = EvaluationRun.create(
            org_id=dto.org_id,
            agent_id=dto.agent_id,
            created_by=dto.created_by,
            name=dto.name,
            eval_type=EvaluationType(dto.eval_type),
            agent_version_id=dto.agent_version_id,
            dataset_id=dto.dataset_id,
            description=dto.description,
            config=dto.config,
        )
        return await self._repo.save(run)


class GetEvaluationRunUseCase:
    def __init__(self, run_repo: EvaluationRunRepository) -> None:
        self._repo = run_repo

    async def execute(self, run_id: str, org_id: str) -> EvaluationRun:
        run = await self._repo.get_by_id(run_id)
        if not run or run.org_id != org_id:
            raise EvaluationRunNotFoundError(run_id)
        return run


class ListEvaluationRunsUseCase:
    def __init__(self, run_repo: EvaluationRunRepository) -> None:
        self._repo = run_repo

    async def execute(
        self,
        org_id: str,
        agent_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[EvaluationRun], int]:
        runs = await self._repo.list_by_org(org_id, agent_id, limit, offset)
        total = await self._repo.count_by_org(org_id, agent_id)
        return runs, total


class GetEvaluationResultsUseCase:
    def __init__(self, result_repo: EvaluationResultRepository) -> None:
        self._repo = result_repo

    async def execute(
        self,
        run_id: str,
        passed: bool | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[EvaluationResult], int]:
        results = await self._repo.list_by_run(run_id, passed, limit, offset)
        total = await self._repo.count_by_run(run_id, passed)
        return results, total
