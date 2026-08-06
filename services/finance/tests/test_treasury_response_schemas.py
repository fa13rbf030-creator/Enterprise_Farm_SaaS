from decimal import Decimal
from uuid import uuid4

from finance_service.schemas.treasury import (
    TreasuryDashboardRead,
    TreasuryFraudReviewRead,
)


def test_treasury_fraud_review_schema() -> None:
    result = TreasuryFraudReviewRead(
        batch_id=uuid4(),
        passed=2,
        review_required=1,
        blocked=0,
        can_submit_for_approval=True,
    )

    assert result.can_submit_for_approval is True


def test_treasury_dashboard_schema() -> None:
    dashboard = TreasuryDashboardRead(
        tenant_id=uuid4(),
        draft_batches=1,
        pending_approval_batches=2,
        approved_batches=3,
        submitted_batches=4,
        settled_batches=5,
        failed_batches=0,
        total_pending_amount=Decimal("1000"),
        total_submitted_amount=Decimal("500"),
    )

    assert dashboard.settled_batches == 5
