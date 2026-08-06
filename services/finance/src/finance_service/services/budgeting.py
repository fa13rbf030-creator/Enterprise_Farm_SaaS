from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from finance_service.core.enums import (
    BudgetStatus,
    BudgetVersionStatus,
)
from finance_service.models.budgeting import (
    FinanceBudget,
    FinanceBudgetLine,
    FinanceBudgetVersion,
    FinanceCostAllocationRule,
    FinanceCostCentre,
    FinanceCostVariance,
    FinanceProfitCentre,
    FinanceStandardCost,
)
from finance_service.repositories.budgeting import (
    get_budget,
    get_cost_centre,
    get_latest_budget_version,
    get_profit_centre,
    list_budget_lines,
)
from finance_service.schemas.budgeting import (
    BudgetApprovalRequest,
    BudgetCreate,
    BudgetDetailRead,
    CostAllocationRuleCreate,
    CostCentreCreate,
    CostVarianceCreate,
    ProfitCentreCreate,
    StandardCostCreate,
)
from finance_service.services.budget_calculations import (
    calculate_budget_line_amount,
    calculate_budget_variance,
    calculate_standard_cost,
)


class BudgetWorkflowError(ValueError):
    pass


async def create_cost_centre(
    session: AsyncSession,
    *,
    payload: CostCentreCreate,
) -> FinanceCostCentre:
    if payload.parent_id is not None:
        parent = await get_cost_centre(
            session,
            tenant_id=payload.tenant_id,
            cost_centre_id=payload.parent_id,
        )

        if parent is None:
            raise BudgetWorkflowError(
                "Parent cost centre not found"
            )

    cost_centre = FinanceCostCentre(
        tenant_id=payload.tenant_id,
        code=payload.code.strip(),
        name=payload.name.strip(),
        object_type=payload.object_type,
        parent_id=payload.parent_id,
        external_reference=payload.external_reference,
        manager_id=payload.manager_id,
        description=payload.description.strip(),
    )

    session.add(cost_centre)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise BudgetWorkflowError(
            "Cost-centre code already exists"
        ) from exc

    await session.refresh(cost_centre)
    return cost_centre


async def create_profit_centre(
    session: AsyncSession,
    *,
    payload: ProfitCentreCreate,
) -> FinanceProfitCentre:
    if payload.parent_id is not None:
        parent = await get_profit_centre(
            session,
            tenant_id=payload.tenant_id,
            profit_centre_id=payload.parent_id,
        )

        if parent is None:
            raise BudgetWorkflowError(
                "Parent profit centre not found"
            )

    profit_centre = FinanceProfitCentre(
        tenant_id=payload.tenant_id,
        code=payload.code.strip(),
        name=payload.name.strip(),
        object_type=payload.object_type,
        parent_id=payload.parent_id,
        external_reference=payload.external_reference,
        manager_id=payload.manager_id,
    )

    session.add(profit_centre)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise BudgetWorkflowError(
            "Profit-centre code already exists"
        ) from exc

    await session.refresh(profit_centre)
    return profit_centre


async def create_budget(
    session: AsyncSession,
    *,
    payload: BudgetCreate,
) -> FinanceBudget:
    total_amount = Decimal("0")

    budget = FinanceBudget(
        tenant_id=payload.tenant_id,
        budget_number=payload.budget_number.strip(),
        name=payload.name.strip(),
        budget_type=payload.budget_type,
        fiscal_year_id=payload.fiscal_year_id,
        scenario=payload.scenario,
        currency_code=payload.currency_code.upper(),
        starts_on=payload.starts_on,
        ends_on=payload.ends_on,
        total_amount=Decimal("0"),
        created_by=payload.created_by,
        notes=payload.notes.strip(),
    )

    session.add(budget)
    await session.flush()

    version = FinanceBudgetVersion(
        tenant_id=payload.tenant_id,
        budget_id=budget.id,
        version_number=1,
        version_name=payload.version_name.strip(),
        status=BudgetVersionStatus.DRAFT,
        total_amount=Decimal("0"),
        created_by=payload.created_by,
    )

    session.add(version)
    await session.flush()

    for line_payload in payload.lines:
        amount = (
            line_payload.amount
            if line_payload.amount is not None
            else calculate_budget_line_amount(
                quantity=line_payload.quantity,
                unit_rate=line_payload.unit_rate,
            )
        )

        if line_payload.cost_centre_id is not None:
            cost_centre = await get_cost_centre(
                session,
                tenant_id=payload.tenant_id,
                cost_centre_id=line_payload.cost_centre_id,
            )

            if cost_centre is None:
                raise BudgetWorkflowError(
                    "Budget line cost centre not found"
                )

        if line_payload.profit_centre_id is not None:
            profit_centre = await get_profit_centre(
                session,
                tenant_id=payload.tenant_id,
                profit_centre_id=line_payload.profit_centre_id,
            )

            if profit_centre is None:
                raise BudgetWorkflowError(
                    "Budget line profit centre not found"
                )

        session.add(
            FinanceBudgetLine(
                tenant_id=payload.tenant_id,
                version_id=version.id,
                line_number=line_payload.line_number,
                ledger_account_id=line_payload.ledger_account_id,
                fiscal_period_id=line_payload.fiscal_period_id,
                cost_centre_id=line_payload.cost_centre_id,
                profit_centre_id=line_payload.profit_centre_id,
                object_type=line_payload.object_type,
                object_reference=line_payload.object_reference,
                quantity=line_payload.quantity,
                unit_rate=line_payload.unit_rate,
                amount=amount,
                description=line_payload.description.strip(),
            )
        )

        total_amount += amount

    budget.total_amount = total_amount
    version.total_amount = total_amount

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise BudgetWorkflowError(
            "Budget number or budget-line number already exists"
        ) from exc

    await session.refresh(budget)
    return budget


async def get_budget_detail(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    budget_id: UUID,
) -> BudgetDetailRead:
    budget = await get_budget(
        session,
        tenant_id=tenant_id,
        budget_id=budget_id,
    )

    if budget is None:
        raise BudgetWorkflowError("Budget not found")

    version = await get_latest_budget_version(
        session,
        tenant_id=tenant_id,
        budget_id=budget_id,
    )

    if version is None:
        raise BudgetWorkflowError(
            "Budget version not found"
        )

    lines = await list_budget_lines(
        session,
        tenant_id=tenant_id,
        version_id=version.id,
    )

    return BudgetDetailRead(
        **budget.__dict__,
        version=version,
        lines=lines,
    )


async def submit_budget_for_approval(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    budget_id: UUID,
    submitted_by: UUID,
) -> FinanceBudget:
    budget = await get_budget(
        session,
        tenant_id=tenant_id,
        budget_id=budget_id,
        for_update=True,
    )

    if budget is None:
        raise BudgetWorkflowError("Budget not found")

    if budget.status != BudgetStatus.DRAFT:
        raise BudgetWorkflowError(
            "Only draft budgets can be submitted"
        )

    if budget.created_by != submitted_by:
        raise BudgetWorkflowError(
            "Only budget creator can submit budget"
        )

    budget.status = BudgetStatus.PENDING_APPROVAL

    await session.commit()
    await session.refresh(budget)

    return budget


async def decide_budget_approval(
    session: AsyncSession,
    *,
    budget_id: UUID,
    payload: BudgetApprovalRequest,
) -> FinanceBudget:
    budget = await get_budget(
        session,
        tenant_id=payload.tenant_id,
        budget_id=budget_id,
        for_update=True,
    )

    if budget is None:
        raise BudgetWorkflowError("Budget not found")

    if budget.status != BudgetStatus.PENDING_APPROVAL:
        raise BudgetWorkflowError(
            "Budget is not pending approval"
        )

    if budget.created_by == payload.approved_by:
        raise BudgetWorkflowError(
            "Budget creator cannot approve own budget"
        )

    version = await get_latest_budget_version(
        session,
        tenant_id=payload.tenant_id,
        budget_id=budget.id,
    )

    if version is None:
        raise BudgetWorkflowError(
            "Budget version not found"
        )

    if payload.approve:
        budget.status = BudgetStatus.APPROVED
        budget.approved_by = payload.approved_by
        version.status = BudgetVersionStatus.BASELINE
    else:
        budget.status = BudgetStatus.REJECTED
        version.status = BudgetVersionStatus.DRAFT

    await session.commit()
    await session.refresh(budget)

    return budget


async def create_standard_cost(
    session: AsyncSession,
    *,
    payload: StandardCostCreate,
) -> FinanceStandardCost:
    total = calculate_standard_cost(
        material_cost=payload.material_cost,
        labour_cost=payload.labour_cost,
        overhead_cost=payload.overhead_cost,
    )

    record = FinanceStandardCost(
        tenant_id=payload.tenant_id,
        object_type=payload.object_type,
        object_reference=payload.object_reference.strip(),
        costing_method=payload.costing_method,
        material_cost=payload.material_cost,
        labour_cost=payload.labour_cost,
        overhead_cost=payload.overhead_cost,
        total_standard_cost=total,
        effective_from=payload.effective_from,
        effective_to=payload.effective_to,
    )

    session.add(record)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise BudgetWorkflowError(
            "Standard cost already exists for this scope"
        ) from exc

    await session.refresh(record)
    return record


async def create_cost_variance(
    session: AsyncSession,
    *,
    payload: CostVarianceCreate,
) -> FinanceCostVariance:
    amount, percent, favourable = calculate_budget_variance(
        budget_amount=payload.budget_amount,
        actual_amount=payload.actual_amount,
        expense_nature=payload.expense_nature,
    )

    variance = FinanceCostVariance(
        tenant_id=payload.tenant_id,
        variance_date=payload.variance_date,
        variance_type=payload.variance_type,
        object_type=payload.object_type,
        object_reference=payload.object_reference.strip(),
        budget_amount=payload.budget_amount,
        actual_amount=payload.actual_amount,
        variance_amount=amount,
        variance_percent=percent,
        is_favourable=favourable,
    )

    session.add(variance)
    await session.commit()
    await session.refresh(variance)

    return variance


async def create_allocation_rule(
    session: AsyncSession,
    *,
    payload: CostAllocationRuleCreate,
) -> FinanceCostAllocationRule:
    source = await get_cost_centre(
        session,
        tenant_id=payload.tenant_id,
        cost_centre_id=payload.source_cost_centre_id,
    )

    if source is None:
        raise BudgetWorkflowError(
            "Allocation source cost centre not found"
        )

    rule = FinanceCostAllocationRule(
        tenant_id=payload.tenant_id,
        rule_code=payload.rule_code.strip(),
        name=payload.name.strip(),
        allocation_method=payload.allocation_method,
        source_cost_centre_id=payload.source_cost_centre_id,
        target_object_type=payload.target_object_type,
        basis_reference=payload.basis_reference,
    )

    session.add(rule)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise BudgetWorkflowError(
            "Allocation-rule code already exists"
        ) from exc

    await session.refresh(rule)
    return rule
