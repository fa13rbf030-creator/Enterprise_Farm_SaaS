from decimal import Decimal
from uuid import uuid4

import pytest

from finance_service.schemas.closing import (
    OpeningBalanceBatchCreate,
    OpeningBalanceLineCreate,
)
from finance_service.services.opening_balances import (
    OpeningBalanceValidationError,
    validate_opening_balance_batch,
)


def build_batch(
    debit: Decimal = Decimal("100"),
    credit: Decimal = Decimal("100"),
) -> OpeningBalanceBatchCreate:
    return OpeningBalanceBatchCreate(
        tenant_id=uuid4(),
        fiscal_period_id=uuid4(),
        batch_number="OB-001",
        created_by=uuid4(),
        lines=[
            OpeningBalanceLineCreate(
                ledger_account_id=uuid4(),
                debit=debit,
            ),
            OpeningBalanceLineCreate(
                ledger_account_id=uuid4(),
                credit=credit,
            ),
        ],
    )


def test_balanced_opening_batch() -> None:
    debit, credit = validate_opening_balance_batch(
        build_batch()
    )

    assert debit == Decimal("100")
    assert credit == Decimal("100")


def test_unbalanced_opening_batch_rejected() -> None:
    with pytest.raises(
        OpeningBalanceValidationError,
        match="not balanced",
    ):
        validate_opening_balance_batch(
            build_batch(
                debit=Decimal("100"),
                credit=Decimal("90"),
            )
        )


def test_duplicate_accounts_rejected() -> None:
    account_id = uuid4()
    payload = build_batch()

    payload.lines[0].ledger_account_id = account_id
    payload.lines[1].ledger_account_id = account_id

    with pytest.raises(
        OpeningBalanceValidationError,
        match="must be unique",
    ):
        validate_opening_balance_batch(payload)
