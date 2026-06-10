from __future__ import annotations

import hashlib
import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime


def _generate_key() -> tuple[str, str, str]:
    """Returns (raw_key, prefix, hash)."""
    raw = f"aarp_{secrets.token_urlsafe(32)}"
    prefix = raw[:12]
    key_hash = hashlib.sha256(raw.encode()).hexdigest()
    return raw, prefix, key_hash


@dataclass
class ApiKey:
    id: str
    org_id: str
    user_id: str
    name: str
    key_hash: str
    key_prefix: str
    scopes: list[str]
    last_used_at: datetime | None
    expires_at: datetime | None
    created_at: datetime

    @classmethod
    def create(
        cls,
        org_id: str,
        user_id: str,
        name: str,
        scopes: list[str] | None = None,
        expires_at: datetime | None = None,
    ) -> tuple[ApiKey, str]:
        raw_key, prefix, key_hash = _generate_key()
        api_key = cls(
            id=str(uuid.uuid4()),
            org_id=org_id,
            user_id=user_id,
            name=name,
            key_hash=key_hash,
            key_prefix=prefix,
            scopes=scopes or ["read", "write"],
            last_used_at=None,
            expires_at=expires_at,
            created_at=datetime.now(UTC),
        )
        return api_key, raw_key

    def record_use(self) -> None:
        self.last_used_at = datetime.now(UTC)

    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return datetime.now(UTC) > self.expires_at
