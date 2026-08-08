from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from finance_service.models.finance_analytics import (
    FinanceAnalyticsSnapshot,
    FinanceAnalyticsSnapshotStatus,
)
from finance_service.repositories.finance_analytics import (
    get_finance_analytics_snapshot,
    get_latest_finance_analytics_snapshot,
)
from finance_service.schemas.finance_analytics import (
    CFOExecutiveDashboardRead,
    FinanceAnalyticsSnapshotApprove,
    FinanceAnalyticsSnapshotCreate,
)
from finance_service.services.finance_analytics_calculations import (
    calculate_budget_utilization_percentage,
    calculate_cash_conversion_cycle,
    calculate_debt_to_equity_ratio,
    calculate_dpo,
    calculate_dso,
    calculate_ebitda,
    calculate_ebitda_margin_percentage,
    calculate_free_cash_flow,
    calculate_gross_margin_percentage,
    calculate_inventory_days,
    calculate_net_margin_percentage,
    calculate_operating_margin_percentage,
    calculate_quick_ratio,
    calculate_return_on_assets_percentage,
    calculate_return_on_equity_percentage,
    calculate_working_capital,
)
from finance_service.services.financial_reporting_calculations import (
    calculate_current_ratio,
)


class FinanceAnalyticsWorkflowError(ValueError):
    pass


def _calculate_ccc(
    *,
    inventory_days: Decimal | None,
    dso: Decimal | None,
    dpo: Decimal | None,
) -> Decimal | None:
    if (
        inventory_days is None
        or dso is None
        or dpo is None
    ):
        return None

    return calculate_cash_conversion_cycle(
        inventory_days=inventory_days,
        dso=dso,
        dpo=dpo,
    )


async def create_finance_analytics_snapshot(
    session: AsyncSession,
    *,
    payload: FinanceAnalyticsSnapshotCreate,
) -> FinanceAnalyticsSnapshot:
    ebitda = calculate_ebitda(
        net_income=payload.net_income,
        interest_expense=payload.interest_expense,
        tax_expense=payload.tax_expense,
        depreciation=payload.depreciation,
        amortization=payload.amortization,
    )

    current_ratio = calculate_current_ratio(
        current_assets=payload.current_assets,
        current_liabilities=payload.current_liabilities,
    )

    quick_ratio = calculate_quick_ratio(
        cash_and_equivalents=payload.cash_and_equivalents,
        marketable_securities=payload.marketable_securities,
        accounts_receivable=payload.accounts_receivable,
        current_liabilities=payload.current_liabilities,
    )

    gross_margin = calculate_gross_margin_percentage(
        revenue=payload.revenue,
        cost_of_goods_sold=payload.cost_of_goods_sold,
    )

    operating_margin = calculate_operating_margin_percentage(
        revenue=payload.revenue,
        operating_income=payload.operating_income,
    )

    net_margin = calculate_net_margin_percentage(
        revenue=payload.revenue,
        net_income=payload.net_income,
    )

    ebitda_margin = calculate_ebitda_margin_percentage(
        revenue=payload.revenue,
        ebitda=ebitda,
    )

    roa = calculate_return_on_assets_percentage(
        net_income=payload.net_income,
        average_total_assets=payload.average_total_assets,
    )

    roe = calculate_return_on_equity_percentage(
        net_income=payload.net_income,
        average_equity=payload.average_equity,
    )

    debt_to_equity = calculate_debt_to_equity_ratio(
        total_debt=payload.total_debt,
        total_equity=payload.total_equity,
    )

    dso = calculate_dso(
        average_accounts_receivable=(
            payload.average_accounts_receivable
        ),
        credit_sales=payload.credit_sales,
        days_in_period=payload.days_in_period,
    )

    dpo = calculate_dpo(
        average_accounts_payable=(
            payload.average_accounts_payable
        ),
        credit_purchases=payload.credit_purchases,
        days_in_period=payload.days_in_period,
    )

    inventory_days = calculate_inventory_days(
        average_inventory=payload.average_inventory,
        cost_of_goods_sold=payload.cost_of_goods_sold,
        days_in_period=payload.days_in_period,
    )

    ccc = _calculate_ccc(
        inventory_days=inventory_days,
        dso=dso,
        dpo=dpo,
    )

    working_capital = calculate_working_capital(
        current_assets=payload.current_assets,
        current_liabilities=payload.current_liabilities,
    )

    free_cash_flow = calculate_free_cash_flow(
        operating_cash_flow=payload.operating_cash_flow,
        capital_expenditure=payload.capital_expenditure,
    )

    budget_utilization = calculate_budget_utilization_percentage(
        actual_amount=payload.actual_amount,
        budget_amount=payload.budget_amount,
    )

    obj = FinanceAnalyticsSnapshot(
        tenant_id=payload.tenant_id,
        snapshot_number=payload.snapshot_number.strip(),
        period_type=payload.period_type,
        period_start=payload.period_start,
        period_end=payload.period_end,
        currency_code=payload.currency_code.upper(),
        revenue=payload.revenue,
        cost_of_goods_sold=payload.cost_of_goods_sold,
        operating_income=payload.operating_income,
        net_income=payload.net_income,
        ebitda=ebitda,
        current_assets=payload.current_assets,
        current_liabilities=payload.current_liabilities,
        cash_and_equivalents=payload.cash_and_equivalents,
        accounts_receivable=payload.accounts_receivable,
        accounts_payable=payload.accounts_payable,
        inventory=payload.inventory,
        total_assets=payload.total_assets,
        total_equity=payload.total_equity,
        total_debt=payload.total_debt,
        operating_cash_flow=payload.operating_cash_flow,
        capital_expenditure=payload.capital_expenditure,
        budget_amount=payload.budget_amount,
        actual_amount=payload.actual_amount,
        current_ratio=current_ratio,
        quick_ratio=quick_ratio,
        gross_margin_percentage=gross_margin,
        operating_margin_percentage=operating_margin,
        net_margin_percentage=net_margin,
        ebitda_margin_percentage=ebitda_margin,
        return_on_assets_percentage=roa,
        return_on_equity_percentage=roe,
        debt_to_equity_ratio=debt_to_equity,
        dso_days=dso,
        dpo_days=dpo,
        inventory_days=inventory_days,
        cash_conversion_cycle_days=ccc,
        working_capital=working_capital,
        free_cash_flow=free_cash_flow,
        budget_utilization_percentage=budget_utilization,
        status=FinanceAnalyticsSnapshotStatus.CALCULATED,
        calculated_by=payload.calculated_by,
        calculated_at=datetime.now(timezone.utc),
    )

    session.add(obj)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise FinanceAnalyticsWorkflowError(
            "Finance analytics snapshot already exists "
            "for this number or period"
        ) from exc

    await session.refresh(obj)
    return obj


async def approve_finance_analytics_snapshot(
    session: AsyncSession,
    *,
    snapshot_id: UUID,
    payload: FinanceAnalyticsSnapshotApprove,
) -> FinanceAnalyticsSnapshot:
    snapshot = await get_finance_analytics_snapshot(
        session,
        tenant_id=payload.tenant_id,
        snapshot_id=snapshot_id,
        for_update=True,
    )

    if snapshot is None:
        raise FinanceAnalyticsWorkflowError(
            "Finance analytics snapshot not found"
        )

    if snapshot.status != FinanceAnalyticsSnapshotStatus.CALCULATED:
        raise FinanceAnalyticsWorkflowError(
            "Only calculated analytics snapshots can be approved"
        )

    if snapshot.calculated_by == payload.approved_by:
        raise FinanceAnalyticsWorkflowError(
            "Snapshot calculator cannot approve own snapshot"
        )

    snapshot.status = FinanceAnalyticsSnapshotStatus.APPROVED
    snapshot.approved_by = payload.approved_by
    snapshot.approved_at = datetime.now(timezone.utc)

    await session.commit()
    await session.refresh(snapshot)

    return snapshot


async def build_cfo_executive_dashboard(
    session: AsyncSession,
    *,
    tenant_id: UUID,
) -> CFOExecutiveDashboardRead:
    snapshot = await get_latest_finance_analytics_snapshot(
        session,
        tenant_id=tenant_id,
        approved_only=True,
    )

    if snapshot is None:
        raise FinanceAnalyticsWorkflowError(
            "Approved finance analytics snapshot not found"
        )

    return CFOExecutiveDashboardRead(
        tenant_id=snapshot.tenant_id,
        period_start=snapshot.period_start,
        period_end=snapshot.period_end,
        currency_code=snapshot.currency_code,
        snapshot_status=snapshot.status,
        revenue=snapshot.revenue,
        net_income=snapshot.net_income,
        ebitda=snapshot.ebitda,
        gross_margin_percentage=(
            snapshot.gross_margin_percentage
        ),
        net_margin_percentage=(
            snapshot.net_margin_percentage
        ),
        ebitda_margin_percentage=(
            snapshot.ebitda_margin_percentage
        ),
        current_ratio=snapshot.current_ratio,
        quick_ratio=snapshot.quick_ratio,
        working_capital=snapshot.working_capital,
        free_cash_flow=snapshot.free_cash_flow,
        return_on_assets_percentage=(
            snapshot.return_on_assets_percentage
        ),
        return_on_equity_percentage=(
            snapshot.return_on_equity_percentage
        ),
        debt_to_equity_ratio=(
            snapshot.debt_to_equity_ratio
        ),
        dso_days=snapshot.dso_days,
        dpo_days=snapshot.dpo_days,
        inventory_days=snapshot.inventory_days,
        cash_conversion_cycle_days=(
            snapshot.cash_conversion_cycle_days
        ),
        budget_utilization_percentage=(
            snapshot.budget_utilization_percentage
        ),
    )
