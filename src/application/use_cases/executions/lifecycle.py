"""Execution lifecycle use cases: create, start, complete, fail, cancel, get, list."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from src.application.interfaces.repositories import (
    ExecutionRepository,
    AgentV2Repository,
)
from src.domain.entities import Execution
from src.domain.exceptions import DomainException
from src.domain.value_objects import ExecutionStatus, TriggerType
from src.infrastructure.ai.cost_calculator import calculate_cost


class ExecutionNotFoundError(DomainException):
    def __init__(self, exec_id: str) -> None:
        super().__init__(f"Execution '{exec_id}' not found")


class ExecutionAccessDeniedError(DomainException):
    def __init__(self) -> None:
        super().__init__("Access denied to this execution")


@dataclass(frozen=True)
class CreateExecutionDTO:
    org_id: str
    agent_id: str
    input: dict[str, Any]
    initiated_by: str | None = None
    agent_version_id: str | None = None
    trigger_type: TriggerType = TriggerType.API
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CompleteExecutionDTO:
    exec_id: str
    org_id: str
    output: dict[str, Any]
    input_tokens: int = 0
    output_tokens: int = 0
    provider: str = "ollama"
    model: str = "llama3.2"


@dataclass(frozen=True)
class FailExecutionDTO:
    exec_id: str
    org_id: str
    error_message: str


@dataclass(frozen=True)
class ListExecutionsQuery:
    org_id: str
    agent_id: str | None = None
    status: ExecutionStatus | None = None
    limit: int = 50
    offset: int = 0


class CreateExecutionUseCase:
    def __init__(self, exec_repo: ExecutionRepository) -> None:
        self._repo = exec_repo

    async def execute(self, dto: CreateExecutionDTO) -> Execution:
        execution = Execution.create(
            org_id=dto.org_id,
            agent_id=dto.agent_id,
            input=dto.input,
            agent_version_id=dto.agent_version_id,
            trigger_type=dto.trigger_type,
            initiated_by=dto.initiated_by,
            tags=dto.tags,
            metadata=dto.metadata,
        )
        return await self._repo.save(execution)


class StartExecutionUseCase:
    def __init__(self, exec_repo: ExecutionRepository) -> None:
        self._repo = exec_repo

    async def execute(self, exec_id: str, org_id: str) -> Execution:
        execution = await self._repo.get_by_id(exec_id)
        if not execution:
            raise ExecutionNotFoundError(exec_id)
        if execution.org_id != org_id:
            raise ExecutionAccessDeniedError()
        execution.start()
        return await self._repo.update(execution)


class CompleteExecutionUseCase:
    def __init__(self, exec_repo: ExecutionRepository) -> None:
        self._repo = exec_repo

    async def execute(self, dto: CompleteExecutionDTO) -> Execution:
        execution = await self._repo.get_by_id(dto.exec_id)
        if not execution:
            raise ExecutionNotFoundError(dto.exec_id)
        if execution.org_id != dto.org_id:
            raise ExecutionAccessDeniedError()

        cost = calculate_cost(dto.provider, dto.model, dto.input_tokens, dto.output_tokens)
        execution.complete(
            output=dto.output,
            input_tokens=dto.input_tokens,
            output_tokens=dto.output_tokens,
            cost_usd=cost,
            model_provider=dto.provider,
            model_name=dto.model,
        )
        return await self._repo.update(execution)


class FailExecutionUseCase:
    def __init__(self, exec_repo: ExecutionRepository) -> None:
        self._repo = exec_repo

    async def execute(self, dto: FailExecutionDTO) -> Execution:
        execution = await self._repo.get_by_id(dto.exec_id)
        if not execution:
            raise ExecutionNotFoundError(dto.exec_id)
        if execution.org_id != dto.org_id:
            raise ExecutionAccessDeniedError()
        execution.fail(dto.error_message)
        return await self._repo.update(execution)


class CancelExecutionUseCase:
    def __init__(self, exec_repo: ExecutionRepository) -> None:
        self._repo = exec_repo

    async def execute(self, exec_id: str, org_id: str) -> Execution:
        execution = await self._repo.get_by_id(exec_id)
        if not execution:
            raise ExecutionNotFoundError(exec_id)
        if execution.org_id != org_id:
            raise ExecutionAccessDeniedError()
        execution.cancel()
        return await self._repo.update(execution)


class GetExecutionUseCase:
    def __init__(self, exec_repo: ExecutionRepository) -> None:
        self._repo = exec_repo

    async def execute(self, exec_id: str, org_id: str) -> Execution:
        execution = await self._repo.get_by_id(exec_id)
        if not execution:
            raise ExecutionNotFoundError(exec_id)
        if execution.org_id != org_id:
            raise ExecutionAccessDeniedError()
        return execution


class ListExecutionsUseCase:
    def __init__(self, exec_repo: ExecutionRepository) -> None:
        self._repo = exec_repo

    async def execute(self, query: ListExecutionsQuery) -> tuple[list[Execution], int]:
        executions = await self._repo.list_by_org(
            org_id=query.org_id,
            agent_id=query.agent_id,
            status=query.status,
            limit=query.limit,
            offset=query.offset,
        )
        total = await self._repo.count_by_org(
            org_id=query.org_id,
            agent_id=query.agent_id,
            status=query.status,
        )
        return executions, total
