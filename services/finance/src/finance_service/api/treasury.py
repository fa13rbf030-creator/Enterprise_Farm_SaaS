from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
    Query,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from finance_service.api.gl import validate_payload_tenant
from finance_service.db.session import get_db_session
from finance_service.repositories.treasury import (
    list_liquidity_forecasts,
    list_treasury_batches,
)
from finance_service.schemas.treasury import (
    LiquidityForecastCreate,
    LiquidityForecastRead,
    SettlementConfirmationCreate,
    TreasuryBatchApprovalCreate,
    TreasuryBatchSubmissionCreate,
    TreasuryBatchSubmitForApproval,
    TreasuryDashboardRead,
    TreasuryFraudReviewRead,
    TreasuryPaymentBatchCreate,
    TreasuryPaymentBatchFullRead,
    TreasuryPaymentBatchRead,
    TreasuryPaymentFileRead,
)
from finance_service.services.treasury import (
    TreasuryWorkflowError,
    build_treasury_dashboard,
    confirm_item_settlement,
    create_liquidity_forecast,
    create_payment_batch,
    decide_batch_approval,
    generate_payment_file,
    get_payment_batch_detail,
    review_batch_fraud,
    submit_batch_for_approval,
    submit_batch_to_bank,
)


router = APIRouter(
    prefix="/treasury",
    tags=["treasury"],
)


def translate_treasury_error(
    exc: TreasuryWorkflowError,
) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail=str(exc),
    )


@router.post(
    "/payment-batches",
    response_model=TreasuryPaymentBatchRead,
    status_code=status.HTTP_201_CREATED,
)
async def post_payment_batch(
    payload: TreasuryPaymentBatchCreate,
    x_tenant_id: UUID = Header(
        ...,
        alias="X-Tenant-ID",
    ),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        return await create_payment_batch(
            session,
            payload=payload,
        )
    except TreasuryWorkflowError as exc:
        raise translate_treasury_error(exc) from exc


@router.get(
    "/payment-batches",
    response_model=list[TreasuryPaymentBatchRead],
)
async def get_payment_batches(
    x_tenant_id: UUID = Header(
        ...,
        alias="X-Tenant-ID",
    ),
    session: AsyncSession = Depends(get_db_session),
):
    return await list_treasury_batches(
        session,
        tenant_id=x_tenant_id,
    )


@router.get(
    "/payment-batches/{batch_id}",
    response_model=TreasuryPaymentBatchFullRead,
)
async def get_payment_batch(
    batch_id: UUID,
    x_tenant_id: UUID = Header(
        ...,
        alias="X-Tenant-ID",
    ),
    session: AsyncSession = Depends(get_db_session),
):
    try:
        return await get_payment_batch_detail(
            session,
            tenant_id=x_tenant_id,
            batch_id=batch_id,
        )
    except TreasuryWorkflowError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get(
    "/payment-batches/{batch_id}/fraud-review",
    response_model=TreasuryFraudReviewRead,
)
async def get_batch_fraud_review(
    batch_id: UUID,
    x_tenant_id: UUID = Header(
        ...,
        alias="X-Tenant-ID",
    ),
    session: AsyncSession = Depends(get_db_session),
):
    try:
        return await review_batch_fraud(
            session,
            tenant_id=x_tenant_id,
            batch_id=batch_id,
        )
    except TreasuryWorkflowError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.post(
    "/payment-batches/{batch_id}/submit-for-approval",
    response_model=TreasuryPaymentBatchRead,
)
async def post_submit_for_approval(
    batch_id: UUID,
    payload: TreasuryBatchSubmitForApproval,
    x_tenant_id: UUID = Header(
        ...,
        alias="X-Tenant-ID",
    ),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        return await submit_batch_for_approval(
            session,
            tenant_id=x_tenant_id,
            batch_id=batch_id,
            submitted_by=payload.submitted_by,
        )
    except TreasuryWorkflowError as exc:
        raise translate_treasury_error(exc) from exc


@router.post(
    "/payment-batches/{batch_id}/approval",
    response_model=TreasuryPaymentBatchRead,
)
async def post_batch_approval(
    batch_id: UUID,
    payload: TreasuryBatchApprovalCreate,
    x_tenant_id: UUID = Header(
        ...,
        alias="X-Tenant-ID",
    ),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        return await decide_batch_approval(
            session,
            batch_id=batch_id,
            payload=payload,
        )
    except TreasuryWorkflowError as exc:
        raise translate_treasury_error(exc) from exc


@router.post(
    "/payment-batches/{batch_id}/generate-file",
    response_model=TreasuryPaymentFileRead,
)
async def post_generate_payment_file(
    batch_id: UUID,
    x_tenant_id: UUID = Header(
        ...,
        alias="X-Tenant-ID",
    ),
    session: AsyncSession = Depends(get_db_session),
):
    try:
        return await generate_payment_file(
            session,
            tenant_id=x_tenant_id,
            batch_id=batch_id,
        )
    except TreasuryWorkflowError as exc:
        raise translate_treasury_error(exc) from exc


@router.post(
    "/payment-batches/{batch_id}/submit-to-bank",
    response_model=TreasuryPaymentBatchRead,
)
async def post_submit_to_bank(
    batch_id: UUID,
    payload: TreasuryBatchSubmissionCreate,
    x_tenant_id: UUID = Header(
        ...,
        alias="X-Tenant-ID",
    ),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        return await submit_batch_to_bank(
            session,
            tenant_id=x_tenant_id,
            batch_id=batch_id,
            submitted_by=payload.submitted_by,
            external_submission_id=(
                payload.external_submission_id
            ),
        )
    except TreasuryWorkflowError as exc:
        raise translate_treasury_error(exc) from exc


@router.post(
    "/payment-items/{item_id}/settlement",
    response_model=TreasuryPaymentBatchRead,
)
async def post_item_settlement(
    item_id: UUID,
    payload: SettlementConfirmationCreate,
    x_tenant_id: UUID = Header(
        ...,
        alias="X-Tenant-ID",
    ),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        return await confirm_item_settlement(
            session,
            item_id=item_id,
            payload=payload,
        )
    except TreasuryWorkflowError as exc:
        raise translate_treasury_error(exc) from exc


@router.post(
    "/liquidity-forecasts",
    response_model=LiquidityForecastRead,
    status_code=status.HTTP_201_CREATED,
)
async def post_liquidity_forecast(
    payload: LiquidityForecastCreate,
    x_tenant_id: UUID = Header(
        ...,
        alias="X-Tenant-ID",
    ),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        return await create_liquidity_forecast(
            session,
            payload=payload,
        )
    except TreasuryWorkflowError as exc:
        raise translate_treasury_error(exc) from exc


@router.get(
    "/liquidity-forecasts",
    response_model=list[LiquidityForecastRead],
)
async def get_liquidity_forecasts(
    forecast_date: date | None = None,
    currency_code: str | None = Query(
        default=None,
        min_length=3,
        max_length=3,
    ),
    x_tenant_id: UUID = Header(
        ...,
        alias="X-Tenant-ID",
    ),
    session: AsyncSession = Depends(get_db_session),
):
    return await list_liquidity_forecasts(
        session,
        tenant_id=x_tenant_id,
        forecast_date=forecast_date,
        currency_code=currency_code,
    )


@router.get(
    "/dashboard",
    response_model=TreasuryDashboardRead,
)
async def get_treasury_dashboard(
    x_tenant_id: UUID = Header(
        ...,
        alias="X-Tenant-ID",
    ),
    session: AsyncSession = Depends(get_db_session),
):
    return await build_treasury_dashboard(
        session,
        tenant_id=x_tenant_id,
    )
