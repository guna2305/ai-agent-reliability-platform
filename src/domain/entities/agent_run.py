from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from src.domain.exceptions import InvalidRunTransitionError
from src.domain.value_objects import RunStatus

_VALID_RUN_TRANSITIONS: dict[RunStatus, set[RunStatus]] = {
    RunStatus.PENDING: {RunStatus.RUNNING, RunStatus.FAILED},
    RunStatus.RUNNING: {RunStatus.SUCCEEDED, RunStatus.FAILED, RunStatus.TIMED_OUT},
    RunStatus.SUCCEEDED: set(),
    RunStatus.FAILED: set(),
    RunStatus.TIMED_OUT: set(),
}


@dataclass
class AgentRun:
    id: str
    agent_id: str
    status: RunStatus
    started_at: datetime
    completed_at: datetime | None
    duration_ms: int | None
    input_tokens: int | None
    output_tokens: int | None
    error_message: str | None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        agent_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> AgentRun:
        return cls(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            status=RunStatus.PENDING,
            started_at=datetime.now(UTC),
            completed_at=None,
            duration_ms=None,
            input_tokens=None,
            output_tokens=None,
            error_message=None,
            metadata=metadata or {},
        )

    def start(self) -> None:
        self._transition(RunStatus.RUNNING)

    def complete(self, input_tokens: int | None = None, output_tokens: int | None = None) -> None:
        self._transition(RunStatus.SUCCEEDED)
        self._finalize(input_tokens=input_tokens, output_tokens=output_tokens)

    def fail(self, error_message: str) -> None:
        self._transition(RunStatus.FAILED)
        self.error_message = error_message
        self._finalize()

    def timeout(self) -> None:
        self._transition(RunStatus.TIMED_OUT)
        self._finalize()

    def _transition(self, new_status: RunStatus) -> None:
        allowed = _VALID_RUN_TRANSITIONS.get(self.status, set())
        if new_status not in allowed:
            raise InvalidRunTransitionError(self.id, self.status.value, new_status.value)
        self.status = new_status

    def _finalize(
        self,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
    ) -> None:
        self.completed_at = datetime.now(UTC)
        self.duration_ms = int(
            (self.completed_at - self.started_at).total_seconds() * 1000
        )
        if input_tokens is not None:
            self.input_tokens = input_tokens
        if output_tokens is not None:
            self.output_tokens = output_tokens

    @property
    def is_terminal(self) -> bool:
        return self.status in {RunStatus.SUCCEEDED, RunStatus.FAILED, RunStatus.TIMED_OUT}
