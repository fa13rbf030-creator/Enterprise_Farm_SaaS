from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class RefreshTokenRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    refresh_token: str = Field(min_length=20)


class TokenResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class AccessTokenClaims(BaseModel):
    model_config = ConfigDict(extra="forbid")

    subject: UUID
    tenant_id: UUID
    permissions: list[str]
    token_id: UUID
