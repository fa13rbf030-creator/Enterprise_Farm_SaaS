from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from finance_service.schemas.gl import (
    JournalEntryCreate,
)


class JournalValidationError(ValueError):
    pass


def quantize_amount(
    amount: Decimal,
    *,
    decimal_places: int = 2,
) -> Decimal:
    quantum = Decimal("1").scaleb(-decimal_places)

    return amount.quantize(
        quantum,
        rounding=ROUND_HALF_UP,
    )


def calculate_base_amount(
    amount: Decimal,
    exchange_rate: Decimal,
    *,
    decimal_places: int = 2,
) -> Decimal:
    return quantize_amount(
        amount * exchange_rate,
        decimal_places=decimal_places,
    )


def calculate_journal_totals(
    journal: JournalEntryCreate,
    *,
    decimal_places: int = 2,
) -> tuple[Decimal, Decimal]:
    total_debit = Decimal("0")
    total_credit = Decimal("0")

    seen_line_numbers: set[int] = set()

    for line in journal.lines:
        if line.line_number in seen_line_numbers:
            raise JournalValidationError(
                "Journal line numbers must be unique"
            )

        seen_line_numbers.add(line.line_number)

        total_debit += calculate_base_amount(
            line.debit,
            line.exchange_rate,
            decimal_places=decimal_places,
        )
        total_credit += calculate_base_amount(
            line.credit,
            line.exchange_rate,
            decimal_places=decimal_places,
        )

    return (
        quantize_amount(
            total_debit,
            decimal_places=decimal_places,
        ),
        quantize_amount(
            total_credit,
            decimal_places=decimal_places,
        ),
    )


def validate_balanced_journal(
    journal: JournalEntryCreate,
    *,
    decimal_places: int = 2,
) -> tuple[Decimal, Decimal]:
    total_debit, total_credit = calculate_journal_totals(
        journal,
        decimal_places=decimal_places,
    )

    if total_debit <= 0:
        raise JournalValidationError(
            "Journal total must be greater than zero"
        )

    if total_debit != total_credit:
        raise JournalValidationError(
            "Journal entry is not balanced"
        )

    return total_debit, total_credit
