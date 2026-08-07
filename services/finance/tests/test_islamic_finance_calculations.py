from decimal import Decimal

import pytest

from finance_service.services.islamic_finance_calculations import (
    IslamicFinanceCalculationError,
    calculate_crop_ushr,
    calculate_livestock_assessment_value,
    calculate_monetary_zakat,
    calculate_sadaqah_amount,
    calculate_zakatable_base,
    is_hawl_complete,
    is_nisab_met,
)


def test_zakatable_base_deducts_configured_liabilities():
    assert calculate_zakatable_base(
        eligible_assets=Decimal("1000000"),
        deductible_liabilities=Decimal("200000"),
    ) == Decimal("800000.00")


def test_zakatable_base_cannot_be_negative():
    assert calculate_zakatable_base(
        eligible_assets=Decimal("100000"),
        deductible_liabilities=Decimal("150000"),
    ) == Decimal("0.00")


def test_nisab_met():
    assert is_nisab_met(
        zakatable_base=Decimal("1000000"),
        nisab_value=Decimal("900000"),
    ) is True


def test_nisab_not_met():
    assert is_nisab_met(
        zakatable_base=Decimal("800000"),
        nisab_value=Decimal("900000"),
    ) is False


def test_hawl_complete_uses_configured_days():
    assert is_hawl_complete(
        holding_days=355,
        required_hawl_days=354,
    ) is True


def test_monetary_zakat_with_configured_rate():
    assert calculate_monetary_zakat(
        zakatable_base=Decimal("1000000"),
        nisab_value=Decimal("500000"),
        rate_percentage=Decimal("2.5"),
        hawl_complete=True,
    ) == Decimal("25000.00")


def test_zakat_zero_when_nisab_not_met():
    assert calculate_monetary_zakat(
        zakatable_base=Decimal("400000"),
        nisab_value=Decimal("500000"),
        rate_percentage=Decimal("2.5"),
        hawl_complete=True,
    ) == Decimal("0.00")


def test_zakat_zero_when_hawl_incomplete():
    assert calculate_monetary_zakat(
        zakatable_base=Decimal("1000000"),
        nisab_value=Decimal("500000"),
        rate_percentage=Decimal("2.5"),
        hawl_complete=False,
    ) == Decimal("0.00")


def test_crop_ushr_uses_configured_rate():
    assert calculate_crop_ushr(
        eligible_crop_output_value=Decimal("500000"),
        rate_percentage=Decimal("10"),
    ) == Decimal("50000.00")


def test_livestock_assessment_value():
    assert calculate_livestock_assessment_value(
        eligible_count=40,
        unit_assessment_value=Decimal("75000"),
    ) == Decimal("3000000.00")


def test_sadaqah_is_voluntary_amount():
    assert calculate_sadaqah_amount(
        voluntary_amount=Decimal("12345.67"),
    ) == Decimal("12345.67")


def test_invalid_zakat_rate_rejected():
    with pytest.raises(
        IslamicFinanceCalculationError
    ):
        calculate_monetary_zakat(
            zakatable_base=Decimal("1000"),
            nisab_value=Decimal("500"),
            rate_percentage=Decimal("101"),
            hawl_complete=True,
        )


def test_invalid_ushr_rate_rejected():
    with pytest.raises(
        IslamicFinanceCalculationError
    ):
        calculate_crop_ushr(
            eligible_crop_output_value=Decimal("1000"),
            rate_percentage=Decimal("-1"),
        )
