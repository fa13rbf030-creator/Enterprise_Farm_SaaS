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
from finance_service.schemas.tax_compliance import (
    StatutoryFilingCreate,
    StatutoryFilingRead,
    TaxCodeCreate,
    TaxCodeRead,
    TaxJurisdictionCreate,
    TaxJurisdictionRead,
    TaxPeriodCreate,
    TaxPeriodRead,
    TaxRateCreate,
    TaxRateRead,
    TaxRegistrationCreate,
    TaxRegistrationRead,
    TaxReturnCreate,
    TaxReturnRead,
    WithholdingTaxRuleCreate,
)
from finance_service.services.tax_compliance import (
    TaxComplianceWorkflowError,
    create_statutory_filing,
    create_tax_code,
    create_tax_jurisdiction,
    create_tax_period,
    create_tax_rate,
    create_tax_registration,
    create_tax_return,
    create_withholding_rule,
)


router = APIRouter(
    prefix="/tax-compliance",
    tags=["tax-compliance"],
)


def translate_tax_compliance_error(
    exc: TaxComplianceWorkflowError,
) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail=str(exc),
    )


@router.post(
    "/jurisdictions",
    response_model=TaxJurisdictionRead,
    status_code=status.HTTP_201_CREATED,
)
async def post_tax_jurisdiction(
    payload: TaxJurisdictionCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        return await create_tax_jurisdiction(
            session,
            payload=payload,
        )
    except TaxComplianceWorkflowError as exc:
        raise translate_tax_compliance_error(exc) from exc


@router.post(
    "/registrations",
    response_model=TaxRegistrationRead,
    status_code=status.HTTP_201_CREATED,
)
async def post_tax_registration(
    payload: TaxRegistrationCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        return await create_tax_registration(
            session,
            payload=payload,
        )
    except TaxComplianceWorkflowError as exc:
        raise translate_tax_compliance_error(exc) from exc


@router.post(
    "/codes",
    response_model=TaxCodeRead,
    status_code=status.HTTP_201_CREATED,
)
async def post_tax_code(
    payload: TaxCodeCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        return await create_tax_code(
            session,
            payload=payload,
        )
    except TaxComplianceWorkflowError as exc:
        raise translate_tax_compliance_error(exc) from exc


@router.post(
    "/rates",
    response_model=TaxRateRead,
    status_code=status.HTTP_201_CREATED,
)
async def post_tax_rate(
    payload: TaxRateCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        return await create_tax_rate(
            session,
            payload=payload,
        )
    except TaxComplianceWorkflowError as exc:
        raise translate_tax_compliance_error(exc) from exc


@router.post(
    "/withholding-rules",
    status_code=status.HTTP_201_CREATED,
)
async def post_withholding_rule(
    payload: WithholdingTaxRuleCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        return await create_withholding_rule(
            session,
            payload=payload,
        )
    except TaxComplianceWorkflowError as exc:
        raise translate_tax_compliance_error(exc) from exc


@router.post(
    "/periods",
    response_model=TaxPeriodRead,
    status_code=status.HTTP_201_CREATED,
)
async def post_tax_period(
    payload: TaxPeriodCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        return await create_tax_period(
            session,
            payload=payload,
        )
    except TaxComplianceWorkflowError as exc:
        raise translate_tax_compliance_error(exc) from exc


@router.post(
    "/returns",
    response_model=TaxReturnRead,
    status_code=status.HTTP_201_CREATED,
)
async def post_tax_return(
    payload: TaxReturnCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        return await create_tax_return(
            session,
            payload=payload,
        )
    except TaxComplianceWorkflowError as exc:
        raise translate_tax_compliance_error(exc) from exc


@router.post(
    "/filings",
    response_model=StatutoryFilingRead,
    status_code=status.HTTP_201_CREATED,
)
async def post_statutory_filing(
    payload: StatutoryFilingCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        return await create_statutory_filing(
            session,
            payload=payload,
        )
    except TaxComplianceWorkflowError as exc:
        raise translate_tax_compliance_error(exc) from exc
