"""create finance general ledger foundation

Revision ID: 0001_finance_gl
Revises:
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0001_finance_gl"
down_revision = None
branch_labels = None
depends_on = None


account_type = sa.Enum(
    "ASSET",
    "LIABILITY",
    "EQUITY",
    "REVENUE",
    "EXPENSE",
    name="finance_account_type",
)

normal_balance = sa.Enum(
    "DEBIT",
    "CREDIT",
    name="finance_normal_balance",
)

account_status = sa.Enum(
    "ACTIVE",
    "INACTIVE",
    "ARCHIVED",
    name="finance_account_status",
)

period_status = sa.Enum(
    "OPEN",
    "SOFT_CLOSED",
    "CLOSED",
    name="finance_fiscal_period_status",
)

journal_source = sa.Enum(
    "MANUAL",
    "ACCOUNTS_RECEIVABLE",
    "ACCOUNTS_PAYABLE",
    "INVENTORY",
    "PAYROLL",
    "AGRICULTURE",
    "MANUFACTURING",
    "SYSTEM",
    name="finance_journal_source",
)

journal_status = sa.Enum(
    "DRAFT",
    "POSTED",
    "REVERSED",
    "VOID",
    name="finance_journal_status",
)


def upgrade() -> None:
    bind = op.get_bind()


    op.create_table(
        "finance_ledger_accounts",
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
            "parent_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column(
            "description",
            sa.Text(),
            nullable=False,
            server_default="",
        ),
        sa.Column(
            "account_type",
            account_type,
            nullable=False,
        ),
        sa.Column(
            "normal_balance",
            normal_balance,
            nullable=False,
        ),
        sa.Column(
            "status",
            account_status,
            nullable=False,
            server_default="ACTIVE",
        ),
        sa.Column(
            "currency_code",
            sa.String(3),
            nullable=False,
            server_default="PKR",
        ),
        sa.Column(
            "is_control_account",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column(
            "allows_manual_posting",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
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
            ["parent_id"],
            ["finance_ledger_accounts.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "code",
            name="uq_finance_ledger_accounts_tenant_code",
        ),
    )

    op.create_index(
        "ix_finance_ledger_accounts_tenant_id",
        "finance_ledger_accounts",
        ["tenant_id"],
    )

    op.create_table(
        "finance_fiscal_years",
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
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("starts_on", sa.Date(), nullable=False),
        sa.Column("ends_on", sa.Date(), nullable=False),
        sa.Column(
            "is_closed",
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
            name="uq_finance_fiscal_years_tenant_name",
        ),
    )

    op.create_index(
        "ix_finance_fiscal_years_tenant_id",
        "finance_fiscal_years",
        ["tenant_id"],
    )

    op.create_table(
        "finance_fiscal_periods",
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
            "period_number",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("starts_on", sa.Date(), nullable=False),
        sa.Column("ends_on", sa.Date(), nullable=False),
        sa.Column(
            "status",
            period_status,
            nullable=False,
            server_default="OPEN",
        ),
        sa.ForeignKeyConstraint(
            ["fiscal_year_id"],
            ["finance_fiscal_years.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "fiscal_year_id",
            "period_number",
            name="uq_finance_fiscal_periods_year_number",
        ),
    )

    op.create_index(
        "ix_finance_fiscal_periods_tenant_id",
        "finance_fiscal_periods",
        ["tenant_id"],
    )
    op.create_index(
        "ix_finance_fiscal_periods_fiscal_year_id",
        "finance_fiscal_periods",
        ["fiscal_year_id"],
    )

    op.create_table(
        "finance_journal_entries",
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
            "journal_number",
            sa.String(100),
            nullable=False,
        ),
        sa.Column("entry_date", sa.Date(), nullable=False),
        sa.Column(
            "source",
            journal_source,
            nullable=False,
            server_default="MANUAL",
        ),
        sa.Column(
            "source_reference",
            sa.String(200),
            nullable=True,
        ),
        sa.Column(
            "description",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "status",
            journal_status,
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
            "posted_by",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "posted_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "reversal_of_id",
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
            ["reversal_of_id"],
            ["finance_journal_entries.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "journal_number",
            name="uq_finance_journal_entries_tenant_number",
        ),
    )

    op.create_index(
        "ix_finance_journal_entries_tenant_id",
        "finance_journal_entries",
        ["tenant_id"],
    )
    op.create_index(
        "ix_finance_journal_entries_fiscal_period_id",
        "finance_journal_entries",
        ["fiscal_period_id"],
    )

    op.create_table(
        "finance_journal_lines",
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
            "ledger_account_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "line_number",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "description",
            sa.String(500),
            nullable=False,
            server_default="",
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
            "currency_code",
            sa.String(3),
            nullable=False,
            server_default="PKR",
        ),
        sa.Column(
            "exchange_rate",
            sa.Numeric(24, 10),
            nullable=False,
            server_default="1",
        ),
        sa.Column(
            "base_debit",
            sa.Numeric(24, 6),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "base_credit",
            sa.Numeric(24, 6),
            nullable=False,
            server_default="0",
        ),
        sa.ForeignKeyConstraint(
            ["journal_entry_id"],
            ["finance_journal_entries.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["ledger_account_id"],
            ["finance_ledger_accounts.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "journal_entry_id",
            "line_number",
            name="uq_finance_journal_lines_entry_number",
        ),
    )

    op.create_index(
        "ix_finance_journal_lines_tenant_id",
        "finance_journal_lines",
        ["tenant_id"],
    )
    op.create_index(
        "ix_finance_journal_lines_journal_entry_id",
        "finance_journal_lines",
        ["journal_entry_id"],
    )
    op.create_index(
        "ix_finance_journal_lines_ledger_account_id",
        "finance_journal_lines",
        ["ledger_account_id"],
    )


def downgrade() -> None:
    op.drop_table("finance_journal_lines")
    op.drop_table("finance_journal_entries")
    op.drop_table("finance_fiscal_periods")
    op.drop_table("finance_fiscal_years")
    op.drop_table("finance_ledger_accounts")

    bind = op.get_bind()

    journal_status.drop(bind, checkfirst=True)
    journal_source.drop(bind, checkfirst=True)
    period_status.drop(bind, checkfirst=True)
    account_status.drop(bind, checkfirst=True)
    normal_balance.drop(bind, checkfirst=True)
    account_type.drop(bind, checkfirst=True)
