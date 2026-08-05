from __future__ import annotations

from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
)


class PasswordResetRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    token: str = Field(min_length=20, max_length=500)
    new_password: str = Field(
        min_length=12,
        max_length=128,
    )


class PasswordResetAccepted(BaseModel):
    model_config = ConfigDict(extra="forbid")

    accepted: bool = True
    message: str = (
        "If the account exists, password reset instructions "
        "will be issued"
    )


class LogoutRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    refresh_token: str = Field(min_length=20)


class LogoutResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    revoked: bool = True
