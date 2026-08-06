from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)

from finance_service.core.enums import (
    FiscalYearCloseStatus,
    OpeningBalanceStatus,
)


class OpeningBalanceLineCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ledger_account_id: UUID
    debit: Decimal = Field(default=Decimal("0"), ge=0)
    credit: Decimal = Field(default=Decimal("0"), ge=0)
    description: str = Field(default="", max_length=500)

    @model_validator(mode="after")
    def validate_amount(self):
        if self.debit > 0 and self.credit > 0:
            raise ValueError(
                "Opening balance line cannot contain "
                "both debit and credit"
            )

        if self.debit == 0 and self.credit == 0:
            raise ValueError(
                "Opening balance line requires an amount"
            )

        return self


class OpeningBalanceBatchCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    fiscal_period_id: UUID
    batch_number: str = Field(
        min_length=1,
        max_length=100,
    )
    description: str = Field(default="", max_length=500)
    created_by: UUID
    lines: list[OpeningBalanceLineCreate] = Field(
        min_length=2
    )


class OpeningBalanceBatchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    fiscal_period_id: UUID
    batch_number: str
    description: str
    status: OpeningBalanceStatus
    total_debit: Decimal
    total_credit: Decimal
    created_by: UUID
    validated_by: UUID | None
    posted_journal_id: UUID | None


class FiscalYearCloseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    retained_earnings_account_id: UUID
    started_by: UUID
    closing_journal_number: str = Field(
        min_length=1,
        max_length=100,
    )


class FiscalYearCloseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    fiscal_year_id: UUID
    retained_earnings_account_id: UUID
    closing_journal_id: UUID | None
    status: FiscalYearCloseStatus
    net_income: Decimal
    started_by: UUID
    error_message: str


class FiscalYearClosePreviewLine(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ledger_account_id: UUID
    account_code: str
    account_name: str
    debit: Decimal
    credit: Decimal


class FiscalYearClosePreview(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    fiscal_year_id: UUID
    revenue_total: Decimal
    expense_total: Decimal
    net_income: Decimal
    lines: list[FiscalYearClosePreviewLine]
