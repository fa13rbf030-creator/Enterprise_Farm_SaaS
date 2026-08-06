from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from finance_service.core.enums import JournalStatus


class LedgerInquiryLine(BaseModel):
    model_config = ConfigDict(extra="forbid")

    journal_id: UUID
    journal_number: str
    entry_date: date
    description: str
    line_description: str
    debit: Decimal
    credit: Decimal
    running_debit: Decimal
    running_credit: Decimal
    status: JournalStatus


class LedgerInquiryRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    ledger_account_id: UUID
    account_code: str
    account_name: str
    opening_debit: Decimal
    opening_credit: Decimal
    period_debit: Decimal
    period_credit: Decimal
    closing_debit: Decimal
    closing_credit: Decimal
    lines: list[LedgerInquiryLine]


class JournalSearchItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    journal_number: str
    entry_date: date
    description: str
    status: JournalStatus
    total_debit: Decimal
    total_credit: Decimal
