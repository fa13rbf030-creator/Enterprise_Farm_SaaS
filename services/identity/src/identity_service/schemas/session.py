from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class SessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    user_id: UUID
    ip_address: str | None
    user_agent: str | None
    device_name: str | None
    is_trusted: bool
    last_seen_at: datetime
    expires_at: datetime
    revoked_at: datetime | None
    created_at: datetime


class SessionTrustUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    is_trusted: bool


class RevokeAllSessionsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    revoked_count: int
