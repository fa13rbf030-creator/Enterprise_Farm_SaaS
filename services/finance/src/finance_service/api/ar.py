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
from finance_service.repositories.ar import (
    list_customer_invoices,
    list_customers,
)
from finance_service.schemas.ar import (
    CreditNoteCreate,
    CreditNoteRead,
    CustomerAgingRead,
    CustomerCreate,
    CustomerRead,
    InvoiceCreate,
    InvoiceDetailRead,
    InvoiceRead,
    ReceiptAllocationCreate,
    ReceiptCreate,
    ReceiptPostRequest,
    ReceiptRead,
)
from finance_service.services.ar import (
    ArWorkflowError,
    allocate_receipt,
    build_aging,
    create_credit_note,
    create_customer,
    create_invoice,
    create_receipt,
    get_invoice_detail,
    issue_credit_note,
    issue_invoice,
    post_receipt,
)


router = APIRouter(
    prefix="/ar",
    tags=["accounts-receivable"],
)


def translate_ar_error(exc: ArWorkflowError) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=str(exc),
    )


@router.post(
    "/customers",
    response_model=CustomerRead,
    status_code=status.HTTP_201_CREATED,
)
async def post_customer(
    payload: CustomerCreate,
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
        return await create_customer(
            session,
            payload=payload,
        )
    except ArWorkflowError as exc:
        raise translate_ar_error(exc) from exc


@router.get(
    "/customers",
    response_model=list[CustomerRead],
)
async def get_customers(
    x_tenant_id: UUID = Header(
        ...,
        alias="X-Tenant-ID",
    ),
    session: AsyncSession = Depends(get_db_session),
):
    return await list_customers(
        session,
        tenant_id=x_tenant_id,
    )


@router.post(
    "/invoices",
    response_model=InvoiceRead,
    status_code=status.HTTP_201_CREATED,
)
async def post_invoice(
    payload: InvoiceCreate,
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
        return await create_invoice(
            session,
            payload=payload,
        )
    except ArWorkflowError as exc:
        raise translate_ar_error(exc) from exc


@router.get(
    "/invoices/{invoice_id}",
    response_model=InvoiceDetailRead,
)
async def get_invoice_endpoint(
    invoice_id: UUID,
    x_tenant_id: UUID = Header(
        ...,
        alias="X-Tenant-ID",
    ),
    session: AsyncSession = Depends(get_db_session),
):
    try:
        return await get_invoice_detail(
            session,
            tenant_id=x_tenant_id,
            invoice_id=invoice_id,
        )
    except ArWorkflowError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.post(
    "/invoices/{invoice_id}/issue",
    response_model=InvoiceRead,
)
async def issue_invoice_endpoint(
    invoice_id: UUID,
    issued_by: UUID = Query(...),
    x_tenant_id: UUID = Header(
        ...,
        alias="X-Tenant-ID",
    ),
    session: AsyncSession = Depends(get_db_session),
):
    try:
        return await issue_invoice(
            session,
            tenant_id=x_tenant_id,
            invoice_id=invoice_id,
            issued_by=issued_by,
        )
    except ArWorkflowError as exc:
        raise translate_ar_error(exc) from exc


@router.get(
    "/customers/{customer_id}/invoices",
    response_model=list[InvoiceRead],
)
async def get_customer_invoices(
    customer_id: UUID,
    x_tenant_id: UUID = Header(
        ...,
        alias="X-Tenant-ID",
    ),
    session: AsyncSession = Depends(get_db_session),
):
    return await list_customer_invoices(
        session,
        tenant_id=x_tenant_id,
        customer_id=customer_id,
    )


@router.post(
    "/receipts",
    response_model=ReceiptRead,
    status_code=status.HTTP_201_CREATED,
)
async def post_receipt_create(
    payload: ReceiptCreate,
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
        return await create_receipt(
            session,
            payload=payload,
        )
    except ArWorkflowError as exc:
        raise translate_ar_error(exc) from exc


@router.post(
    "/receipts/{receipt_id}/post",
    response_model=ReceiptRead,
)
async def post_receipt_endpoint(
    receipt_id: UUID,
    payload: ReceiptPostRequest,
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
        return await post_receipt(
            session,
            tenant_id=x_tenant_id,
            receipt_id=receipt_id,
            cash_account_id=payload.cash_account_id,
            posted_by=payload.posted_by,
        )
    except ArWorkflowError as exc:
        raise translate_ar_error(exc) from exc


@router.post(
    "/receipts/{receipt_id}/allocations",
    response_model=ReceiptRead,
)
async def post_receipt_allocation(
    receipt_id: UUID,
    payload: ReceiptAllocationCreate,
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
        return await allocate_receipt(
            session,
            receipt_id=receipt_id,
            payload=payload,
        )
    except ArWorkflowError as exc:
        raise translate_ar_error(exc) from exc


@router.post(
    "/credit-notes",
    response_model=CreditNoteRead,
    status_code=status.HTTP_201_CREATED,
)
async def post_credit_note(
    payload: CreditNoteCreate,
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
        return await create_credit_note(
            session,
            payload=payload,
        )
    except ArWorkflowError as exc:
        raise translate_ar_error(exc) from exc


@router.post(
    "/credit-notes/{credit_note_id}/issue",
    response_model=CreditNoteRead,
)
async def issue_credit_note_endpoint(
    credit_note_id: UUID,
    issued_by: UUID = Query(...),
    x_tenant_id: UUID = Header(
        ...,
        alias="X-Tenant-ID",
    ),
    session: AsyncSession = Depends(get_db_session),
):
    try:
        return await issue_credit_note(
            session,
            tenant_id=x_tenant_id,
            credit_note_id=credit_note_id,
            issued_by=issued_by,
        )
    except ArWorkflowError as exc:
        raise translate_ar_error(exc) from exc


@router.get(
    "/aging",
    response_model=CustomerAgingRead,
)
async def get_aging(
    as_of_date: date,
    customer_id: UUID | None = None,
    x_tenant_id: UUID = Header(
        ...,
        alias="X-Tenant-ID",
    ),
    session: AsyncSession = Depends(get_db_session),
):
    return await build_aging(
        session,
        tenant_id=x_tenant_id,
        as_of_date=as_of_date,
        customer_id=customer_id,
    )
