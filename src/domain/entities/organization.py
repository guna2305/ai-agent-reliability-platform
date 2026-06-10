from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime


def _slugify(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_-]+", "-", slug)
    return slug[:63]


@dataclass
class Organization:
    id: str
    name: str
    slug: str
    description: str | None
    plan: str  # free / pro / enterprise
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @classmethod
    def create(
        cls,
        name: str,
        description: str | None = None,
        plan: str = "free",
    ) -> Organization:
        now = datetime.now(UTC)
        return cls(
            id=str(uuid.uuid4()),
            name=name,
            slug=_slugify(name),
            description=description,
            plan=plan,
            created_at=now,
            updated_at=now,
        )

    def upgrade_plan(self, plan: str) -> None:
        self.plan = plan
        self.updated_at = datetime.now(UTC)


@dataclass
class OrgMember:
    id: str
    org_id: str
    user_id: str
    role: str
    created_at: datetime

    @classmethod
    def create(cls, org_id: str, user_id: str, role: str) -> OrgMember:
        return cls(
            id=str(uuid.uuid4()),
            org_id=org_id,
            user_id=user_id,
            role=role,
            created_at=datetime.now(UTC),
        )
