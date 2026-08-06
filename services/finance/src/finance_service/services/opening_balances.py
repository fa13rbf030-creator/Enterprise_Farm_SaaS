from __future__ import annotations

from decimal import Decimal

from finance_service.schemas.closing import (
    OpeningBalanceBatchCreate,
)


class OpeningBalanceValidationError(ValueError):
    pass


def calculate_opening_balance_totals(
    payload: OpeningBalanceBatchCreate,
) -> tuple[Decimal, Decimal]:
    total_debit = Decimal("0")
    total_credit = Decimal("0")
    account_ids = set()

    for line in payload.lines:
        if line.ledger_account_id in account_ids:
            raise OpeningBalanceValidationError(
                "Opening balance accounts must be unique"
            )

        account_ids.add(line.ledger_account_id)
        total_debit += line.debit
        total_credit += line.credit

    return total_debit, total_credit


def validate_opening_balance_batch(
    payload: OpeningBalanceBatchCreate,
) -> tuple[Decimal, Decimal]:
    total_debit, total_credit = (
        calculate_opening_balance_totals(payload)
    )

    if total_debit <= 0:
        raise OpeningBalanceValidationError(
            "Opening balance total must be greater than zero"
        )

    if total_debit != total_credit:
        raise OpeningBalanceValidationError(
            "Opening balance batch is not balanced"
        )

    return total_debit, total_credit
