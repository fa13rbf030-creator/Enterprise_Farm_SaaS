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
from finance_service.schemas.posting import (
    JournalPostRequest,
    JournalReverseRequest,
    JournalStatusRead,
    PeriodStatusUpdate,
    TrialBalanceRead,
)
from finance_service.services.posting import (
    PostingValidationError,
    build_trial_balance,
    post_journal,
    reverse_journal,
    update_period_status,
)


router = APIRouter(
    prefix="/gl",
    tags=["general-ledger-posting"],
)


@router.post(
    "/journals/{journal_id}/post",
    response_model=JournalStatusRead,
)
async def post_journal_endpoint(
    journal_id: UUID,
    payload: JournalPostRequest,
    x_tenant_id: UUID = Header(
        ...,
        alias="X-Tenant-ID",
    ),
    session: AsyncSession = Depends(get_db_session),
) -> JournalStatusRead:
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        journal = await post_journal(
            session,
            tenant_id=x_tenant_id,
            journal_id=journal_id,
            posted_by=payload.posted_by,
        )
    except PostingValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    return JournalStatusRead(
        id=journal.id,
        status=journal.status,
    )


@router.post(
    "/journals/{journal_id}/reverse",
    response_model=JournalStatusRead,
    status_code=status.HTTP_201_CREATED,
)
async def reverse_journal_endpoint(
    journal_id: UUID,
    payload: JournalReverseRequest,
    x_tenant_id: UUID = Header(
        ...,
        alias="X-Tenant-ID",
    ),
    session: AsyncSession = Depends(get_db_session),
) -> JournalStatusRead:
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        reversal = await reverse_journal(
            session,
            tenant_id=x_tenant_id,
            journal_id=journal_id,
            reversed_by=payload.reversed_by,
            reversal_journal_number=(
                payload.reversal_journal_number
            ),
            reversal_description=(
                payload.reversal_description
            ),
        )
    except PostingValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    return JournalStatusRead(
        id=reversal.id,
        status=reversal.status,
    )


@router.patch(
    "/fiscal-periods/{fiscal_period_id}/status",
)
async def patch_period_status(
    fiscal_period_id: UUID,
    payload: PeriodStatusUpdate,
    x_tenant_id: UUID = Header(
        ...,
        alias="X-Tenant-ID",
    ),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, str]:
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        period_status = await update_period_status(
            session,
            tenant_id=x_tenant_id,
            fiscal_period_id=fiscal_period_id,
            target_status=payload.status,
        )
    except PostingValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    return {"status": period_status.value}


@router.get(
    "/fiscal-periods/{fiscal_period_id}/trial-balance",
    response_model=TrialBalanceRead,
)
async def get_trial_balance(
    fiscal_period_id: UUID,
    x_tenant_id: UUID = Header(
        ...,
        alias="X-Tenant-ID",
    ),
    session: AsyncSession = Depends(get_db_session),
) -> TrialBalanceRead:
    return await build_trial_balance(
        session,
        tenant_id=x_tenant_id,
        fiscal_period_id=fiscal_period_id,
    )
