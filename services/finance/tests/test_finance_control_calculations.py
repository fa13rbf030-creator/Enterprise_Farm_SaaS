from decimal import Decimal

import pytest

from finance_service.services.finance_control_calculations import (
    FinanceControlCalculationError,
    calculate_attestation_completion,
    calculate_control_effectiveness,
    calculate_control_health_score,
    calculate_exception_rate,
    calculate_reconciliation_variance,
    calculate_residual_risk_score,
    is_reconciliation_within_tolerance,
)


def test_control_effectiveness():
    assert calculate_control_effectiveness(
        passed_checks=9,
        total_checks=10,
    ) == Decimal("90.00")


def test_control_effectiveness_zero_total():
    assert calculate_control_effectiveness(
        passed_checks=0,
        total_checks=0,
    ) == Decimal("0.00")


def test_exception_rate():
    assert calculate_exception_rate(
        exception_count=5,
        transaction_count=200,
    ) == Decimal("2.50")


def test_residual_risk_score():
    assert calculate_residual_risk_score(
        inherent_risk_score=Decimal("80"),
        control_effectiveness_percentage=Decimal("75"),
    ) == Decimal("20.00")


def test_reconciliation_variance():
    assert calculate_reconciliation_variance(
        source_balance=Decimal("1000"),
        target_balance=Decimal("995"),
    ) == Decimal("5.00")


def test_reconciliation_within_tolerance():
    assert is_reconciliation_within_tolerance(
        source_balance=Decimal("1000"),
        target_balance=Decimal("999.50"),
        tolerance=Decimal("0.50"),
    ) is True


def test_attestation_completion():
    assert calculate_attestation_completion(
        completed_attestations=8,
        required_attestations=10,
    ) == Decimal("80.00")


def test_control_health_score():
    assert calculate_control_health_score(
        effectiveness_percentage=Decimal("90"),
        reconciliation_percentage=Decimal("95"),
        attestation_percentage=Decimal("85"),
    ) == Decimal("90.00")


def test_invalid_effectiveness_counts():
    with pytest.raises(
        FinanceControlCalculationError
    ):
        calculate_control_effectiveness(
            passed_checks=11,
            total_checks=10,
        )


def test_negative_tolerance_rejected():
    with pytest.raises(
        FinanceControlCalculationError
    ):
        is_reconciliation_within_tolerance(
            source_balance=Decimal("100"),
            target_balance=Decimal("100"),
            tolerance=Decimal("-1"),
        )
