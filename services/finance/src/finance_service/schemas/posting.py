from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from finance_service.core.enums import (
    BalanceDirection,
    FiscalPeriodStatus,
    JournalStatus,
)


class JournalPostRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    posted_by: UUID


class JournalReverseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    reversed_by: UUID
    reversal_journal_number: str = Field(
        min_length=1,
        max_length=100,
    )
    reversal_description: str = Field(
        min_length=1,
        max_length=2000,
    )


class PeriodStatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    status: FiscalPeriodStatus


class AccountBalanceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ledger_account_id: UUID
    fiscal_period_id: UUID
    opening_debit: Decimal
    opening_credit: Decimal
    period_debit: Decimal
    period_credit: Decimal
    closing_debit: Decimal
    closing_credit: Decimal


class TrialBalanceLine(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ledger_account_id: UUID
    account_code: str
    account_name: str
    debit: Decimal
    credit: Decimal
    direction: BalanceDirection


class TrialBalanceRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    fiscal_period_id: UUID
    total_debit: Decimal
    total_credit: Decimal
    is_balanced: bool
    lines: list[TrialBalanceLine]


class JournalStatusRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    status: JournalStatus
