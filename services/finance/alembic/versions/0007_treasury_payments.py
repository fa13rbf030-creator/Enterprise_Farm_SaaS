"""add treasury payment and liquidity foundation

Revision ID: 0007_finance_treasury
Revises: 0006_finance_banking
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0007_finance_treasury"
down_revision = "0006_finance_banking"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "finance_treasury_payment_batches",
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
        sa.Column("batch_number", sa.String(100), nullable=False),
        sa.Column("batch_date", sa.Date(), nullable=False),
        sa.Column("execution_date", sa.Date(), nullable=False),
        sa.Column(
            "bank_account_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "currency_code",
            sa.String(3),
            nullable=False,
            server_default="PKR",
        ),
        sa.Column(
            "total_amount",
            sa.Numeric(24, 6),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "item_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "status",
            sa.Enum(
                "DRAFT",
                "PENDING_APPROVAL",
                "APPROVED",
                "REJECTED",
                "GENERATED",
                "SUBMITTED",
                "PARTIALLY_SETTLED",
                "SETTLED",
                "FAILED",
                "CANCELLED",
                name="finance_treasury_batch_status",
            ),
            nullable=False,
            server_default="DRAFT",
        ),
        sa.Column(
            "file_format",
            sa.Enum(
                "ISO20022_PAIN_001",
                "CSV",
                "FIXED_WIDTH",
                "BANK_API",
                name="finance_treasury_file_format",
            ),
            nullable=False,
            server_default="ISO20022_PAIN_001",
        ),
        sa.Column("payment_file_name", sa.String(500)),
        sa.Column("payment_file_hash", sa.String(128)),
        sa.Column("external_submission_id", sa.String(200)),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "approved_by",
            postgresql.UUID(as_uuid=True),
        ),
        sa.Column(
            "submitted_at",
            sa.DateTime(timezone=True),
        ),
        sa.Column(
            "settled_at",
            sa.DateTime(timezone=True),
        ),
        sa.Column(
            "notes",
            sa.Text(),
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
            ["bank_account_id"],
            ["finance_bank_accounts.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "batch_number",
            name="uq_finance_treasury_batch_tenant_number",
        ),
    )

    op.create_index(
        "ix_finance_treasury_payment_batches_tenant_id",
        "finance_treasury_payment_batches",
        ["tenant_id"],
    )

    op.create_table(
        "finance_treasury_payment_items",
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
        sa.Column("line_number", sa.Integer(), nullable=False),
        sa.Column(
            "vendor_id",
            postgresql.UUID(as_uuid=True),
        ),
        sa.Column(
            "vendor_payment_id",
            postgresql.UUID(as_uuid=True),
        ),
        sa.Column(
            "payment_reference",
            sa.String(200),
            nullable=False,
        ),
        sa.Column(
            "beneficiary_name",
            sa.String(200),
            nullable=False,
        ),
        sa.Column(
            "beneficiary_account",
            sa.String(100),
            nullable=False,
        ),
        sa.Column(
            "beneficiary_iban",
            sa.String(100),
        ),
        sa.Column(
            "beneficiary_bank_code",
            sa.String(100),
        ),
        sa.Column(
            "amount",
            sa.Numeric(24, 6),
            nullable=False,
        ),
        sa.Column(
            "currency_code",
            sa.String(3),
            nullable=False,
            server_default="PKR",
        ),
        sa.Column(
            "status",
            sa.Enum(
                "PENDING",
                "APPROVED",
                "REJECTED",
                "SUBMITTED",
                "SETTLED",
                "FAILED",
                "CANCELLED",
                name="finance_treasury_item_status",
            ),
            nullable=False,
            server_default="PENDING",
        ),
        sa.Column(
            "fraud_check_status",
            sa.Enum(
                "PASSED",
                "REVIEW_REQUIRED",
                "BLOCKED",
                name="finance_fraud_check_status",
            ),
            nullable=False,
            server_default="PASSED",
        ),
        sa.Column("fraud_reason", sa.String(500)),
        sa.Column("settlement_reference", sa.String(200)),
        sa.Column(
            "settlement_status",
            sa.Enum(
                "PENDING",
                "CONFIRMED",
                "REJECTED",
                "RETURNED",
                name="finance_settlement_status",
            ),
            nullable=False,
            server_default="PENDING",
        ),
        sa.Column("failure_reason", sa.String(500)),
        sa.ForeignKeyConstraint(
            ["batch_id"],
            ["finance_treasury_payment_batches.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["vendor_id"],
            ["finance_vendors.id"],
        ),
        sa.ForeignKeyConstraint(
            ["vendor_payment_id"],
            ["finance_vendor_payments.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "batch_id",
            "line_number",
            name="uq_finance_treasury_item_batch_line",
        ),
        sa.UniqueConstraint(
            "tenant_id",
            "payment_reference",
            name="uq_finance_treasury_item_tenant_reference",
        ),
    )

    op.create_table(
        "finance_treasury_batch_approvals",
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
            "approver_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "decision",
            sa.Enum(
                "APPROVED",
                "REJECTED",
                name="finance_treasury_approval_decision",
            ),
            nullable=False,
        ),
        sa.Column(
            "comments",
            sa.String(1000),
            nullable=False,
            server_default="",
        ),
        sa.Column(
            "decided_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["batch_id"],
            ["finance_treasury_payment_batches.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "batch_id",
            "approver_id",
            name="uq_finance_treasury_approval_batch_user",
        ),
    )

    op.create_table(
        "finance_liquidity_forecasts",
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
        sa.Column("forecast_date", sa.Date(), nullable=False),
        sa.Column("horizon_days", sa.Integer(), nullable=False),
        sa.Column(
            "currency_code",
            sa.String(3),
            nullable=False,
        ),
        sa.Column(
            "scenario",
            sa.Enum(
                "BASE",
                "CONSERVATIVE",
                "STRESS",
                name="finance_liquidity_forecast_scenario",
            ),
            nullable=False,
        ),
        sa.Column(
            "opening_cash",
            sa.Numeric(24, 6),
            nullable=False,
        ),
        sa.Column(
            "expected_inflows",
            sa.Numeric(24, 6),
            nullable=False,
        ),
        sa.Column(
            "expected_outflows",
            sa.Numeric(24, 6),
            nullable=False,
        ),
        sa.Column(
            "projected_closing_cash",
            sa.Numeric(24, 6),
            nullable=False,
        ),
        sa.Column(
            "minimum_cash_buffer",
            sa.Numeric(24, 6),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "funding_gap",
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
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "forecast_date",
            "currency_code",
            "scenario",
            name="uq_finance_liquidity_forecast_scope",
        ),
    )


def downgrade() -> None:
    op.drop_table("finance_liquidity_forecasts")
    op.drop_table("finance_treasury_batch_approvals")
    op.drop_table("finance_treasury_payment_items")
    op.drop_table("finance_treasury_payment_batches")
