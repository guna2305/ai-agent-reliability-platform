"""Unit tests for execution lifecycle use cases."""
from __future__ import annotations

import pytest
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from src.application.interfaces.repositories import ExecutionRepository
from src.application.use_cases.executions import (
    CancelExecutionUseCase,
    CompleteExecutionDTO,
    CompleteExecutionUseCase,
    CreateExecutionDTO,
    CreateExecutionUseCase,
    ExecutionNotFoundError,
    FailExecutionDTO,
    FailExecutionUseCase,
    GetExecutionUseCase,
    ListExecutionsQuery,
    ListExecutionsUseCase,
    StartExecutionUseCase,
)
from src.domain.entities import Execution
from src.domain.value_objects import ExecutionStatus, TriggerType


# ── In-memory fake ────────────────────────────────────────────────────────────

class FakeExecRepo(ExecutionRepository):
    def __init__(self):
        self._store: dict[str, Execution] = {}

    async def save(self, execution: Execution) -> Execution:
        self._store[execution.id] = execution
        return execution

    async def get_by_id(self, exec_id: str) -> Execution | None:
        return self._store.get(exec_id)

    async def update(self, execution: Execution) -> Execution:
        self._store[execution.id] = execution
        return execution

    async def list_by_org(self, org_id, agent_id=None, status=None, limit=50, offset=0):
        items = [e for e in self._store.values() if e.org_id == org_id]
        if agent_id:
            items = [e for e in items if e.agent_id == agent_id]
        if status:
            items = [e for e in items if e.status == status]
        return items[offset:offset+limit]

    async def count_by_org(self, org_id, agent_id=None, status=None):
        return len(await self.list_by_org(org_id, agent_id, status, 9999, 0))

    async def get_stats(self, org_id, start_dt, end_dt, agent_id=None):
        return {"total": 0, "succeeded": 0, "failed": 0, "success_rate": 0.0,
                "avg_duration_ms": 0.0, "total_tokens": 0, "total_cost_usd": 0.0}

    async def get_cost_by_model(self, org_id, start_dt, end_dt):
        return []

    async def get_daily_costs(self, org_id, start_dt, end_dt):
        return []


@pytest.fixture
def repo() -> FakeExecRepo:
    return FakeExecRepo()


@pytest.mark.asyncio
async def test_create_execution_is_queued(repo):
    uc = CreateExecutionUseCase(repo)
    ex = await uc.execute(CreateExecutionDTO(
        org_id="org-1", agent_id="agent-1", input={"query": "test"},
    ))
    assert ex.status == ExecutionStatus.QUEUED
    assert ex.id is not None


@pytest.mark.asyncio
async def test_start_transitions_to_running(repo):
    create_uc = CreateExecutionUseCase(repo)
    ex = await create_uc.execute(CreateExecutionDTO(org_id="org-1", agent_id="a", input={}))

    start_uc = StartExecutionUseCase(repo)
    ex = await start_uc.execute(ex.id, "org-1")
    assert ex.status == ExecutionStatus.RUNNING


@pytest.mark.asyncio
async def test_complete_execution_calculates_ollama_cost(repo):
    create_uc = CreateExecutionUseCase(repo)
    ex = await create_uc.execute(CreateExecutionDTO(org_id="org-1", agent_id="a", input={}))
    await StartExecutionUseCase(repo).execute(ex.id, "org-1")

    uc = CompleteExecutionUseCase(repo)
    ex = await uc.execute(CompleteExecutionDTO(
        exec_id=ex.id, org_id="org-1", output={"result": "done"},
        input_tokens=500, output_tokens=200, provider="ollama", model="llama3.2",
    ))
    assert ex.status == ExecutionStatus.SUCCEEDED
    assert ex.total_cost_usd == Decimal("0")  # Ollama is free
    assert ex.total_tokens == 700
    assert ex.duration_ms is not None


@pytest.mark.asyncio
async def test_fail_execution(repo):
    create_uc = CreateExecutionUseCase(repo)
    ex = await create_uc.execute(CreateExecutionDTO(org_id="org-1", agent_id="a", input={}))
    await StartExecutionUseCase(repo).execute(ex.id, "org-1")

    uc = FailExecutionUseCase(repo)
    ex = await uc.execute(FailExecutionDTO(exec_id=ex.id, org_id="org-1", error_message="Timeout"))
    assert ex.status == ExecutionStatus.FAILED
    assert ex.error_message == "Timeout"


@pytest.mark.asyncio
async def test_cancel_from_queued(repo):
    create_uc = CreateExecutionUseCase(repo)
    ex = await create_uc.execute(CreateExecutionDTO(org_id="org-1", agent_id="a", input={}))
    uc = CancelExecutionUseCase(repo)
    ex = await uc.execute(ex.id, "org-1")
    assert ex.status == ExecutionStatus.CANCELLED


@pytest.mark.asyncio
async def test_get_not_found(repo):
    uc = GetExecutionUseCase(repo)
    with pytest.raises(ExecutionNotFoundError):
        await uc.execute("nonexistent", "org-1")


@pytest.mark.asyncio
async def test_list_executions_filters(repo):
    create_uc = CreateExecutionUseCase(repo)
    for _ in range(3):
        ex = await create_uc.execute(CreateExecutionDTO(org_id="org-1", agent_id="a", input={}))
        await StartExecutionUseCase(repo).execute(ex.id, "org-1")
        await CompleteExecutionUseCase(repo).execute(CompleteExecutionDTO(
            exec_id=ex.id, org_id="org-1", output={},
        ))
    # Add one failed
    ex = await create_uc.execute(CreateExecutionDTO(org_id="org-1", agent_id="a", input={}))
    await StartExecutionUseCase(repo).execute(ex.id, "org-1")
    await FailExecutionUseCase(repo).execute(FailExecutionDTO(ex.id, "org-1", "err"))

    list_uc = ListExecutionsUseCase(repo)
    succeeded, total = await list_uc.execute(ListExecutionsQuery(
        org_id="org-1", status=ExecutionStatus.SUCCEEDED
    ))
    assert total == 3
    failed, _ = await list_uc.execute(ListExecutionsQuery(
        org_id="org-1", status=ExecutionStatus.FAILED
    ))
    assert len(failed) == 1
