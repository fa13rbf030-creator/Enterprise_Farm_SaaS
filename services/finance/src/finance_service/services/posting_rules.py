from __future__ import annotations

from finance_service.core.enums import (
    FiscalPeriodStatus,
    JournalStatus,
)


class PostingRuleError(ValueError):
    pass


def validate_journal_can_post(
    *,
    journal_status: JournalStatus,
    period_status: FiscalPeriodStatus,
) -> None:
    if journal_status != JournalStatus.DRAFT:
        raise PostingRuleError(
            "Only draft journals can be posted"
        )

    if period_status != FiscalPeriodStatus.OPEN:
        raise PostingRuleError(
            "Journal cannot be posted into a closed period"
        )


def validate_journal_can_reverse(
    *,
    journal_status: JournalStatus,
    period_status: FiscalPeriodStatus,
) -> None:
    if journal_status != JournalStatus.POSTED:
        raise PostingRuleError(
            "Only posted journals can be reversed"
        )

    if period_status != FiscalPeriodStatus.OPEN:
        raise PostingRuleError(
            "Journal cannot be reversed in a closed period"
        )


def validate_period_transition(
    *,
    current: FiscalPeriodStatus,
    target: FiscalPeriodStatus,
) -> None:
    allowed = {
        FiscalPeriodStatus.OPEN: {
            FiscalPeriodStatus.SOFT_CLOSED,
            FiscalPeriodStatus.CLOSED,
        },
        FiscalPeriodStatus.SOFT_CLOSED: {
            FiscalPeriodStatus.OPEN,
            FiscalPeriodStatus.CLOSED,
        },
        FiscalPeriodStatus.CLOSED: set(),
    }

    if target == current:
        return

    if target not in allowed[current]:
        raise PostingRuleError(
            f"Invalid fiscal period transition: "
            f"{current.value} -> {target.value}"
        )
