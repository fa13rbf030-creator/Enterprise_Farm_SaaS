from uuid import uuid4

from finance_service.schemas.posting import (
    JournalPostRequest,
    JournalReverseRequest,
    PeriodStatusUpdate,
)
from finance_service.core.enums import FiscalPeriodStatus


def test_journal_post_request() -> None:
    payload = JournalPostRequest(
        tenant_id=uuid4(),
        posted_by=uuid4(),
    )

    assert payload.posted_by is not None


def test_journal_reverse_request() -> None:
    payload = JournalReverseRequest(
        tenant_id=uuid4(),
        reversed_by=uuid4(),
        reversal_journal_number="REV-001",
        reversal_description="Correction",
    )

    assert payload.reversal_journal_number == "REV-001"


def test_period_status_update() -> None:
    payload = PeriodStatusUpdate(
        tenant_id=uuid4(),
        status=FiscalPeriodStatus.SOFT_CLOSED,
    )

    assert (
        payload.status
        == FiscalPeriodStatus.SOFT_CLOSED
    )
