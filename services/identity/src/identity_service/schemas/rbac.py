from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PermissionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(
        min_length=3,
        max_length=150,
        pattern=r"^[a-z0-9_.:-]+$",
    )
    description: str = Field(
        default="",
        max_length=500,
    )


class PermissionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    description: str


class RoleCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    name: str = Field(min_length=2, max_length=150)
    description: str = Field(default="", max_length=500)
    permission_ids: list[UUID] = Field(default_factory=list)


class RoleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    name: str
    description: str
    is_system: bool


class UserRoleAssignment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    user_id: UUID
    role_ids: list[UUID] = Field(min_length=1)
