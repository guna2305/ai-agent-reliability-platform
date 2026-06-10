from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass
class Dataset:
    id: str
    org_id: str
    name: str
    description: str | None
    dataset_type: str  # golden / benchmark / regression
    created_by: str
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(
        cls,
        org_id: str,
        name: str,
        created_by: str,
        dataset_type: str = "golden",
        description: str | None = None,
    ) -> Dataset:
        now = datetime.now(UTC)
        return cls(
            id=str(uuid.uuid4()),
            org_id=org_id,
            name=name,
            description=description,
            dataset_type=dataset_type,
            created_by=created_by,
            metadata={},
            created_at=now,
            updated_at=now,
        )


@dataclass
class DatasetItem:
    id: str
    dataset_id: str
    input: dict[str, Any]
    expected_output: dict[str, Any] | None
    context: list[str]
    metadata: dict[str, Any]
    created_at: datetime

    @classmethod
    def create(
        cls,
        dataset_id: str,
        input: dict[str, Any],
        expected_output: dict[str, Any] | None = None,
        context: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> DatasetItem:
        return cls(
            id=str(uuid.uuid4()),
            dataset_id=dataset_id,
            input=input,
            expected_output=expected_output,
            context=context or [],
            metadata=metadata or {},
            created_at=datetime.now(UTC),
        )
