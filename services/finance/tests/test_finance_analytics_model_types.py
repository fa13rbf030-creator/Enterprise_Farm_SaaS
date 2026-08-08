from finance_service.models.finance_analytics import (
    FinanceAnalyticsPeriodType,
    FinanceAnalyticsSnapshot,
    FinanceAnalyticsSnapshotStatus,
)


def test_finance_analytics_period_types() -> None:
    assert FinanceAnalyticsPeriodType.DAILY.value == "DAILY"
    assert FinanceAnalyticsPeriodType.MONTHLY.value == "MONTHLY"
    assert FinanceAnalyticsPeriodType.QUARTERLY.value == "QUARTERLY"
    assert FinanceAnalyticsPeriodType.YEARLY.value == "YEARLY"


def test_finance_analytics_snapshot_statuses() -> None:
    assert FinanceAnalyticsSnapshotStatus.DRAFT.value == "DRAFT"
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


def test_finance_analytics_snapshot_table_name() -> None:
    assert (
        FinanceAnalyticsSnapshot.__tablename__
        == "finance_analytics_snapshots"
    )


def test_finance_analytics_snapshot_has_core_kpis() -> None:
    columns = FinanceAnalyticsSnapshot.__table__.columns

    required = {
        "revenue",
        "net_income",
        "ebitda",
        "current_ratio",
        "quick_ratio",
        "gross_margin_percentage",
        "net_margin_percentage",
        "return_on_assets_percentage",
        "return_on_equity_percentage",
        "debt_to_equity_ratio",
        "dso_days",
        "dpo_days",
        "inventory_days",
        "cash_conversion_cycle_days",
        "working_capital",
        "free_cash_flow",
        "budget_utilization_percentage",
    }

    assert required.issubset(set(columns.keys()))
