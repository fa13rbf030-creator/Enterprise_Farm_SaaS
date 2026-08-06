from datetime import date
from decimal import Decimal
from uuid import uuid4

from finance_service.core.enums import JournalStatus
from finance_service.schemas.inquiry import (
    JournalSearchItem,
    LedgerInquiryLine,
)


def test_journal_search_item() -> None:
    item = JournalSearchItem(
        id=uuid4(),
        journal_number="JV-001",
        entry_date=date(2026, 1, 1),
        description="Journal",
        status=JournalStatus.POSTED,
        total_debit=Decimal("100"),
        total_credit=Decimal("100"),
    )

    assert item.status == JournalStatus.POSTED


def test_ledger_inquiry_line() -> None:
    line = LedgerInquiryLine(
        journal_id=uuid4(),
        journal_number="JV-001",
        entry_date=date(2026, 1, 1),
        description="Journal",
        line_description="Cash",
        debit=Decimal("100"),
        credit=Decimal("0"),
        running_debit=Decimal("100"),
        running_credit=Decimal("0"),
        status=JournalStatus.POSTED,
    )

    assert line.running_debit == Decimal("100")
