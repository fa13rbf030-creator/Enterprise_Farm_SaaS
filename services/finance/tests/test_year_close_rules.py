import pytest

from finance_service.core.enums import (
    AccountType,
    FiscalPeriodStatus,
    FiscalYearCloseStatus,
)
from finance_service.services.year_close_rules import (
    FiscalYearCloseRuleError,
    is_temporary_account,
    validate_year_can_close,
)


def test_year_can_close_when_all_periods_closed() -> None:
    validate_year_can_close(
        period_statuses=[
            FiscalPeriodStatus.CLOSED,
            FiscalPeriodStatus.CLOSED,
        ],
        current_status=FiscalYearCloseStatus.OPEN,
    )


def test_open_period_blocks_year_close() -> None:
    with pytest.raises(
        FiscalYearCloseRuleError,
        match="All fiscal periods must be closed",
    ):
        validate_year_can_close(
            period_statuses=[
                FiscalPeriodStatus.CLOSED,
                FiscalPeriodStatus.OPEN,
            ],
            current_status=FiscalYearCloseStatus.OPEN,
        )


def test_revenue_and_expense_are_temporary() -> None:
    assert is_temporary_account(AccountType.REVENUE)
    assert is_temporary_account(AccountType.EXPENSE)
    assert not is_temporary_account(AccountType.ASSET)
