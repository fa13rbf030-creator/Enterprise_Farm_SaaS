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
from finance_service.schemas.intercompany import (
    ConsolidationGroupCreate,
    ConsolidationGroupRead,
    ConsolidationPeriodCreate,
    ConsolidationPeriodRead,
    IntercompanyAccountMappingCreate,
    IntercompanyAccountMappingRead,
    IntercompanyOrganizationCreate,
    IntercompanyOrganizationRead,
    IntercompanyRelationshipCreate,
    IntercompanyRelationshipRead,
    IntercompanyTransactionCreate,
    IntercompanyTransactionRead,
)
from finance_service.services.intercompany import (
    IntercompanyWorkflowError,
    create_consolidation_group,
    create_consolidation_period,
    create_intercompany_account_mapping,
    create_intercompany_organization,
    create_intercompany_relationship,
    create_intercompany_transaction,
)

router = APIRouter(
    prefix="/intercompany",
    tags=["intercompany"],
)


def translate_intercompany_error(
    exc: IntercompanyWorkflowError,
) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail=str(exc),
    )


@router.post(
    "/organizations",
    response_model=IntercompanyOrganizationRead,
    status_code=status.HTTP_201_CREATED,
)
async def post_intercompany_organization(
    payload: IntercompanyOrganizationCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        return await create_intercompany_organization(
            session,
            payload=payload,
        )
    except IntercompanyWorkflowError as exc:
        raise translate_intercompany_error(exc) from exc


@router.post(
    "/relationships",
    response_model=IntercompanyRelationshipRead,
    status_code=status.HTTP_201_CREATED,
)
async def post_intercompany_relationship(
    payload: IntercompanyRelationshipCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        return await create_intercompany_relationship(
            session,
            payload=payload,
        )
    except IntercompanyWorkflowError as exc:
        raise translate_intercompany_error(exc) from exc


@router.post(
    "/account-mappings",
    response_model=IntercompanyAccountMappingRead,
    status_code=status.HTTP_201_CREATED,
)
async def post_intercompany_account_mapping(
    payload: IntercompanyAccountMappingCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        return await create_intercompany_account_mapping(
            session,
            payload=payload,
        )
    except IntercompanyWorkflowError as exc:
        raise translate_intercompany_error(exc) from exc


@router.post(
    "/consolidation-groups",
    response_model=ConsolidationGroupRead,
    status_code=status.HTTP_201_CREATED,
)
async def post_consolidation_group(
    payload: ConsolidationGroupCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        return await create_consolidation_group(
            session,
            payload=payload,
        )
    except IntercompanyWorkflowError as exc:
        raise translate_intercompany_error(exc) from exc


@router.post(
    "/consolidation-periods",
    response_model=ConsolidationPeriodRead,
    status_code=status.HTTP_201_CREATED,
)
async def post_consolidation_period(
    payload: ConsolidationPeriodCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        return await create_consolidation_period(
            session,
            payload=payload,
        )
    except IntercompanyWorkflowError as exc:
        raise translate_intercompany_error(exc) from exc


@router.post(
    "/transactions",
    response_model=IntercompanyTransactionRead,
    status_code=status.HTTP_201_CREATED,
)
async def post_intercompany_transaction(
    payload: IntercompanyTransactionCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        return await create_intercompany_transaction(
            session,
            payload=payload,
        )
    except IntercompanyWorkflowError as exc:
        raise translate_intercompany_error(exc) from exc
