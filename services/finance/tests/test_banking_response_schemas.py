from datetime import date
from decimal import Decimal
from uuid import uuid4

from finance_service.schemas.banking import (
    DailyBankBalanceRead,
    ReconciliationCompleteRequest,
)


def test_reconciliation_complete_request() -> None:
    payload = ReconciliationCompleteRequest(
        tenant_id=uuid4(),
        completed_by=uuid4(),
    )

    assert payload.completed_by is not None


def test_daily_bank_balance_schema() -> None:
    payload = DailyBankBalanceRead(
        tenant_id=uuid4(),
        bank_account_id=uuid4(),
        as_of_date=date(2026, 8, 6),
        opening_balance=Decimal("1000"),
        credits=Decimal("500"),
        debits=Decimal("250"),
        closing_balance=Decimal("1250"),
    )

    assert payload.closing_balance == Decimal("1250")
