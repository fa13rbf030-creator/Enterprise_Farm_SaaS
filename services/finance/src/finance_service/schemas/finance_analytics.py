from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)

from finance_service.models.finance_analytics import (
    FinanceAnalyticsPeriodType,
    FinanceAnalyticsSnapshotStatus,
)


class FinanceAnalyticsSnapshotCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    snapshot_number: str = Field(
        min_length=1,
        max_length=64,
    )
    period_type: FinanceAnalyticsPeriodType
    period_start: date
    period_end: date

    currency_code: str = Field(
        min_length=3,
        max_length=3,
    )

    revenue: Decimal = Decimal("0")
    cost_of_goods_sold: Decimal = Decimal("0")
    operating_income: Decimal = Decimal("0")
    net_income: Decimal = Decimal("0")

    interest_expense: Decimal = Decimal("0")
    tax_expense: Decimal = Decimal("0")
    depreciation: Decimal = Decimal("0")
    amortization: Decimal = Decimal("0")

    current_assets: Decimal = Decimal("0")
    current_liabilities: Decimal = Decimal("0")

    cash_and_equivalents: Decimal = Decimal("0")
    marketable_securities: Decimal = Decimal("0")

    accounts_receivable: Decimal = Decimal("0")
    accounts_payable: Decimal = Decimal("0")
    inventory: Decimal = Decimal("0")

    total_assets: Decimal = Decimal("0")
    average_total_assets: Decimal = Decimal("0")

    total_equity: Decimal = Decimal("0")
    average_equity: Decimal = Decimal("0")

    total_debt: Decimal = Decimal("0")

    operating_cash_flow: Decimal = Decimal("0")
    capital_expenditure: Decimal = Decimal("0")

    budget_amount: Decimal = Decimal("0")
    actual_amount: Decimal = Decimal("0")

    credit_sales: Decimal = Decimal("0")
    credit_purchases: Decimal = Decimal("0")

    average_accounts_receivable: Decimal = Decimal("0")
    average_accounts_payable: Decimal = Decimal("0")
    average_inventory: Decimal = Decimal("0")

    days_in_period: int = Field(
        default=365,
        gt=0,
        le=366,
    )

    calculated_by: UUID

    @model_validator(mode="after")
    def validate_period(self):
        if self.period_end < self.period_start:
            raise ValueError(
                "Analytics period end cannot precede start"
            )

        self.currency_code = self.currency_code.upper()

        return self


class FinanceAnalyticsSnapshotRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    snapshot_number: str

    period_type: FinanceAnalyticsPeriodType
    period_start: date
    period_end: date
    currency_code: str

    revenue: Decimal
    cost_of_goods_sold: Decimal
    operating_income: Decimal
    net_income: Decimal
    ebitda: Decimal

    current_assets: Decimal
    current_liabilities: Decimal
    cash_and_equivalents: Decimal

    accounts_receivable: Decimal
    accounts_payable: Decimal
    inventory: Decimal

    total_assets: Decimal
    total_equity: Decimal
    total_debt: Decimal

    operating_cash_flow: Decimal
    capital_expenditure: Decimal

    budget_amount: Decimal
    actual_amount: Decimal

    current_ratio: Decimal | None
    quick_ratio: Decimal | None

    gross_margin_percentage: Decimal | None
    operating_margin_percentage: Decimal | None
    net_margin_percentage: Decimal | None
    ebitda_margin_percentage: Decimal | None

    return_on_assets_percentage: Decimal | None
    return_on_equity_percentage: Decimal | None

    debt_to_equity_ratio: Decimal | None

    dso_days: Decimal | None
    dpo_days: Decimal | None
    inventory_days: Decimal | None
    cash_conversion_cycle_days: Decimal | None

    working_capital: Decimal
    free_cash_flow: Decimal

    budget_utilization_percentage: Decimal | None

    status: FinanceAnalyticsSnapshotStatus

    calculated_by: UUID
    approved_by: UUID | None

    calculated_at: datetime | None
    approved_at: datetime | None

    created_at: datetime
    updated_at: datetime


class FinanceAnalyticsSnapshotApprove(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    approved_by: UUID


class CFOExecutiveDashboardRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    period_start: date
    period_end: date
    currency_code: str

    snapshot_status: FinanceAnalyticsSnapshotStatus

    revenue: Decimal
    net_income: Decimal
    ebitda: Decimal

    gross_margin_percentage: Decimal | None
    net_margin_percentage: Decimal | None
    ebitda_margin_percentage: Decimal | None

    current_ratio: Decimal | None
    quick_ratio: Decimal | None

    working_capital: Decimal
    free_cash_flow: Decimal

    return_on_assets_percentage: Decimal | None
    return_on_equity_percentage: Decimal | None
    debt_to_equity_ratio: Decimal | None

    dso_days: Decimal | None
    dpo_days: Decimal | None
    inventory_days: Decimal | None
    cash_conversion_cycle_days: Decimal | None

    budget_utilization_percentage: Decimal | None
