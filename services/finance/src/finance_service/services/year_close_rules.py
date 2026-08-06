from __future__ import annotations

from finance_service.core.enums import (
    AccountType,
    FiscalPeriodStatus,
    FiscalYearCloseStatus,
)


class FiscalYearCloseRuleError(ValueError):
    pass


def validate_year_can_close(
    *,
    period_statuses: list[FiscalPeriodStatus],
    current_status: FiscalYearCloseStatus,
) -> None:
    if current_status == FiscalYearCloseStatus.CLOSED:
        raise FiscalYearCloseRuleError(
            "Fiscal year is already closed"
        )

    if not period_statuses:
        raise FiscalYearCloseRuleError(
            "Fiscal year has no accounting periods"
        )

    if any(
        status != FiscalPeriodStatus.CLOSED
        for status in period_statuses
    ):
        raise FiscalYearCloseRuleError(
            "All fiscal periods must be closed"
        )


def is_temporary_account(
    account_type: AccountType,
) -> bool:
    return account_type in {
        AccountType.REVENUE,
        AccountType.EXPENSE,
    }
