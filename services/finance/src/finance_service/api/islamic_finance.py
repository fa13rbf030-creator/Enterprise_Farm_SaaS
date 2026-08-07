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
from finance_service.schemas.islamic_finance import (
    IslamicDisbursementEvidenceCreate,
    IslamicDisbursementEvidenceRead,
    LivestockZakatRuleCreate,
    NisabReferenceCreate,
    NisabReferenceRead,
    SadaqahTransactionCreate,
    SadaqahTransactionRead,
    ShariahRuleApprove,
    ShariahRuleSetCreate,
    ShariahRuleSetRead,
    UshrAssessmentCreate,
    UshrAssessmentRead,
    ZakatAssessmentCreate,
    ZakatAssessmentRead,
)
from finance_service.services.islamic_finance import (
    IslamicFinanceWorkflowError,
    approve_shariah_rule_set,
    create_disbursement_evidence,
    create_livestock_zakat_rule,
    create_nisab_reference,
    create_sadaqah_transaction,
    create_shariah_rule_set,
    create_ushr_assessment,
    create_zakat_assessment,
)


router = APIRouter(
    prefix="/islamic-finance",
    tags=["islamic-finance"],
)


def translate_islamic_finance_error(
    exc: IslamicFinanceWorkflowError,
) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail=str(exc),
    )


@router.post(
    "/rule-sets",
    response_model=ShariahRuleSetRead,
    status_code=status.HTTP_201_CREATED,
)
async def post_rule_set(
    payload: ShariahRuleSetCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        return await create_shariah_rule_set(
            session,
            payload=payload,
        )
    except IslamicFinanceWorkflowError as exc:
        raise translate_islamic_finance_error(exc) from exc


@router.post(
    "/rule-sets/{rule_set_id}/approve",
    response_model=ShariahRuleSetRead,
)
async def post_approve_rule_set(
    rule_set_id: UUID,
    payload: ShariahRuleApprove,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        return await approve_shariah_rule_set(
            session,
            rule_set_id=rule_set_id,
            payload=payload,
        )
    except IslamicFinanceWorkflowError as exc:
        raise translate_islamic_finance_error(exc) from exc


@router.post(
    "/nisab-references",
    response_model=NisabReferenceRead,
    status_code=status.HTTP_201_CREATED,
)
async def post_nisab_reference(
    payload: NisabReferenceCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        return await create_nisab_reference(
            session,
            payload=payload,
        )
    except IslamicFinanceWorkflowError as exc:
        raise translate_islamic_finance_error(exc) from exc


@router.post(
    "/zakat-assessments",
    response_model=ZakatAssessmentRead,
    status_code=status.HTTP_201_CREATED,
)
async def post_zakat_assessment(
    payload: ZakatAssessmentCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        return await create_zakat_assessment(
            session,
            payload=payload,
        )
    except IslamicFinanceWorkflowError as exc:
        raise translate_islamic_finance_error(exc) from exc


@router.post(
    "/ushr-assessments",
    response_model=UshrAssessmentRead,
    status_code=status.HTTP_201_CREATED,
)
async def post_ushr_assessment(
    payload: UshrAssessmentCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        return await create_ushr_assessment(
            session,
            payload=payload,
        )
    except IslamicFinanceWorkflowError as exc:
        raise translate_islamic_finance_error(exc) from exc


@router.post(
    "/livestock-zakat-rules",
    status_code=status.HTTP_201_CREATED,
)
async def post_livestock_zakat_rule(
    payload: LivestockZakatRuleCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        return await create_livestock_zakat_rule(
            session,
            payload=payload,
        )
    except IslamicFinanceWorkflowError as exc:
        raise translate_islamic_finance_error(exc) from exc


@router.post(
    "/sadaqah-transactions",
    response_model=SadaqahTransactionRead,
    status_code=status.HTTP_201_CREATED,
)
async def post_sadaqah_transaction(
    payload: SadaqahTransactionCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        return await create_sadaqah_transaction(
            session,
            payload=payload,
        )
    except IslamicFinanceWorkflowError as exc:
        raise translate_islamic_finance_error(exc) from exc


@router.post(
    "/disbursement-evidence",
    response_model=IslamicDisbursementEvidenceRead,
    status_code=status.HTTP_201_CREATED,
)
async def post_disbursement_evidence(
    payload: IslamicDisbursementEvidenceCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        return await create_disbursement_evidence(
            session,
            payload=payload,
        )
    except IslamicFinanceWorkflowError as exc:
        raise translate_islamic_finance_error(exc) from exc
