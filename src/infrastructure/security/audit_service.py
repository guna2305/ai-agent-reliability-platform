"""Write immutable audit log entries for security-sensitive mutations."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models.analytics_model import AuditLogModel


async def write_audit_log(
    session: AsyncSession,
    action: str,
    resource_type: str,
    resource_id: str | None = None,
    org_id: str | None = None,
    user_id: str | None = None,
    old_value: dict[str, Any] | None = None,
    new_value: dict[str, Any] | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> None:
    entry = AuditLogModel(
        id=str(uuid.uuid4()),
        org_id=org_id,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        old_value=old_value,
        new_value=new_value,
        ip_address=ip_address,
        user_agent=user_agent,
        created_at=datetime.now(UTC),
    )
    session.add(entry)
    # Caller must commit the session
