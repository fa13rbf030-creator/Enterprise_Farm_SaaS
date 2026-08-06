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
from finance_service.schemas.financial_close import (
    FinancialCloseCycleCreate,
    FinancialCloseCycleRead,
    FinancialCloseExceptionCreate,
    FinancialCloseExceptionRead,
    FinancialCloseSignOffCreate,
    FinancialCloseSignOffRead,
    FinancialCloseTaskRead,
    FinancialCloseTaskStatusUpdate,
    FinancialPeriodLockCreate,
    FinancialPeriodLockRead,
    FinancialPeriodUnlock,
)
from finance_service.services.financial_close import (
    FinancialCloseWorkflowError,
    create_close_cycle,
    create_close_exception,
    lock_financial_period,
    open_close_cycle,
    sign_off_close_cycle,
    unlock_financial_period,
    update_close_task_status,
)


router = APIRouter(
    prefix="/financial-close",
    tags=["financial-close"],
)


def translate_financial_close_error(
    exc: FinancialCloseWorkflowError,
) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail=str(exc),
    )


@router.post(
    "/cycles",
    response_model=FinancialCloseCycleRead,
    status_code=status.HTTP_201_CREATED,
)
async def post_close_cycle(
    payload: FinancialCloseCycleCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        return await create_close_cycle(
            session,
            payload=payload,
        )
    except FinancialCloseWorkflowError as exc:
        raise translate_financial_close_error(exc) from exc


@router.post(
    "/cycles/{cycle_id}/open",
    response_model=FinancialCloseCycleRead,
)
async def post_open_close_cycle(
    cycle_id: UUID,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    try:
        return await open_close_cycle(
            session,
            tenant_id=x_tenant_id,
            cycle_id=cycle_id,
        )
    except FinancialCloseWorkflowError as exc:
        raise translate_financial_close_error(exc) from exc


@router.patch(
    "/tasks/{task_id}/status",
    response_model=FinancialCloseTaskRead,
)
async def patch_close_task_status(
    task_id: UUID,
    payload: FinancialCloseTaskStatusUpdate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        return await update_close_task_status(
            session,
            task_id=task_id,
            payload=payload,
        )
    except FinancialCloseWorkflowError as exc:
        raise translate_financial_close_error(exc) from exc


@router.post(
    "/exceptions",
    response_model=FinancialCloseExceptionRead,
    status_code=status.HTTP_201_CREATED,
)
async def post_close_exception(
    payload: FinancialCloseExceptionCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        return await create_close_exception(
            session,
            payload=payload,
        )
    except FinancialCloseWorkflowError as exc:
        raise translate_financial_close_error(exc) from exc


@router.post(
    "/signoffs",
    response_model=FinancialCloseSignOffRead,
    status_code=status.HTTP_201_CREATED,
)
async def post_close_signoff(
    payload: FinancialCloseSignOffCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        return await sign_off_close_cycle(
            session,
            payload=payload,
        )
    except FinancialCloseWorkflowError as exc:
        raise translate_financial_close_error(exc) from exc


@router.post(
    "/period-locks",
    response_model=FinancialPeriodLockRead,
    status_code=status.HTTP_201_CREATED,
)
async def post_period_lock(
    payload: FinancialPeriodLockCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        return await lock_financial_period(
            session,
            payload=payload,
        )
    except FinancialCloseWorkflowError as exc:
        raise translate_financial_close_error(exc) from exc


@router.post(
    "/period-locks/{lock_id}/unlock",
    response_model=FinancialPeriodLockRead,
)
async def post_period_unlock(
    lock_id: UUID,
    payload: FinancialPeriodUnlock,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        return await unlock_financial_period(
            session,
            lock_id=lock_id,
            payload=payload,
        )
    except FinancialCloseWorkflowError as exc:
        raise translate_financial_close_error(exc) from exc
