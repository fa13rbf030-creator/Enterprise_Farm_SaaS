from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)

from finance_service.core.enums import (
    AccountStatus,
    AccountType,
    JournalSource,
    JournalStatus,
    NormalBalance,
)


class LedgerAccountCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    parent_id: UUID | None = None
    code: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    account_type: AccountType
    normal_balance: NormalBalance
    currency_code: str = Field(
        default="PKR",
        min_length=3,
        max_length=3,
    )
    is_control_account: bool = False
    allows_manual_posting: bool = True


class LedgerAccountRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    parent_id: UUID | None
    code: str
    name: str
    description: str
    account_type: AccountType
    normal_balance: NormalBalance
    status: AccountStatus
    currency_code: str
    is_control_account: bool
    allows_manual_posting: bool


class FiscalYearCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    name: str = Field(min_length=1, max_length=100)
    starts_on: date
    ends_on: date

    @model_validator(mode="after")
    def validate_dates(self):
        if self.ends_on < self.starts_on:
            raise ValueError(
                "Fiscal year end date cannot precede start date"
            )
        return self


class FiscalPeriodCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    fiscal_year_id: UUID
    period_number: int = Field(ge=1, le=99)
    name: str = Field(min_length=1, max_length=100)
    starts_on: date
    ends_on: date

    @model_validator(mode="after")
    def validate_dates(self):
        if self.ends_on < self.starts_on:
            raise ValueError(
                "Fiscal period end date cannot precede start date"
            )
        return self


class JournalLineCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ledger_account_id: UUID
    line_number: int = Field(ge=1)
    description: str = Field(default="", max_length=500)
    debit: Decimal = Field(default=Decimal("0"), ge=0)
    credit: Decimal = Field(default=Decimal("0"), ge=0)
    currency_code: str = Field(
        default="PKR",
        min_length=3,
        max_length=3,
    )
    exchange_rate: Decimal = Field(
        default=Decimal("1"),
        gt=0,
    )

    @model_validator(mode="after")
    def validate_debit_credit(self):
        if self.debit > 0 and self.credit > 0:
            raise ValueError(
                "Journal line cannot contain both debit and credit"
            )

        if self.debit == 0 and self.credit == 0:
            raise ValueError(
                "Journal line must contain debit or credit"
            )

        return self


class JournalEntryCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    fiscal_period_id: UUID
    journal_number: str = Field(
        min_length=1,
        max_length=100,
    )
    entry_date: date
    source: JournalSource = JournalSource.MANUAL
    source_reference: str | None = Field(
        default=None,
        max_length=200,
    )
    description: str = Field(min_length=1, max_length=2000)
    created_by: UUID
    lines: list[JournalLineCreate] = Field(min_length=2)


class JournalEntryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    fiscal_period_id: UUID
    journal_number: str
    entry_date: date
    source: JournalSource
    source_reference: str | None
    description: str
    status: JournalStatus
    total_debit: Decimal
    total_credit: Decimal
    created_by: UUID
    posted_by: UUID | None


class FiscalYearRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    name: str
    starts_on: date
    ends_on: date
    is_closed: bool


class FiscalPeriodRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    fiscal_year_id: UUID
    period_number: int
    name: str
    starts_on: date
    ends_on: date
    status: str


class JournalLineRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    journal_entry_id: UUID
    ledger_account_id: UUID
    line_number: int
    description: str
    debit: Decimal
    credit: Decimal
    currency_code: str
    exchange_rate: Decimal
    base_debit: Decimal
    base_credit: Decimal


class JournalDetailRead(JournalEntryRead):
    lines: list[JournalLineRead]
