from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from src.domain.entities import Execution, ExecutionTrace, ToolCall
from src.domain.value_objects import ExecutionStatus


class ExecutionRepository(ABC):
    @abstractmethod
    async def save(self, execution: Execution) -> Execution: ...

    @abstractmethod
    async def get_by_id(self, exec_id: str) -> Execution | None: ...

    @abstractmethod
    async def update(self, execution: Execution) -> Execution: ...

    @abstractmethod
    async def list_by_org(
        self,
        org_id: str,
        agent_id: str | None = None,
        status: ExecutionStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Execution]: ...

    @abstractmethod
    async def count_by_org(
        self,
        org_id: str,
        agent_id: str | None = None,
        status: ExecutionStatus | None = None,
    ) -> int: ...

    @abstractmethod
    async def get_stats(
        self,
        org_id: str,
        start_dt: datetime,
        end_dt: datetime,
        agent_id: str | None = None,
    ) -> dict: ...

    @abstractmethod
    async def get_cost_by_model(
        self,
        org_id: str,
        start_dt: datetime,
        end_dt: datetime,
    ) -> list[dict]: ...

    @abstractmethod
    async def get_daily_costs(
        self,
        org_id: str,
        start_dt: datetime,
        end_dt: datetime,
    ) -> list[dict]: ...


class ExecutionTraceRepository(ABC):
    @abstractmethod
    async def save(self, trace: ExecutionTrace) -> ExecutionTrace: ...

    @abstractmethod
    async def get_by_id(self, trace_id: str) -> ExecutionTrace | None: ...

    @abstractmethod
    async def list_by_execution(self, exec_id: str) -> list[ExecutionTrace]: ...

    @abstractmethod
    async def update(self, trace: ExecutionTrace) -> ExecutionTrace: ...


class ToolCallRepository(ABC):
    @abstractmethod
    async def save(self, tool_call: ToolCall) -> ToolCall: ...

    @abstractmethod
    async def get_by_id(self, call_id: str) -> ToolCall | None: ...

    @abstractmethod
    async def list_by_execution(self, exec_id: str) -> list[ToolCall]: ...

    @abstractmethod
    async def update(self, tool_call: ToolCall) -> ToolCall: ...
