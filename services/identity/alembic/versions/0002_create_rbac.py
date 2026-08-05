"""create identity RBAC tables

Revision ID: 0002_identity_rbac
Revises: 0001_identity_users
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0002_identity_rbac"
down_revision = "0001_identity_users"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "identity_permissions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "code",
            sa.String(length=150),
            nullable=False,
        ),
        sa.Column(
            "description",
            sa.String(length=500),
            nullable=False,
            server_default="",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "code",
            name="uq_identity_permissions_code",
        ),
    )

    op.create_table(
        "identity_roles",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "name",
            sa.String(length=150),
            nullable=False,
        ),
        sa.Column(
            "description",
            sa.String(length=500),
            nullable=False,
            server_default="",
        ),
        sa.Column(
            "is_system",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "name",
            name="uq_identity_roles_tenant_name",
        ),
    )

    op.create_index(
        "ix_identity_roles_tenant_id",
        "identity_roles",
        ["tenant_id"],
    )

    op.create_table(
        "identity_role_permissions",
        sa.Column(
            "role_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "permission_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["permission_id"],
            ["identity_permissions.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["role_id"],
            ["identity_roles.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "role_id",
            "permission_id",
        ),
    )

    op.create_table(
        "identity_user_roles",
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "role_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["role_id"],
            ["identity_roles.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["identity_users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "user_id",
            "role_id",
        ),
    )

    op.create_index(
        "ix_identity_user_roles_tenant_id",
        "identity_user_roles",
        ["tenant_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_identity_user_roles_tenant_id",
        table_name="identity_user_roles",
    )
    op.drop_table("identity_user_roles")
    op.drop_table("identity_role_permissions")

    op.drop_index(
        "ix_identity_roles_tenant_id",
        table_name="identity_roles",
    )
    op.drop_table("identity_roles")
    op.drop_table("identity_permissions")
