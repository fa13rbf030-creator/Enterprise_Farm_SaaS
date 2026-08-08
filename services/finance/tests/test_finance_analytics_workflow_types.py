from finance_service.models.finance_analytics import (
    FinanceAnalyticsSnapshotStatus,
)


def test_snapshot_workflow_statuses() -> None:
    assert (
        FinanceAnalyticsSnapshotStatus.DRAFT.value
        == "DRAFT"
    )
    assert (
        FinanceAnalyticsSnapshotStatus.CALCULATED.value
        == "CALCULATED"
    )
    assert (
        FinanceAnalyticsSnapshotStatus.APPROVED.value
        == "APPROVED"
    )
    assert (
        FinanceAnalyticsSnapshotStatus.SUPERSEDED.value
        == "SUPERSEDED"
    )
