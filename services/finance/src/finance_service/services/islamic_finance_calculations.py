from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP


MONEY_QUANTUM = Decimal("0.01")
RATE_DIVISOR = Decimal("100")


class IslamicFinanceCalculationError(ValueError):
    pass


def quantize_islamic_money(
    value: Decimal,
) -> Decimal:
    return value.quantize(
        MONEY_QUANTUM,
        rounding=ROUND_HALF_UP,
    )


def is_nisab_met(
    *,
    zakatable_base: Decimal,
    nisab_value: Decimal,
) -> bool:
    if zakatable_base < 0:
        raise IslamicFinanceCalculationError(
            "Zakatable base cannot be negative"
        )

    if nisab_value < 0:
        raise IslamicFinanceCalculationError(
            "Nisab value cannot be negative"
        )

    return zakatable_base >= nisab_value


def is_hawl_complete(
    *,
    holding_days: int,
    required_hawl_days: int,
) -> bool:
    if holding_days < 0:
        raise IslamicFinanceCalculationError(
            "Holding days cannot be negative"
        )

    if required_hawl_days <= 0:
        raise IslamicFinanceCalculationError(
            "Required Hawl days must be positive"
        )

    return holding_days >= required_hawl_days


def calculate_zakatable_base(
    *,
    eligible_assets: Decimal,
    deductible_liabilities: Decimal = Decimal("0"),
) -> Decimal:
    if eligible_assets < 0:
        raise IslamicFinanceCalculationError(
            "Eligible assets cannot be negative"
        )

    if deductible_liabilities < 0:
        raise IslamicFinanceCalculationError(
            "Deductible liabilities cannot be negative"
        )

    return quantize_islamic_money(
        max(
            Decimal("0"),
            eligible_assets - deductible_liabilities,
        )
    )


def calculate_monetary_zakat(
    *,
    zakatable_base: Decimal,
    nisab_value: Decimal,
    rate_percentage: Decimal,
    hawl_complete: bool,
) -> Decimal:
    if zakatable_base < 0:
        raise IslamicFinanceCalculationError(
            "Zakatable base cannot be negative"
        )

    if nisab_value < 0:
        raise IslamicFinanceCalculationError(
            "Nisab value cannot be negative"
        )

    if (
        rate_percentage < 0
        or rate_percentage > 100
    ):
        raise IslamicFinanceCalculationError(
            "Zakat rate must be between 0 and 100"
        )

    if not hawl_complete:
        return Decimal("0.00")

    if not is_nisab_met(
        zakatable_base=zakatable_base,
        nisab_value=nisab_value,
    ):
        return Decimal("0.00")

    return quantize_islamic_money(
        zakatable_base
        * rate_percentage
        / RATE_DIVISOR
    )


def calculate_crop_ushr(
    *,
    eligible_crop_output_value: Decimal,
    rate_percentage: Decimal,
) -> Decimal:
    if eligible_crop_output_value < 0:
        raise IslamicFinanceCalculationError(
            "Eligible crop output value cannot be negative"
        )

    if (
        rate_percentage < 0
        or rate_percentage > 100
    ):
        raise IslamicFinanceCalculationError(
            "Ushr rate must be between 0 and 100"
        )

    return quantize_islamic_money(
        eligible_crop_output_value
        * rate_percentage
        / RATE_DIVISOR
    )


def calculate_livestock_assessment_value(
    *,
    eligible_count: int,
    unit_assessment_value: Decimal,
) -> Decimal:
    if eligible_count < 0:
        raise IslamicFinanceCalculationError(
            "Eligible livestock count cannot be negative"
        )

    if unit_assessment_value < 0:
        raise IslamicFinanceCalculationError(
            "Unit assessment value cannot be negative"
        )

    return quantize_islamic_money(
        Decimal(eligible_count)
        * unit_assessment_value
    )


def calculate_sadaqah_amount(
    *,
    voluntary_amount: Decimal,
) -> Decimal:
    if voluntary_amount < 0:
        raise IslamicFinanceCalculationError(
            "Sadaqah amount cannot be negative"
        )

    return quantize_islamic_money(
        voluntary_amount
    )
