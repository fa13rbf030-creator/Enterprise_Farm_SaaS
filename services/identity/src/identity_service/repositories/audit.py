from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from identity_service.models.audit import AuditEvent


async def record_audit_event(
    session: AsyncSession,
    *,
    event_type: str,
    outcome: str,
    tenant_id: UUID | None = None,
    actor_id: UUID | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    details: dict | None = None,
    commit: bool = True,
) -> AuditEvent:
    event = AuditEvent(
        tenant_id=tenant_id,
        actor_id=actor_id,
        event_type=event_type,
        resource_type=resource_type,
        resource_id=resource_id,
        outcome=outcome,
        ip_address=ip_address,
        user_agent=user_agent,
        details=details or {},
    )

    session.add(event)

    if commit:
        await session.commit()
        await session.refresh(event)

    return event
