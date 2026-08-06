from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from finance_service.core.enums import (
    BankAccountType,
    BankStatementLineType,
)
from finance_service.schemas.banking import (
    BankAccountCreate,
    BankStatementCreate,
    BankStatementLineCreate,
)


def test_bank_account_schema() -> None:
    payload = BankAccountCreate(
        tenant_id=uuid4(),
        account_code="BANK-01",
        account_name="Main Bank",
        bank_name="Example Bank",
        account_number="123456",
        account_type=BankAccountType.CURRENT,
        ledger_account_id=uuid4(),
        created_by=uuid4(),
    )

    assert payload.currency_code == "PKR"


def test_invalid_statement_period() -> None:
    with pytest.raises(ValidationError):
        BankStatementCreate(
            tenant_id=uuid4(),
            bank_account_id=uuid4(),
            statement_number="ST-1",
            statement_date=date(2026, 1, 15),
            period_start=date(2026, 2, 1),
            period_end=date(2026, 1, 1),
            opening_balance=Decimal("0"),
            closing_balance=Decimal("100"),
            imported_by=uuid4(),
            lines=[
                BankStatementLineCreate(
                    line_number=1,
                    transaction_date=date(2026, 1, 1),
                    description="Deposit",
                    line_type=(
                        BankStatementLineType.CREDIT
                    ),
                    amount=Decimal("100"),
                )
            ],
        )
