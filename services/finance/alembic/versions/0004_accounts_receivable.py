"""add accounts receivable foundation

Revision ID: 0004_finance_ar
Revises: 0003_finance_closing
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0004_finance_ar"
down_revision = "0003_finance_closing"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "finance_customers",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("customer_code", sa.String(50), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("email", sa.String(320), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("billing_address", sa.Text(), nullable=False, server_default=""),
        sa.Column("currency_code", sa.String(3), nullable=False, server_default="PKR"),
        sa.Column("credit_limit", sa.Numeric(24, 6), nullable=False, server_default="0"),
        sa.Column("payment_terms_days", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "status",
            sa.Enum(
                "ACTIVE",
                "ON_HOLD",
                "INACTIVE",
                name="finance_customer_status",
            ),
            nullable=False,
            server_default="ACTIVE",
        ),
        sa.Column("ar_control_account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("revenue_account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tax_account_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_tax_registered", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("tax_registration_number", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["ar_control_account_id"], ["finance_ledger_accounts.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["revenue_account_id"], ["finance_ledger_accounts.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tax_account_id"], ["finance_ledger_accounts.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "customer_code",
            name="uq_finance_customers_tenant_code",
        ),
    )
    op.create_index(
        "ix_finance_customers_tenant_id",
        "finance_customers",
        ["tenant_id"],
    )

    op.create_table(
        "finance_customer_invoices",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("fiscal_period_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("invoice_number", sa.String(100), nullable=False),
        sa.Column("invoice_date", sa.Date(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("currency_code", sa.String(3), nullable=False, server_default="PKR"),
        sa.Column("exchange_rate", sa.Numeric(24, 10), nullable=False, server_default="1"),
        sa.Column("subtotal", sa.Numeric(24, 6), nullable=False, server_default="0"),
        sa.Column("discount_total", sa.Numeric(24, 6), nullable=False, server_default="0"),
        sa.Column("tax_total", sa.Numeric(24, 6), nullable=False, server_default="0"),
        sa.Column("total_amount", sa.Numeric(24, 6), nullable=False, server_default="0"),
        sa.Column("paid_amount", sa.Numeric(24, 6), nullable=False, server_default="0"),
        sa.Column("credited_amount", sa.Numeric(24, 6), nullable=False, server_default="0"),
        sa.Column("outstanding_amount", sa.Numeric(24, 6), nullable=False, server_default="0"),
        sa.Column(
            "status",
            sa.Enum(
                "DRAFT",
                "ISSUED",
                "PARTIALLY_PAID",
                "PAID",
                "VOID",
                "CREDITED",
                name="finance_invoice_status",
            ),
            nullable=False,
            server_default="DRAFT",
        ),
        sa.Column("description", sa.String(500), nullable=False, server_default=""),
        sa.Column("journal_entry_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["customer_id"], ["finance_customers.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["fiscal_period_id"], ["finance_fiscal_periods.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["journal_entry_id"], ["finance_journal_entries.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "invoice_number",
            name="uq_finance_customer_invoices_tenant_number",
        ),
    )
    op.create_index(
        "ix_finance_customer_invoices_tenant_id",
        "finance_customer_invoices",
        ["tenant_id"],
    )
    op.create_index(
        "ix_finance_customer_invoices_customer_id",
        "finance_customer_invoices",
        ["customer_id"],
    )
    op.create_index(
        "ix_finance_customer_invoices_fiscal_period_id",
        "finance_customer_invoices",
        ["fiscal_period_id"],
    )

    op.create_table(
        "finance_customer_invoice_lines",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("invoice_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("line_number", sa.Integer(), nullable=False),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("quantity", sa.Numeric(24, 6), nullable=False),
        sa.Column("unit_price", sa.Numeric(24, 6), nullable=False),
        sa.Column("discount_amount", sa.Numeric(24, 6), nullable=False, server_default="0"),
        sa.Column("tax_rate", sa.Numeric(12, 6), nullable=False, server_default="0"),
        sa.Column("tax_amount", sa.Numeric(24, 6), nullable=False, server_default="0"),
        sa.Column("line_total", sa.Numeric(24, 6), nullable=False, server_default="0"),
        sa.Column("revenue_account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["invoice_id"], ["finance_customer_invoices.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["revenue_account_id"], ["finance_ledger_accounts.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "invoice_id",
            "line_number",
            name="uq_finance_customer_invoice_lines_number",
        ),
    )

    op.create_table(
        "finance_customer_credit_notes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("invoice_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("fiscal_period_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("credit_note_number", sa.String(100), nullable=False),
        sa.Column("credit_note_date", sa.Date(), nullable=False),
        sa.Column("amount", sa.Numeric(24, 6), nullable=False),
        sa.Column("tax_amount", sa.Numeric(24, 6), nullable=False, server_default="0"),
        sa.Column("total_amount", sa.Numeric(24, 6), nullable=False),
        sa.Column("applied_amount", sa.Numeric(24, 6), nullable=False, server_default="0"),
        sa.Column(
            "status",
            sa.Enum(
                "DRAFT",
                "ISSUED",
                "APPLIED",
                "VOID",
                name="finance_credit_note_status",
            ),
            nullable=False,
            server_default="DRAFT",
        ),
        sa.Column("reason", sa.String(500), nullable=False),
        sa.Column("journal_entry_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["customer_id"], ["finance_customers.id"]),
        sa.ForeignKeyConstraint(["invoice_id"], ["finance_customer_invoices.id"]),
        sa.ForeignKeyConstraint(["fiscal_period_id"], ["finance_fiscal_periods.id"]),
        sa.ForeignKeyConstraint(["journal_entry_id"], ["finance_journal_entries.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "credit_note_number",
            name="uq_finance_customer_credit_notes_tenant_number",
        ),
    )

    op.create_table(
        "finance_customer_receipts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("fiscal_period_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("receipt_number", sa.String(100), nullable=False),
        sa.Column("receipt_date", sa.Date(), nullable=False),
        sa.Column("amount", sa.Numeric(24, 6), nullable=False),
        sa.Column("allocated_amount", sa.Numeric(24, 6), nullable=False, server_default="0"),
        sa.Column("unallocated_amount", sa.Numeric(24, 6), nullable=False),
        sa.Column("currency_code", sa.String(3), nullable=False, server_default="PKR"),
        sa.Column("exchange_rate", sa.Numeric(24, 10), nullable=False, server_default="1"),
        sa.Column(
            "payment_method",
            sa.Enum(
                "CASH",
                "BANK_TRANSFER",
                "CHEQUE",
                "CARD",
                "MOBILE_WALLET",
                "OTHER",
                name="finance_payment_method",
            ),
            nullable=False,
        ),
        sa.Column("reference_number", sa.String(200), nullable=True),
        sa.Column("bank_account_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "DRAFT",
                "POSTED",
                "PARTIALLY_ALLOCATED",
                "ALLOCATED",
                "VOID",
                name="finance_receipt_status",
            ),
            nullable=False,
            server_default="DRAFT",
        ),
        sa.Column("journal_entry_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["customer_id"], ["finance_customers.id"]),
        sa.ForeignKeyConstraint(["fiscal_period_id"], ["finance_fiscal_periods.id"]),
        sa.ForeignKeyConstraint(["journal_entry_id"], ["finance_journal_entries.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "receipt_number",
            name="uq_finance_customer_receipts_tenant_number",
        ),
    )

    op.create_table(
        "finance_receipt_allocations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("receipt_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("invoice_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("allocated_amount", sa.Numeric(24, 6), nullable=False),
        sa.Column("allocated_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("allocated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["receipt_id"], ["finance_customer_receipts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["invoice_id"], ["finance_customer_invoices.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "receipt_id",
            "invoice_id",
            name="uq_finance_receipt_allocations_receipt_invoice",
        ),
    )


def downgrade() -> None:
    op.drop_table("finance_receipt_allocations")
    op.drop_table("finance_customer_receipts")
    op.drop_table("finance_customer_credit_notes")
    op.drop_table("finance_customer_invoice_lines")
    op.drop_table("finance_customer_invoices")
    op.drop_table("finance_customers")
