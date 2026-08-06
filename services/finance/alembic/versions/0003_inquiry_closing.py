"""add opening balances and fiscal year close runs

Revision ID: 0003_finance_closing
Revises: 0002_finance_posting
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0003_finance_closing"
down_revision = "0002_finance_posting"
branch_labels = None
depends_on = None


opening_status = sa.Enum(
    "DRAFT",
    "VALIDATED",
    "POSTED",
    "REJECTED",
    name="finance_opening_balance_status",
)

close_status = sa.Enum(
    "OPEN",
    "IN_PROGRESS",
    "CLOSED",
    "FAILED",
    name="finance_fiscal_year_close_status",
)


def upgrade() -> None:
    op.create_table(
        "finance_opening_balance_batches",
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
            "fiscal_period_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "batch_number",
            sa.String(100),
            nullable=False,
        ),
        sa.Column(
            "description",
            sa.String(500),
            nullable=False,
            server_default="",
        ),
        sa.Column(
            "status",
            opening_status,
            nullable=False,
            server_default="DRAFT",
        ),
        sa.Column(
            "total_debit",
            sa.Numeric(24, 6),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "total_credit",
            sa.Numeric(24, 6),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "validated_by",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "posted_journal_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["fiscal_period_id"],
            ["finance_fiscal_periods.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["posted_journal_id"],
            ["finance_journal_entries.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "batch_number",
            name=(
                "uq_finance_opening_balance_batches_"
                "tenant_number"
            ),
        ),
    )

    op.create_index(
        "ix_finance_opening_balance_batches_tenant_id",
        "finance_opening_balance_batches",
        ["tenant_id"],
    )
    op.create_index(
        "ix_finance_opening_balance_batches_fiscal_period_id",
        "finance_opening_balance_batches",
        ["fiscal_period_id"],
    )

    op.create_table(
        "finance_opening_balance_lines",
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
            "batch_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "ledger_account_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "debit",
            sa.Numeric(24, 6),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "credit",
            sa.Numeric(24, 6),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "description",
            sa.String(500),
            nullable=False,
            server_default="",
        ),
        sa.ForeignKeyConstraint(
            ["batch_id"],
            ["finance_opening_balance_batches.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["ledger_account_id"],
            ["finance_ledger_accounts.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "batch_id",
            "ledger_account_id",
            name=(
                "uq_finance_opening_balance_lines_"
                "batch_account"
            ),
        ),
    )

    op.create_index(
        "ix_finance_opening_balance_lines_tenant_id",
        "finance_opening_balance_lines",
        ["tenant_id"],
    )
    op.create_index(
        "ix_finance_opening_balance_lines_batch_id",
        "finance_opening_balance_lines",
        ["batch_id"],
    )
    op.create_index(
        "ix_finance_opening_balance_lines_ledger_account_id",
        "finance_opening_balance_lines",
        ["ledger_account_id"],
    )

    op.create_table(
        "finance_fiscal_year_close_runs",
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
            "fiscal_year_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "retained_earnings_account_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "closing_journal_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "status",
            close_status,
            nullable=False,
            server_default="OPEN",
        ),
        sa.Column(
            "net_income",
            sa.Numeric(24, 6),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "started_by",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "completed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "error_message",
            sa.String(1000),
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
            ["fiscal_year_id"],
            ["finance_fiscal_years.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["retained_earnings_account_id"],
            ["finance_ledger_accounts.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["closing_journal_id"],
            ["finance_journal_entries.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "fiscal_year_id",
            name=(
                "uq_finance_fiscal_year_close_runs_"
                "tenant_year"
            ),
        ),
    )

    op.create_index(
        "ix_finance_fiscal_year_close_runs_tenant_id",
        "finance_fiscal_year_close_runs",
        ["tenant_id"],
    )
    op.create_index(
        "ix_finance_fiscal_year_close_runs_fiscal_year_id",
        "finance_fiscal_year_close_runs",
        ["fiscal_year_id"],
    )


def downgrade() -> None:
    op.drop_table("finance_fiscal_year_close_runs")
    op.drop_table("finance_opening_balance_lines")
    op.drop_table("finance_opening_balance_batches")

    bind = op.get_bind()
    close_status.drop(bind, checkfirst=True)
    opening_status.drop(bind, checkfirst=True)
