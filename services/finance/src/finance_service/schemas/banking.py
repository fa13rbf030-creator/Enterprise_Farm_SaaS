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
    BankAccountStatus,
    BankAccountType,
    BankStatementLineType,
    BankStatementStatus,
    ReconciliationMatchType,
    ReconciliationStatus,
)


class BankAccountCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    account_code: str = Field(min_length=1, max_length=50)
    account_name: str = Field(min_length=1, max_length=200)
    bank_name: str = Field(min_length=1, max_length=200)
    branch_name: str = Field(default="", max_length=200)
    branch_code: str | None = Field(default=None, max_length=50)
    account_number: str = Field(min_length=1, max_length=100)
    iban: str | None = Field(default=None, max_length=100)
    swift_code: str | None = Field(default=None, max_length=50)
    currency_code: str = Field(
        default="PKR",
        min_length=3,
        max_length=3,
    )
    account_type: BankAccountType
    ledger_account_id: UUID
    opening_balance: Decimal = Decimal("0")
    description: str = Field(default="", max_length=2000)
    created_by: UUID


class BankAccountRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    account_code: str
    account_name: str
    bank_name: str
    branch_name: str
    account_number: str
    iban: str | None
    currency_code: str
    account_type: BankAccountType
    status: BankAccountStatus
    ledger_account_id: UUID
    opening_balance: Decimal
    current_balance: Decimal


class BankStatementLineCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    line_number: int = Field(ge=1)
    transaction_date: date
    value_date: date | None = None
    reference_number: str | None = Field(
        default=None,
        max_length=200,
    )
    description: str = Field(min_length=1, max_length=1000)
    line_type: BankStatementLineType
    amount: Decimal = Field(gt=0)
    running_balance: Decimal | None = None


class BankStatementCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    bank_account_id: UUID
    statement_number: str = Field(
        min_length=1,
        max_length=100,
    )
    statement_date: date
    period_start: date
    period_end: date
    opening_balance: Decimal
    closing_balance: Decimal
    source_file_name: str | None = Field(
        default=None,
        max_length=500,
    )
    imported_by: UUID
    lines: list[BankStatementLineCreate] = Field(
        min_length=1
    )

    @model_validator(mode="after")
    def validate_period(self):
        if self.period_end < self.period_start:
            raise ValueError(
                "Statement period end cannot precede start"
            )

        if not (
            self.period_start
            <= self.statement_date
            <= self.period_end
        ):
            raise ValueError(
                "Statement date must fall inside statement period"
            )

        return self


class BankStatementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    bank_account_id: UUID
    statement_number: str
    statement_date: date
    period_start: date
    period_end: date
    opening_balance: Decimal
    closing_balance: Decimal
    total_credits: Decimal
    total_debits: Decimal
    status: BankStatementStatus
    source_file_name: str | None


class BankStatementLineRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    statement_id: UUID
    line_number: int
    transaction_date: date
    value_date: date | None
    reference_number: str | None
    description: str
    line_type: BankStatementLineType
    amount: Decimal
    running_balance: Decimal | None
    is_reconciled: bool
    matched_journal_entry_id: UUID | None


class BankStatementDetailRead(BankStatementRead):
    lines: list[BankStatementLineRead]


class ReconciliationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    bank_account_id: UUID
    statement_id: UUID
    reconciliation_date: date
    book_balance: Decimal
    started_by: UUID
    notes: str = Field(default="", max_length=2000)


class ReconciliationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    bank_account_id: UUID
    statement_id: UUID
    reconciliation_date: date
    book_balance: Decimal
    statement_balance: Decimal
    reconciled_amount: Decimal
    difference_amount: Decimal
    status: ReconciliationStatus
    started_by: UUID
    completed_by: UUID | None


class ReconciliationMatchCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    statement_line_id: UUID
    journal_entry_id: UUID | None = None
    match_type: ReconciliationMatchType
    matched_amount: Decimal = Field(gt=0)
    matched_by: UUID


class CashPositionRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    currency_code: str
    total_balance: Decimal
    accounts: list[BankAccountRead]


class ReconciliationCompleteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    completed_by: UUID


class BankAdjustmentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    fiscal_period_id: UUID
    transaction_date: date
    offset_account_id: UUID
    journal_number: str = Field(
        min_length=1,
        max_length=100,
    )
    posted_by: UUID
    description: str = Field(
        min_length=1,
        max_length=500,
    )


class ReconciliationMatchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    reconciliation_id: UUID
    statement_line_id: UUID
    journal_entry_id: UUID | None
    match_type: ReconciliationMatchType
    matched_amount: Decimal
    matched_by: UUID


class ReconciliationDetailRead(ReconciliationRead):
    matches: list[ReconciliationMatchRead]


class DailyBankBalanceRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    bank_account_id: UUID
    as_of_date: date
    opening_balance: Decimal
    credits: Decimal
    debits: Decimal
    closing_balance: Decimal
