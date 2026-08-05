"""identity security hardening

Revision ID: 0004_identity_security
Revises: 0003_identity_audit
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0004_identity_security"
down_revision = "0003_identity_audit"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "identity_users",
        sa.Column(
            "failed_login_attempts",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "identity_users",
        sa.Column(
            "locked_until",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "identity_users",
        sa.Column(
            "last_login_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "identity_users",
        sa.Column(
            "password_changed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.create_table(
        "identity_password_reset_tokens",
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
            "user_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "token_hash",
            sa.String(length=128),
            nullable=False,
        ),
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "used_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["identity_users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "token_hash",
            name="uq_identity_password_reset_tokens_hash",
        ),
    )

    op.create_index(
        "ix_identity_password_reset_tokens_tenant_id",
        "identity_password_reset_tokens",
        ["tenant_id"],
    )
    op.create_index(
        "ix_identity_password_reset_tokens_user_id",
        "identity_password_reset_tokens",
        ["user_id"],
    )
    op.create_index(
        "ix_identity_password_reset_tokens_expires_at",
        "identity_password_reset_tokens",
        ["expires_at"],
    )

    op.create_table(
        "identity_revoked_tokens",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "token_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "token_type",
            sa.String(length=32),
            nullable=False,
        ),
        sa.Column(
            "reason",
            sa.String(length=200),
            nullable=False,
            server_default="logout",
        ),
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "revoked_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["identity_users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "token_id",
            name="uq_identity_revoked_tokens_token_id",
        ),
    )

    op.create_index(
        "ix_identity_revoked_tokens_tenant_id",
        "identity_revoked_tokens",
        ["tenant_id"],
    )
    op.create_index(
        "ix_identity_revoked_tokens_user_id",
        "identity_revoked_tokens",
        ["user_id"],
    )
    op.create_index(
        "ix_identity_revoked_tokens_expires_at",
        "identity_revoked_tokens",
        ["expires_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_identity_revoked_tokens_expires_at",
        table_name="identity_revoked_tokens",
    )
    op.drop_index(
        "ix_identity_revoked_tokens_user_id",
        table_name="identity_revoked_tokens",
    )
    op.drop_index(
        "ix_identity_revoked_tokens_tenant_id",
        table_name="identity_revoked_tokens",
    )
    op.drop_table("identity_revoked_tokens")

    op.drop_index(
        "ix_identity_password_reset_tokens_expires_at",
        table_name="identity_password_reset_tokens",
    )
    op.drop_index(
        "ix_identity_password_reset_tokens_user_id",
        table_name="identity_password_reset_tokens",
    )
    op.drop_index(
        "ix_identity_password_reset_tokens_tenant_id",
        table_name="identity_password_reset_tokens",
    )
    op.drop_table("identity_password_reset_tokens")

    op.drop_column(
        "identity_users",
        "password_changed_at",
    )
    op.drop_column(
        "identity_users",
        "last_login_at",
    )
    op.drop_column(
        "identity_users",
        "locked_until",
    )
    op.drop_column(
        "identity_users",
        "failed_login_attempts",
    )
