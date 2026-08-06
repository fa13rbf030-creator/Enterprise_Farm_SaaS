"""add banking and reconciliation foundation

Revision ID: 0006_finance_banking
Revises: 0005_finance_ap
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0006_finance_banking"
down_revision = "0005_finance_ap"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "finance_bank_accounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("account_code", sa.String(50), nullable=False),
        sa.Column("account_name", sa.String(200), nullable=False),
        sa.Column("bank_name", sa.String(200), nullable=False),
        sa.Column("branch_name", sa.String(200), nullable=False, server_default=""),
        sa.Column("branch_code", sa.String(50), nullable=True),
        sa.Column("account_number", sa.String(100), nullable=False),
        sa.Column("iban", sa.String(100), nullable=True),
        sa.Column("swift_code", sa.String(50), nullable=True),
        sa.Column("currency_code", sa.String(3), nullable=False, server_default="PKR"),
        sa.Column(
            "account_type",
            sa.Enum(
                "CURRENT",
                "SAVINGS",
                "CASH",
                "PETTY_CASH",
                "MOBILE_WALLET",
                name="finance_bank_account_type",
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "ACTIVE",
                "INACTIVE",
                "CLOSED",
                name="finance_bank_account_status",
            ),
            nullable=False,
            server_default="ACTIVE",
        ),
        sa.Column("ledger_account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("opening_balance", sa.Numeric(24, 6), nullable=False, server_default="0"),
        sa.Column("current_balance", sa.Numeric(24, 6), nullable=False, server_default="0"),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["ledger_account_id"], ["finance_ledger_accounts.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "account_code",
            name="uq_finance_bank_accounts_tenant_code",
        ),
        sa.UniqueConstraint(
            "tenant_id",
            "iban",
            name="uq_finance_bank_accounts_tenant_iban",
        ),
    )

    op.create_index(
        "ix_finance_bank_accounts_tenant_id",
        "finance_bank_accounts",
        ["tenant_id"],
    )

    op.create_table(
        "finance_bank_statements",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("bank_account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("statement_number", sa.String(100), nullable=False),
        sa.Column("statement_date", sa.Date(), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("opening_balance", sa.Numeric(24, 6), nullable=False),
        sa.Column("closing_balance", sa.Numeric(24, 6), nullable=False),
        sa.Column("total_credits", sa.Numeric(24, 6), nullable=False, server_default="0"),
        sa.Column("total_debits", sa.Numeric(24, 6), nullable=False, server_default="0"),
        sa.Column(
            "status",
            sa.Enum(
                "DRAFT",
                "IMPORTED",
                "IN_RECONCILIATION",
                "RECONCILED",
                "VOID",
                name="finance_bank_statement_status",
            ),
            nullable=False,
            server_default="DRAFT",
        ),
        sa.Column("source_file_name", sa.String(500), nullable=True),
        sa.Column("imported_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("imported_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["bank_account_id"], ["finance_bank_accounts.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "bank_account_id",
            "statement_number",
            name=(
                "uq_finance_bank_statements_"
                "tenant_account_number"
            ),
        ),
    )

    op.create_index(
        "ix_finance_bank_statements_tenant_id",
        "finance_bank_statements",
        ["tenant_id"],
    )
    op.create_index(
        "ix_finance_bank_statements_bank_account_id",
        "finance_bank_statements",
        ["bank_account_id"],
    )

    op.create_table(
        "finance_bank_statement_lines",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("statement_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("line_number", sa.Integer(), nullable=False),
        sa.Column("transaction_date", sa.Date(), nullable=False),
        sa.Column("value_date", sa.Date(), nullable=True),
        sa.Column("reference_number", sa.String(200), nullable=True),
        sa.Column("description", sa.String(1000), nullable=False),
        sa.Column(
            "line_type",
            sa.Enum(
                "CREDIT",
                "DEBIT",
                name="finance_bank_statement_line_type",
            ),
            nullable=False,
        ),
        sa.Column("amount", sa.Numeric(24, 6), nullable=False),
        sa.Column("running_balance", sa.Numeric(24, 6), nullable=True),
        sa.Column("is_reconciled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("matched_journal_entry_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["statement_id"], ["finance_bank_statements.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["matched_journal_entry_id"], ["finance_journal_entries.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "statement_id",
            "line_number",
            name=(
                "uq_finance_bank_statement_lines_"
                "statement_number"
            ),
        ),
    )

    op.create_index(
        "ix_finance_bank_statement_lines_tenant_id",
        "finance_bank_statement_lines",
        ["tenant_id"],
    )
    op.create_index(
        "ix_finance_bank_statement_lines_statement_id",
        "finance_bank_statement_lines",
        ["statement_id"],
    )

    op.create_table(
        "finance_bank_reconciliations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("bank_account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("statement_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reconciliation_date", sa.Date(), nullable=False),
        sa.Column("book_balance", sa.Numeric(24, 6), nullable=False),
        sa.Column("statement_balance", sa.Numeric(24, 6), nullable=False),
        sa.Column("reconciled_amount", sa.Numeric(24, 6), nullable=False, server_default="0"),
        sa.Column("difference_amount", sa.Numeric(24, 6), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "DRAFT",
                "IN_PROGRESS",
                "COMPLETED",
                "CANCELLED",
                name="finance_reconciliation_status",
            ),
            nullable=False,
            server_default="DRAFT",
        ),
        sa.Column("started_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("completed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["bank_account_id"], ["finance_bank_accounts.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["statement_id"], ["finance_bank_statements.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "bank_account_id",
            "statement_id",
            name=(
                "uq_finance_bank_reconciliations_"
                "tenant_account_statement"
            ),
        ),
    )

    op.create_index(
        "ix_finance_bank_reconciliations_tenant_id",
        "finance_bank_reconciliations",
        ["tenant_id"],
    )

    op.create_table(
        "finance_bank_reconciliation_matches",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reconciliation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("statement_line_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("journal_entry_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "match_type",
            sa.Enum(
                "EXACT",
                "PARTIAL",
                "MANUAL",
                "BANK_CHARGE",
                "BANK_INTEREST",
                name="finance_reconciliation_match_type",
            ),
            nullable=False,
        ),
        sa.Column("matched_amount", sa.Numeric(24, 6), nullable=False),
        sa.Column("matched_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("matched_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["reconciliation_id"], ["finance_bank_reconciliations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["statement_line_id"], ["finance_bank_statement_lines.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["journal_entry_id"], ["finance_journal_entries.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "reconciliation_id",
            "statement_line_id",
            name=(
                "uq_finance_bank_reconciliation_matches_"
                "reconciliation_line"
            ),
        ),
    )


def downgrade() -> None:
    op.drop_table("finance_bank_reconciliation_matches")
    op.drop_table("finance_bank_reconciliations")
    op.drop_table("finance_bank_statement_lines")
    op.drop_table("finance_bank_statements")
    op.drop_table("finance_bank_accounts")
