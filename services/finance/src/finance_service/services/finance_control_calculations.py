from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP


class FinanceControlCalculationError(ValueError):
    pass


def quantize_control_percentage(
    value: Decimal,
) -> Decimal:
    return value.quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


def calculate_control_effectiveness(
    *,
    passed_checks: int,
    total_checks: int,
) -> Decimal:
    if passed_checks < 0 or total_checks < 0:
        raise FinanceControlCalculationError(
            "Control check counts cannot be negative"
        )

    if passed_checks > total_checks:
        raise FinanceControlCalculationError(
            "Passed checks cannot exceed total checks"
        )

    if total_checks == 0:
        return Decimal("0.00")

    return quantize_control_percentage(
        Decimal(passed_checks)
        * Decimal("100")
        / Decimal(total_checks)
    )


def calculate_exception_rate(
    *,
    exception_count: int,
    transaction_count: int,
) -> Decimal:
    if exception_count < 0 or transaction_count < 0:
        raise FinanceControlCalculationError(
            "Counts cannot be negative"
        )

    if exception_count > transaction_count:
        raise FinanceControlCalculationError(
            "Exceptions cannot exceed transactions"
        )

    if transaction_count == 0:
        return Decimal("0.00")

    return quantize_control_percentage(
        Decimal(exception_count)
        * Decimal("100")
        / Decimal(transaction_count)
    )


def calculate_residual_risk_score(
    *,
    inherent_risk_score: Decimal,
    control_effectiveness_percentage: Decimal,
) -> Decimal:
    if inherent_risk_score < 0:
        raise FinanceControlCalculationError(
            "Inherent risk score cannot be negative"
        )

    if (
        control_effectiveness_percentage < 0
        or control_effectiveness_percentage > 100
    ):
        raise FinanceControlCalculationError(
            "Control effectiveness must be between 0 and 100"
        )

    residual = (
        inherent_risk_score
        * (
            Decimal("100")
            - control_effectiveness_percentage
        )
        / Decimal("100")
    )

    return quantize_control_percentage(residual)


def calculate_reconciliation_variance(
    *,
    source_balance: Decimal,
    target_balance: Decimal,
) -> Decimal:
    return (source_balance - target_balance).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


def is_reconciliation_within_tolerance(
    *,
    source_balance: Decimal,
    target_balance: Decimal,
    tolerance: Decimal,
) -> bool:
    if tolerance < 0:
        raise FinanceControlCalculationError(
            "Tolerance cannot be negative"
        )

    variance = abs(
        calculate_reconciliation_variance(
            source_balance=source_balance,
            target_balance=target_balance,
        )
    )

    return variance <= tolerance


def calculate_attestation_completion(
    *,
    completed_attestations: int,
    required_attestations: int,
) -> Decimal:
    if (
        completed_attestations < 0
        or required_attestations < 0
    ):
        raise FinanceControlCalculationError(
            "Attestation counts cannot be negative"
        )

    if completed_attestations > required_attestations:
        raise FinanceControlCalculationError(
            "Completed attestations cannot exceed required attestations"
        )

    if required_attestations == 0:
        return Decimal("0.00")

    return quantize_control_percentage(
        Decimal(completed_attestations)
        * Decimal("100")
        / Decimal(required_attestations)
    )


def calculate_control_health_score(
    *,
    effectiveness_percentage: Decimal,
    reconciliation_percentage: Decimal,
    attestation_percentage: Decimal,
) -> Decimal:
    for name, value in (
        ("effectiveness", effectiveness_percentage),
        ("reconciliation", reconciliation_percentage),
        ("attestation", attestation_percentage),
    ):
        if value < 0 or value > 100:
            raise FinanceControlCalculationError(
                f"{name} percentage must be between 0 and 100"
            )

    return quantize_control_percentage(
        (
            effectiveness_percentage
            + reconciliation_percentage
            + attestation_percentage
        )
        / Decimal("3")
    )
