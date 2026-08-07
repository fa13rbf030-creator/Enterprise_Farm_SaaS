from decimal import Decimal

import pytest

from finance_service.services.tax_compliance_calculations import (
    calculate_effective_tax_rate,
    calculate_net_tax_liability,
    calculate_percentage_tax,
    calculate_return_variance,
    calculate_withholding_tax,
    quantize_tax_money,
)


def test_quantize_tax_money():
    assert quantize_tax_money(
        Decimal("10.125")
    ) == Decimal("10.13")


def test_percentage_tax():
    assert calculate_percentage_tax(
        Decimal("1000"),
        Decimal("18"),
    ) == Decimal("180.00")


def test_withholding_tax():
    assert calculate_withholding_tax(
        Decimal("2500"),
        Decimal("5"),
    ) == Decimal("125.00")


def test_percentage_tax_rejects_negative_base():
    with pytest.raises(
        ValueError,
        match="Taxable amount cannot be negative",
    ):
        calculate_percentage_tax(
            Decimal("-1"),
            Decimal("18"),
        )


def test_percentage_tax_rejects_invalid_rate():
    with pytest.raises(
        ValueError,
        match="Tax rate must be between 0 and 100",
    ):
        calculate_percentage_tax(
            Decimal("100"),
            Decimal("101"),
        )


def test_net_tax_liability():
    result = calculate_net_tax_liability(
        output_tax=Decimal("1000"),
        input_tax=Decimal("650"),
        adjustments=Decimal("25"),
        credits=Decimal("10"),
    )

    assert result == Decimal("365.00")


def test_net_tax_liability_can_be_refund():
    result = calculate_net_tax_liability(
        output_tax=Decimal("500"),
        input_tax=Decimal("750"),
    )

    assert result == Decimal("-250.00")


def test_return_variance():
    assert calculate_return_variance(
        ledger_amount=Decimal("1200"),
        return_amount=Decimal("1180"),
    ) == Decimal("20.00")


def test_effective_tax_rate():
    assert calculate_effective_tax_rate(
        tax_amount=Decimal("180"),
        taxable_amount=Decimal("1000"),
    ) == Decimal("18.00")


def test_effective_tax_rate_zero_base():
    assert calculate_effective_tax_rate(
        tax_amount=Decimal("0"),
        taxable_amount=Decimal("0"),
    ) == Decimal("0.00")
