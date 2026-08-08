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
from finance_service.schemas.finance_controls import (
    FinanceAuditEvidenceCreate,
    FinanceAuditEvidenceRead,
    FinanceControlAttestationCreate,
    FinanceControlAttestationRead,
    FinanceControlDefinitionCreate,
    FinanceControlDefinitionRead,
    FinanceControlExceptionCreate,
    FinanceControlExceptionRead,
    FinanceControlExecutionCreate,
    FinanceControlExecutionRead,
    FinanceReconciliationRunCreate,
    FinanceReconciliationRunRead,
)
from finance_service.services.finance_controls import (
    FinanceControlWorkflowError,
    create_audit_evidence,
    create_control_attestation,
    create_control_definition,
    create_control_exception,
    create_control_execution,
    create_reconciliation_run,
)


router = APIRouter(
    prefix="/finance-controls",
    tags=["finance-controls"],
)


def translate_finance_control_error(
    exc: FinanceControlWorkflowError,
) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail=str(exc),
    )


@router.post(
    "/definitions",
    response_model=FinanceControlDefinitionRead,
    status_code=status.HTTP_201_CREATED,
)
async def post_control_definition(
    payload: FinanceControlDefinitionCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        return await create_control_definition(
            session,
            payload=payload,
        )
    except FinanceControlWorkflowError as exc:
        raise translate_finance_control_error(exc) from exc


@router.post(
    "/executions",
    response_model=FinanceControlExecutionRead,
    status_code=status.HTTP_201_CREATED,
)
async def post_control_execution(
    payload: FinanceControlExecutionCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        return await create_control_execution(
            session,
            payload=payload,
        )
    except FinanceControlWorkflowError as exc:
        raise translate_finance_control_error(exc) from exc


@router.post(
    "/reconciliations",
    response_model=FinanceReconciliationRunRead,
    status_code=status.HTTP_201_CREATED,
)
async def post_reconciliation_run(
    payload: FinanceReconciliationRunCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        return await create_reconciliation_run(
            session,
            payload=payload,
        )
    except FinanceControlWorkflowError as exc:
        raise translate_finance_control_error(exc) from exc


@router.post(
    "/exceptions",
    response_model=FinanceControlExceptionRead,
    status_code=status.HTTP_201_CREATED,
)
async def post_control_exception(
    payload: FinanceControlExceptionCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        return await create_control_exception(
            session,
            payload=payload,
        )
    except FinanceControlWorkflowError as exc:
        raise translate_finance_control_error(exc) from exc


@router.post(
    "/attestations",
    response_model=FinanceControlAttestationRead,
    status_code=status.HTTP_201_CREATED,
)
async def post_control_attestation(
    payload: FinanceControlAttestationCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        return await create_control_attestation(
            session,
            payload=payload,
        )
    except FinanceControlWorkflowError as exc:
        raise translate_finance_control_error(exc) from exc


@router.post(
    "/audit-evidence",
    response_model=FinanceAuditEvidenceRead,
    status_code=status.HTTP_201_CREATED,
)
async def post_audit_evidence(
    payload: FinanceAuditEvidenceCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        return await create_audit_evidence(
            session,
            payload=payload,
        )
    except FinanceControlWorkflowError as exc:
        raise translate_finance_control_error(exc) from exc
