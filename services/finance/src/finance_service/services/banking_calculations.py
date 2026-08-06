from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from finance_service.core.enums import (
    BankStatementLineType,
)
from finance_service.schemas.banking import (
    BankStatementCreate,
)


class BankingCalculationError(ValueError):
    pass


def quantize_bank_money(value: Decimal) -> Decimal:
    return value.quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


def calculate_statement_totals(
    payload: BankStatementCreate,
) -> tuple[Decimal, Decimal, Decimal]:
    credits = Decimal("0")
    debits = Decimal("0")
    line_numbers: set[int] = set()

    for line in payload.lines:
        if line.line_number in line_numbers:
            raise BankingCalculationError(
                "Bank statement line numbers must be unique"
            )

        line_numbers.add(line.line_number)

        if line.line_type == BankStatementLineType.CREDIT:
            credits += line.amount
        else:
            debits += line.amount

    credits = quantize_bank_money(credits)
    debits = quantize_bank_money(debits)

    calculated_closing = quantize_bank_money(
        payload.opening_balance + credits - debits
    )

    if calculated_closing != quantize_bank_money(
        payload.closing_balance
    ):
        raise BankingCalculationError(
            "Bank statement closing balance does not reconcile"
        )

    return credits, debits, calculated_closing


def calculate_reconciliation_difference(
    *,
    book_balance: Decimal,
    statement_balance: Decimal,
    reconciled_amount: Decimal,
) -> Decimal:
    return quantize_bank_money(
        statement_balance
        - book_balance
        - reconciled_amount
    )


def validate_match_amount(
    *,
    statement_line_amount: Decimal,
    existing_matched_amount: Decimal,
    new_matched_amount: Decimal,
) -> Decimal:
    total = quantize_bank_money(
        existing_matched_amount + new_matched_amount
    )

    if total > quantize_bank_money(statement_line_amount):
        raise BankingCalculationError(
            "Reconciliation matches exceed statement-line amount"
        )

    return total
