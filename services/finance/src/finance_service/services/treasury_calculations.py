from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from finance_service.core.enums import FraudCheckStatus
from finance_service.schemas.treasury import (
    TreasuryPaymentBatchCreate,
)


class TreasuryCalculationError(ValueError):
    pass


def quantize_treasury_money(value: Decimal) -> Decimal:
    return value.quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


def calculate_payment_batch_total(
    payload: TreasuryPaymentBatchCreate,
) -> tuple[Decimal, int]:
    total = sum(
        (item.amount for item in payload.items),
        Decimal("0"),
    )

    total = quantize_treasury_money(total)

    if total <= 0:
        raise TreasuryCalculationError(
            "Payment batch total must be positive"
        )

    return total, len(payload.items)


def calculate_liquidity_projection(
    *,
    opening_cash: Decimal,
    expected_inflows: Decimal,
    expected_outflows: Decimal,
    minimum_cash_buffer: Decimal,
) -> tuple[Decimal, Decimal]:
    projected_closing = quantize_treasury_money(
        opening_cash
        + expected_inflows
        - expected_outflows
    )

    funding_gap = quantize_treasury_money(
        max(
            minimum_cash_buffer - projected_closing,
            Decimal("0"),
        )
    )

    return projected_closing, funding_gap


def evaluate_basic_payment_fraud(
    *,
    amount: Decimal,
    duplicate_reference: bool,
    beneficiary_changed: bool,
    daily_limit: Decimal,
) -> tuple[FraudCheckStatus, str | None]:
    if duplicate_reference:
        return (
            FraudCheckStatus.BLOCKED,
            "Duplicate payment reference",
        )

    if amount > daily_limit:
        return (
            FraudCheckStatus.REVIEW_REQUIRED,
            "Payment exceeds configured daily limit",
        )

    if beneficiary_changed:
        return (
            FraudCheckStatus.REVIEW_REQUIRED,
            "Beneficiary details recently changed",
        )

    return FraudCheckStatus.PASSED, None
