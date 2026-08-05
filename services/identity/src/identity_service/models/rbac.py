from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from identity_service.db.base import Base


class Permission(Base):
    __tablename__ = "identity_permissions"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    code: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        unique=True,
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        default="",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class Role(Base):
    __tablename__ = "identity_roles"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "name",
            name="uq_identity_roles_tenant_name",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        default="",
    )
    is_system: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class RolePermission(Base):
    __tablename__ = "identity_role_permissions"

    role_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "identity_roles.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )
    permission_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "identity_permissions.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )


class UserRole(Base):
    __tablename__ = "identity_user_roles"

    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "identity_users.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )
    role_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "identity_roles.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        index=True,
    )
