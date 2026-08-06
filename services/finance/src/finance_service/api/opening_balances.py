from __future__ import annotations

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
from finance_service.schemas.closing import (
    OpeningBalanceBatchCreate,
    OpeningBalanceBatchRead,
)
from finance_service.services.opening_balance_workflow import (
    OpeningBalanceWorkflowError,
    create_opening_balance_batch,
    post_opening_balance_batch,
    validate_opening_balance_batch_record,
)


router = APIRouter(
    prefix="/gl/opening-balances",
    tags=["opening-balances"],
)


@router.post(
    "",
    response_model=OpeningBalanceBatchRead,
    status_code=status.HTTP_201_CREATED,
)
async def post_opening_balance_batch_create(
    payload: OpeningBalanceBatchCreate,
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
        return await create_opening_balance_batch(
            session,
            payload=payload,
        )
    except OpeningBalanceWorkflowError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.post(
    "/{batch_id}/validate",
    response_model=OpeningBalanceBatchRead,
)
async def validate_opening_balance_endpoint(
    batch_id: UUID,
    validated_by: UUID = Query(...),
    x_tenant_id: UUID = Header(
        ...,
        alias="X-Tenant-ID",
    ),
    session: AsyncSession = Depends(get_db_session),
):
    try:
        return await validate_opening_balance_batch_record(
            session,
            tenant_id=x_tenant_id,
            batch_id=batch_id,
            validated_by=validated_by,
        )
    except OpeningBalanceWorkflowError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.post(
    "/{batch_id}/post",
    response_model=OpeningBalanceBatchRead,
)
async def post_opening_balance_endpoint(
    batch_id: UUID,
    posted_by: UUID = Query(...),
    journal_number: str = Query(
        ...,
        min_length=1,
        max_length=100,
    ),
    x_tenant_id: UUID = Header(
        ...,
        alias="X-Tenant-ID",
    ),
    session: AsyncSession = Depends(get_db_session),
):
    try:
        return await post_opening_balance_batch(
            session,
            tenant_id=x_tenant_id,
            batch_id=batch_id,
            posted_by=posted_by,
            journal_number=journal_number,
        )
    except OpeningBalanceWorkflowError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
