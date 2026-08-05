import pytest

from finance_service.core.enums import (
    FiscalPeriodStatus,
    JournalStatus,
)
from finance_service.services.posting_rules import (
    PostingRuleError,
    validate_journal_can_post,
    validate_journal_can_reverse,
    validate_period_transition,
)


def test_draft_journal_can_post_in_open_period() -> None:
    validate_journal_can_post(
        journal_status=JournalStatus.DRAFT,
        period_status=FiscalPeriodStatus.OPEN,
    )


def test_posted_journal_cannot_post_again() -> None:
    with pytest.raises(
        PostingRuleError,
        match="Only draft journals",
    ):
        validate_journal_can_post(
            journal_status=JournalStatus.POSTED,
            period_status=FiscalPeriodStatus.OPEN,
        )


def test_posted_journal_can_reverse() -> None:
    validate_journal_can_reverse(
        journal_status=JournalStatus.POSTED,
        period_status=FiscalPeriodStatus.OPEN,
    )


def test_closed_period_cannot_reopen() -> None:
    with pytest.raises(
        PostingRuleError,
        match="Invalid fiscal period transition",
    ):
        validate_period_transition(
            current=FiscalPeriodStatus.CLOSED,
            target=FiscalPeriodStatus.OPEN,
        )


def test_soft_closed_period_can_reopen() -> None:
    validate_period_transition(
        current=FiscalPeriodStatus.SOFT_CLOSED,
        target=FiscalPeriodStatus.OPEN,
    )
