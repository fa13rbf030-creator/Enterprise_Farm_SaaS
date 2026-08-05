"""create identity audit events

Revision ID: 0003_identity_audit
Revises: 0002_identity_rbac
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0003_identity_audit"
down_revision = "0002_identity_rbac"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "identity_audit_events",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "actor_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "event_type",
            sa.String(length=150),
            nullable=False,
        ),
        sa.Column(
            "resource_type",
            sa.String(length=150),
            nullable=True,
        ),
        sa.Column(
            "resource_id",
            sa.String(length=200),
            nullable=True,
        ),
        sa.Column(
            "outcome",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "ip_address",
            sa.String(length=64),
            nullable=True,
        ),
        sa.Column(
            "user_agent",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "details",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_identity_audit_events_tenant_id",
        "identity_audit_events",
        ["tenant_id"],
    )
    op.create_index(
        "ix_identity_audit_events_actor_id",
        "identity_audit_events",
        ["actor_id"],
    )
    op.create_index(
        "ix_identity_audit_events_event_type",
        "identity_audit_events",
        ["event_type"],
    )
    op.create_index(
        "ix_identity_audit_events_created_at",
        "identity_audit_events",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_identity_audit_events_created_at",
        table_name="identity_audit_events",
    )
    op.drop_index(
        "ix_identity_audit_events_event_type",
        table_name="identity_audit_events",
    )
    op.drop_index(
        "ix_identity_audit_events_actor_id",
        table_name="identity_audit_events",
    )
    op.drop_index(
        "ix_identity_audit_events_tenant_id",
        table_name="identity_audit_events",
    )
    op.drop_table("identity_audit_events")
