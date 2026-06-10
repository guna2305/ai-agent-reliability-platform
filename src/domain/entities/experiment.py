from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any


@dataclass
class Experiment:
    id: str
    org_id: str
    name: str
    description: str | None
    status: str  # active / paused / completed
    config: dict[str, Any]
    created_by: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(
        cls,
        org_id: str,
        name: str,
        created_by: str,
        description: str | None = None,
        config: dict[str, Any] | None = None,
    ) -> Experiment:
        now = datetime.now(UTC)
        return cls(
            id=str(uuid.uuid4()),
            org_id=org_id,
            name=name,
            description=description,
            status="active",
            config=config or {},
            created_by=created_by,
            created_at=now,
            updated_at=now,
        )

    def pause(self) -> None:
        self.status = "paused"
        self.updated_at = datetime.now(UTC)

    def complete(self) -> None:
        self.status = "completed"
        self.updated_at = datetime.now(UTC)


@dataclass
class ExperimentVariant:
    id: str
    experiment_id: str
    agent_version_id: str
    name: str
    traffic_weight: Decimal  # 0.0 - 1.0
    config: dict[str, Any]

    @classmethod
    def create(
        cls,
        experiment_id: str,
        agent_version_id: str,
        name: str,
        traffic_weight: float,
        config: dict[str, Any] | None = None,
    ) -> ExperimentVariant:
        return cls(
            id=str(uuid.uuid4()),
            experiment_id=experiment_id,
            agent_version_id=agent_version_id,
            name=name,
            traffic_weight=Decimal(str(traffic_weight)),
            config=config or {},
        )
