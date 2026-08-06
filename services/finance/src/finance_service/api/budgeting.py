from __future__ import annotations

from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from finance_service.api.gl import validate_payload_tenant
from finance_service.db.session import get_db_session
from finance_service.schemas.budgeting import (
    BudgetApprovalRequest,
    BudgetCreate,
    BudgetDetailRead,
    BudgetRead,
    BudgetSubmitRequest,
    CostAllocationRuleCreate,
    CostAllocationRuleRead,
    CostCentreCreate,
    CostCentreRead,
    CostVarianceCreate,
    CostVarianceRead,
    ProfitCentreCreate,
    ProfitCentreRead,
    StandardCostCreate,
    StandardCostRead,
)
from finance_service.services.budgeting import (
    BudgetWorkflowError,
    create_allocation_rule,
    create_budget,
    create_cost_centre,
    create_cost_variance,
    create_profit_centre,
    create_standard_cost,
    decide_budget_approval,
    get_budget_detail,
    submit_budget_for_approval,
)


router = APIRouter(
    prefix="/budgeting",
    tags=["budgeting"],
)


def translate_budget_error(
    exc: BudgetWorkflowError,
) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail=str(exc),
    )


@router.post(
    "/cost-centres",
    response_model=CostCentreRead,
    status_code=status.HTTP_201_CREATED,
)
async def post_cost_centre(
    payload: CostCentreCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        return await create_cost_centre(
            session,
            payload=payload,
        )
    except BudgetWorkflowError as exc:
        raise translate_budget_error(exc) from exc


@router.post(
    "/profit-centres",
    response_model=ProfitCentreRead,
    status_code=status.HTTP_201_CREATED,
)
async def post_profit_centre(
    payload: ProfitCentreCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        return await create_profit_centre(
            session,
            payload=payload,
        )
    except BudgetWorkflowError as exc:
        raise translate_budget_error(exc) from exc


@router.post(
    "/budgets",
    response_model=BudgetRead,
    status_code=status.HTTP_201_CREATED,
)
async def post_budget(
    payload: BudgetCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        return await create_budget(
            session,
            payload=payload,
        )
    except BudgetWorkflowError as exc:
        raise translate_budget_error(exc) from exc


@router.get(
    "/budgets/{budget_id}",
    response_model=BudgetDetailRead,
)
async def get_budget(
    budget_id: UUID,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    try:
        return await get_budget_detail(
            session,
            tenant_id=x_tenant_id,
            budget_id=budget_id,
        )
    except BudgetWorkflowError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.post(
    "/budgets/{budget_id}/submit",
    response_model=BudgetRead,
)
async def post_budget_submission(
    budget_id: UUID,
    payload: BudgetSubmitRequest,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        return await submit_budget_for_approval(
            session,
            tenant_id=x_tenant_id,
            budget_id=budget_id,
            submitted_by=payload.submitted_by,
        )
    except BudgetWorkflowError as exc:
        raise translate_budget_error(exc) from exc


@router.post(
    "/budgets/{budget_id}/approval",
    response_model=BudgetRead,
)
async def post_budget_approval(
    budget_id: UUID,
    payload: BudgetApprovalRequest,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        return await decide_budget_approval(
            session,
            budget_id=budget_id,
            payload=payload,
        )
    except BudgetWorkflowError as exc:
        raise translate_budget_error(exc) from exc


@router.post(
    "/standard-costs",
    response_model=StandardCostRead,
    status_code=status.HTTP_201_CREATED,
)
async def post_standard_cost(
    payload: StandardCostCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        return await create_standard_cost(
            session,
            payload=payload,
        )
    except BudgetWorkflowError as exc:
        raise translate_budget_error(exc) from exc


@router.post(
    "/variances",
    response_model=CostVarianceRead,
    status_code=status.HTTP_201_CREATED,
)
async def post_cost_variance(
    payload: CostVarianceCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    return await create_cost_variance(
        session,
        payload=payload,
    )


@router.post(
    "/allocation-rules",
    response_model=CostAllocationRuleRead,
    status_code=status.HTTP_201_CREATED,
)
async def post_allocation_rule(
    payload: CostAllocationRuleCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        return await create_allocation_rule(
            session,
            payload=payload,
        )
    except BudgetWorkflowError as exc:
        raise translate_budget_error(exc) from exc
