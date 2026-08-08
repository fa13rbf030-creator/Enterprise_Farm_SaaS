from datetime import date
from decimal import Decimal
from uuid import uuid4

from finance_service.models.finance_analytics import (
    FinanceAnalyticsSnapshotStatus,
)
from finance_service.schemas.finance_analytics import (
    CFOExecutiveDashboardRead,
)


def test_cfo_dashboard_schema() -> None:
    dashboard = CFOExecutiveDashboardRead(
        tenant_id=uuid4(),
        period_start=date(2026, 8, 1),
        period_end=date(2026, 8, 31),
        currency_code="PKR",
        snapshot_status=(
            FinanceAnalyticsSnapshotStatus.APPROVED
        ),
        revenue=Decimal("1000"),
        net_income=Decimal("180"),
        ebitda=Decimal("250"),
        gross_margin_percentage=Decimal("40"),
        net_margin_percentage=Decimal("18"),
        ebitda_margin_percentage=Decimal("25"),
        current_ratio=Decimal("2"),
        quick_ratio=Decimal("1.5"),
        working_capital=Decimal("400"),
        free_cash_flow=Decimal("300"),
        return_on_assets_percentage=Decimal("10"),
        return_on_equity_percentage=Decimal("20"),
        debt_to_equity_ratio=Decimal("0.6"),
        dso_days=Decimal("36.5"),
        dpo_days=Decimal("36.5"),
        inventory_days=Decimal("73"),
        cash_conversion_cycle_days=Decimal("73"),
        budget_utilization_percentage=Decimal("75"),
    )

    assert dashboard.currency_code == "PKR"
    assert dashboard.revenue == Decimal("1000")
    assert (
        dashboard.snapshot_status
        == FinanceAnalyticsSnapshotStatus.APPROVED
    )
