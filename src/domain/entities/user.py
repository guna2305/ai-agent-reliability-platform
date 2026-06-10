from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass
class User:
    id: str
    email: str
    hashed_password: str
    full_name: str
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(
        cls,
        email: str,
        hashed_password: str,
        full_name: str,
        is_superuser: bool = False,
    ) -> User:
        now = datetime.now(UTC)
        return cls(
            id=str(uuid.uuid4()),
            email=email.lower().strip(),
            hashed_password=hashed_password,
            full_name=full_name,
            is_active=True,
            is_superuser=is_superuser,
            created_at=now,
            updated_at=now,
        )

    def deactivate(self) -> None:
        self.is_active = False
        self.updated_at = datetime.now(UTC)

    def update_password(self, hashed_password: str) -> None:
        self.hashed_password = hashed_password
        self.updated_at = datetime.now(UTC)
