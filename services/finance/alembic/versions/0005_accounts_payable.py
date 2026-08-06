"""add accounts payable foundation

Revision ID: 0005_finance_ap
Revises: 0004_finance_ar
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0005_finance_ap"
down_revision = "0004_finance_ar"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "finance_vendors",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("vendor_code", sa.String(50), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("email", sa.String(320), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("billing_address", sa.Text(), nullable=False, server_default=""),
        sa.Column("currency_code", sa.String(3), nullable=False, server_default="PKR"),
        sa.Column("payment_terms_days", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("credit_limit", sa.Numeric(24, 6), nullable=False, server_default="0"),
        sa.Column(
            "status",
            sa.Enum(
                "ACTIVE",
                "ON_HOLD",
                "INACTIVE",
                name="finance_vendor_status",
            ),
            nullable=False,
            server_default="ACTIVE",
        ),
        sa.Column("ap_control_account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("default_expense_account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("input_tax_account_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("withholding_tax_account_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_tax_registered", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("tax_registration_number", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["ap_control_account_id"], ["finance_ledger_accounts.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["default_expense_account_id"], ["finance_ledger_accounts.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["input_tax_account_id"], ["finance_ledger_accounts.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["withholding_tax_account_id"], ["finance_ledger_accounts.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "vendor_code",
            name="uq_finance_vendors_tenant_code",
        ),
    )

    op.create_index(
        "ix_finance_vendors_tenant_id",
        "finance_vendors",
        ["tenant_id"],
    )

    op.create_table(
        "finance_supplier_invoices",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("vendor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("fiscal_period_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("invoice_number", sa.String(100), nullable=False),
        sa.Column("vendor_reference", sa.String(200), nullable=True),
        sa.Column("invoice_date", sa.Date(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("currency_code", sa.String(3), nullable=False, server_default="PKR"),
        sa.Column("exchange_rate", sa.Numeric(24, 10), nullable=False, server_default="1"),
        sa.Column("subtotal", sa.Numeric(24, 6), nullable=False, server_default="0"),
        sa.Column("discount_total", sa.Numeric(24, 6), nullable=False, server_default="0"),
        sa.Column("tax_total", sa.Numeric(24, 6), nullable=False, server_default="0"),
        sa.Column("withholding_tax_total", sa.Numeric(24, 6), nullable=False, server_default="0"),
        sa.Column("total_amount", sa.Numeric(24, 6), nullable=False, server_default="0"),
        sa.Column("paid_amount", sa.Numeric(24, 6), nullable=False, server_default="0"),
        sa.Column("debited_amount", sa.Numeric(24, 6), nullable=False, server_default="0"),
        sa.Column("outstanding_amount", sa.Numeric(24, 6), nullable=False, server_default="0"),
        sa.Column(
            "status",
            sa.Enum(
                "DRAFT",
                "POSTED",
                "PARTIALLY_PAID",
                "PAID",
                "VOID",
                "DEBITED",
                name="finance_supplier_invoice_status",
            ),
            nullable=False,
            server_default="DRAFT",
        ),
        sa.Column("description", sa.String(500), nullable=False, server_default=""),
        sa.Column("journal_entry_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("posted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["vendor_id"], ["finance_vendors.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["fiscal_period_id"], ["finance_fiscal_periods.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["journal_entry_id"], ["finance_journal_entries.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "invoice_number",
            name="uq_finance_supplier_invoices_tenant_number",
        ),
    )

    op.create_index(
        "ix_finance_supplier_invoices_tenant_id",
        "finance_supplier_invoices",
        ["tenant_id"],
    )
    op.create_index(
        "ix_finance_supplier_invoices_vendor_id",
        "finance_supplier_invoices",
        ["vendor_id"],
    )
    op.create_index(
        "ix_finance_supplier_invoices_fiscal_period_id",
        "finance_supplier_invoices",
        ["fiscal_period_id"],
    )

    op.create_table(
        "finance_supplier_invoice_lines",
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
        sa.Column("withholding_tax_rate", sa.Numeric(12, 6), nullable=False, server_default="0"),
        sa.Column("withholding_tax_amount", sa.Numeric(24, 6), nullable=False, server_default="0"),
        sa.Column("line_total", sa.Numeric(24, 6), nullable=False, server_default="0"),
        sa.Column("expense_account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["invoice_id"], ["finance_supplier_invoices.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["expense_account_id"], ["finance_ledger_accounts.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "invoice_id",
            "line_number",
            name="uq_finance_supplier_invoice_lines_number",
        ),
    )

    op.create_table(
        "finance_vendor_debit_notes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("vendor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("invoice_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("fiscal_period_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("debit_note_number", sa.String(100), nullable=False),
        sa.Column("debit_note_date", sa.Date(), nullable=False),
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
                name="finance_debit_note_status",
            ),
            nullable=False,
            server_default="DRAFT",
        ),
        sa.Column("reason", sa.String(500), nullable=False),
        sa.Column("journal_entry_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["vendor_id"], ["finance_vendors.id"]),
        sa.ForeignKeyConstraint(["invoice_id"], ["finance_supplier_invoices.id"]),
        sa.ForeignKeyConstraint(["fiscal_period_id"], ["finance_fiscal_periods.id"]),
        sa.ForeignKeyConstraint(["journal_entry_id"], ["finance_journal_entries.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "debit_note_number",
            name="uq_finance_vendor_debit_notes_tenant_number",
        ),
    )

    op.create_table(
        "finance_vendor_payments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("vendor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("fiscal_period_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("payment_number", sa.String(100), nullable=False),
        sa.Column("payment_date", sa.Date(), nullable=False),
        sa.Column("amount", sa.Numeric(24, 6), nullable=False),
        sa.Column("allocated_amount", sa.Numeric(24, 6), nullable=False, server_default="0"),
        sa.Column("unallocated_amount", sa.Numeric(24, 6), nullable=False),
        sa.Column("currency_code", sa.String(3), nullable=False, server_default="PKR"),
        sa.Column("exchange_rate", sa.Numeric(24, 10), nullable=False, server_default="1"),
        sa.Column(
            "payment_method",
            postgresql.ENUM(
                "CASH",
                "BANK_TRANSFER",
                "CHEQUE",
                "CARD",
                "MOBILE_WALLET",
                "OTHER",
                name="finance_payment_method",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("reference_number", sa.String(200), nullable=True),
        sa.Column("cash_account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "DRAFT",
                "POSTED",
                "PARTIALLY_ALLOCATED",
                "ALLOCATED",
                "VOID",
                name="finance_vendor_payment_status",
            ),
            nullable=False,
            server_default="DRAFT",
        ),
        sa.Column("journal_entry_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["vendor_id"], ["finance_vendors.id"]),
        sa.ForeignKeyConstraint(["fiscal_period_id"], ["finance_fiscal_periods.id"]),
        sa.ForeignKeyConstraint(["cash_account_id"], ["finance_ledger_accounts.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["journal_entry_id"], ["finance_journal_entries.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "payment_number",
            name="uq_finance_vendor_payments_tenant_number",
        ),
    )

    op.create_table(
        "finance_vendor_payment_allocations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("payment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("invoice_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("allocated_amount", sa.Numeric(24, 6), nullable=False),
        sa.Column("allocated_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("allocated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["payment_id"], ["finance_vendor_payments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["invoice_id"], ["finance_supplier_invoices.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "payment_id",
            "invoice_id",
            name=(
                "uq_finance_vendor_payment_allocations_"
                "payment_invoice"
            ),
        ),
    )


def downgrade() -> None:
    op.drop_table("finance_vendor_payment_allocations")
    op.drop_table("finance_vendor_payments")
    op.drop_table("finance_vendor_debit_notes")
    op.drop_table("finance_supplier_invoice_lines")
    op.drop_table("finance_supplier_invoices")
    op.drop_table("finance_vendors")
