from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from src.domain.value_objects import ExecutionStatus, TriggerType
from src.domain.exceptions import InvalidRunTransitionError


_VALID_TRANSITIONS: dict[ExecutionStatus, set[ExecutionStatus]] = {
    ExecutionStatus.QUEUED: {ExecutionStatus.RUNNING, ExecutionStatus.CANCELLED},
    ExecutionStatus.RUNNING: {
        ExecutionStatus.SUCCEEDED,
        ExecutionStatus.FAILED,
        ExecutionStatus.TIMED_OUT,
        ExecutionStatus.CANCELLED,
    },
    ExecutionStatus.SUCCEEDED: set(),
    ExecutionStatus.FAILED: set(),
    ExecutionStatus.CANCELLED: set(),
    ExecutionStatus.TIMED_OUT: set(),
}


@dataclass
class Execution:
    id: str
    org_id: str
    agent_id: str
    agent_version_id: str | None
    status: ExecutionStatus
    trigger_type: TriggerType
    input: dict[str, Any]
    output: dict[str, Any] | None
    error_message: str | None
    started_at: datetime
    completed_at: datetime | None
    duration_ms: int | None
    total_tokens: int | None
    input_tokens: int | None
    output_tokens: int | None
    total_cost_usd: Decimal | None
    model_provider: str | None
    model_name: str | None
    tags: list[str]
    metadata: dict[str, Any]
    initiated_by: str | None
    created_at: datetime

    @classmethod
    def create(
        cls,
        org_id: str,
        agent_id: str,
        input: dict[str, Any],
        agent_version_id: str | None = None,
        trigger_type: TriggerType = TriggerType.API,
        initiated_by: str | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Execution:
        now = datetime.now(timezone.utc)
        return cls(
            id=str(uuid.uuid4()),
            org_id=org_id,
            agent_id=agent_id,
            agent_version_id=agent_version_id,
            status=ExecutionStatus.QUEUED,
            trigger_type=trigger_type,
            input=input,
            output=None,
            error_message=None,
            started_at=now,
            completed_at=None,
            duration_ms=None,
            total_tokens=None,
            input_tokens=None,
            output_tokens=None,
            total_cost_usd=None,
            model_provider=None,
            model_name=None,
            tags=tags or [],
            metadata=metadata or {},
            initiated_by=initiated_by,
            created_at=now,
        )

    def start(self) -> None:
        self._transition(ExecutionStatus.RUNNING)

    def complete(
        self,
        output: dict[str, Any],
        input_tokens: int = 0,
        output_tokens: int = 0,
        cost_usd: Decimal | None = None,
        model_provider: str | None = None,
        model_name: str | None = None,
    ) -> None:
        self._transition(ExecutionStatus.SUCCEEDED)
        self.output = output
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.total_tokens = input_tokens + output_tokens
        self.total_cost_usd = cost_usd
        self.model_provider = model_provider
        self.model_name = model_name
        self._finalize()

    def fail(self, error_message: str) -> None:
        self._transition(ExecutionStatus.FAILED)
        self.error_message = error_message
        self._finalize()

    def cancel(self) -> None:
        self._transition(ExecutionStatus.CANCELLED)
        self._finalize()

    def timeout(self) -> None:
        self._transition(ExecutionStatus.TIMED_OUT)
        self._finalize()

    def _transition(self, new_status: ExecutionStatus) -> None:
        allowed = _VALID_TRANSITIONS.get(self.status, set())
        if new_status not in allowed:
            raise InvalidRunTransitionError(self.id, self.status.value, new_status.value)
        self.status = new_status

    def _finalize(self) -> None:
        self.completed_at = datetime.now(timezone.utc)
        self.duration_ms = int((self.completed_at - self.started_at).total_seconds() * 1000)

    @property
    def is_terminal(self) -> bool:
        return self.status.is_terminal
