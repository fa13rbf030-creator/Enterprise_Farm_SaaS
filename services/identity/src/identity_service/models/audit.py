from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from identity_service.db.base import Base


class AuditEvent(Base):
    __tablename__ = "identity_audit_events"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    tenant_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
        index=True,
    )
    actor_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        index=True,
    )
    resource_type: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )
    resource_id: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )
    outcome: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="success",
    )
    ip_address: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )
    user_agent: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    details: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )
