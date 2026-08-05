"""add posting audit and account balances

Revision ID: 0002_finance_posting
Revises: 0001_finance_gl
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0002_finance_posting"
down_revision = "0001_finance_gl"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "finance_account_balances",
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
            "ledger_account_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "fiscal_period_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "opening_debit",
            sa.Numeric(24, 6),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "opening_credit",
            sa.Numeric(24, 6),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "period_debit",
            sa.Numeric(24, 6),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "period_credit",
            sa.Numeric(24, 6),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "closing_debit",
            sa.Numeric(24, 6),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "closing_credit",
            sa.Numeric(24, 6),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["ledger_account_id"],
            ["finance_ledger_accounts.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["fiscal_period_id"],
            ["finance_fiscal_periods.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "ledger_account_id",
            "fiscal_period_id",
            name=(
                "uq_finance_account_balances_"
                "tenant_account_period"
            ),
        ),
    )

    op.create_index(
        "ix_finance_account_balances_tenant_id",
        "finance_account_balances",
        ["tenant_id"],
    )
    op.create_index(
        "ix_finance_account_balances_ledger_account_id",
        "finance_account_balances",
        ["ledger_account_id"],
    )
    op.create_index(
        "ix_finance_account_balances_fiscal_period_id",
        "finance_account_balances",
        ["fiscal_period_id"],
    )

    op.create_table(
        "finance_posting_audit",
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
            "journal_entry_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "action",
            sa.String(50),
            nullable=False,
        ),
        sa.Column(
            "actor_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "previous_status",
            sa.String(50),
            nullable=False,
        ),
        sa.Column(
            "new_status",
            sa.String(50),
            nullable=False,
        ),
        sa.Column(
            "details",
            sa.String(2000),
            nullable=False,
            server_default="",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["journal_entry_id"],
            ["finance_journal_entries.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_finance_posting_audit_tenant_id",
        "finance_posting_audit",
        ["tenant_id"],
    )
    op.create_index(
        "ix_finance_posting_audit_journal_entry_id",
        "finance_posting_audit",
        ["journal_entry_id"],
    )


def downgrade() -> None:
    op.drop_table("finance_posting_audit")
    op.drop_table("finance_account_balances")
