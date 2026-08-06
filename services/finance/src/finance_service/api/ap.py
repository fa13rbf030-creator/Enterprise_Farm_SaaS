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
from finance_service.repositories.ap import (
    list_vendor_invoices,
    list_vendors,
)
from finance_service.schemas.ap import (
    DebitNoteCreate,
    DebitNoteRead,
    PayablesAgingRead,
    SupplierInvoiceCreate,
    SupplierInvoiceDetailRead,
    SupplierInvoiceRead,
    VendorCreate,
    VendorPaymentAllocationCreate,
    VendorPaymentCreate,
    VendorPaymentRead,
    VendorRead,
)
from finance_service.services.ap import (
    ApWorkflowError,
    allocate_vendor_payment,
    build_payables_aging,
    create_debit_note,
    create_supplier_invoice,
    create_vendor,
    create_vendor_payment,
    get_supplier_invoice_detail,
    issue_debit_note,
    post_supplier_invoice,
    post_vendor_payment,
)


router = APIRouter(
    prefix="/ap",
    tags=["accounts-payable"],
)


def translate_ap_error(exc: ApWorkflowError) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=str(exc),
    )


@router.post(
    "/vendors",
    response_model=VendorRead,
    status_code=status.HTTP_201_CREATED,
)
async def post_vendor(
    payload: VendorCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        return await create_vendor(session, payload=payload)
    except ApWorkflowError as exc:
        raise translate_ap_error(exc) from exc


@router.get(
    "/vendors",
    response_model=list[VendorRead],
)
async def get_vendors(
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    return await list_vendors(
        session,
        tenant_id=x_tenant_id,
    )


@router.post(
    "/invoices",
    response_model=SupplierInvoiceRead,
    status_code=status.HTTP_201_CREATED,
)
async def post_supplier_invoice_create(
    payload: SupplierInvoiceCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        return await create_supplier_invoice(
            session,
            payload=payload,
        )
    except ApWorkflowError as exc:
        raise translate_ap_error(exc) from exc


@router.get(
    "/invoices/{invoice_id}",
    response_model=SupplierInvoiceDetailRead,
)
async def get_supplier_invoice_endpoint(
    invoice_id: UUID,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    try:
        return await get_supplier_invoice_detail(
            session,
            tenant_id=x_tenant_id,
            invoice_id=invoice_id,
        )
    except ApWorkflowError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.post(
    "/invoices/{invoice_id}/post",
    response_model=SupplierInvoiceRead,
)
async def post_supplier_invoice_endpoint(
    invoice_id: UUID,
    posted_by: UUID = Query(...),
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    try:
        return await post_supplier_invoice(
            session,
            tenant_id=x_tenant_id,
            invoice_id=invoice_id,
            posted_by=posted_by,
        )
    except ApWorkflowError as exc:
        raise translate_ap_error(exc) from exc


@router.get(
    "/vendors/{vendor_id}/invoices",
    response_model=list[SupplierInvoiceRead],
)
async def get_vendor_invoices(
    vendor_id: UUID,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    return await list_vendor_invoices(
        session,
        tenant_id=x_tenant_id,
        vendor_id=vendor_id,
    )


@router.post(
    "/payments",
    response_model=VendorPaymentRead,
    status_code=status.HTTP_201_CREATED,
)
async def post_vendor_payment_create(
    payload: VendorPaymentCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        return await create_vendor_payment(
            session,
            payload=payload,
        )
    except ApWorkflowError as exc:
        raise translate_ap_error(exc) from exc


@router.post(
    "/payments/{payment_id}/post",
    response_model=VendorPaymentRead,
)
async def post_vendor_payment_endpoint(
    payment_id: UUID,
    posted_by: UUID = Query(...),
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    try:
        return await post_vendor_payment(
            session,
            tenant_id=x_tenant_id,
            payment_id=payment_id,
            posted_by=posted_by,
        )
    except ApWorkflowError as exc:
        raise translate_ap_error(exc) from exc


@router.post(
    "/payments/{payment_id}/allocations",
    response_model=VendorPaymentRead,
)
async def post_vendor_payment_allocation(
    payment_id: UUID,
    payload: VendorPaymentAllocationCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        return await allocate_vendor_payment(
            session,
            payment_id=payment_id,
            payload=payload,
        )
    except ApWorkflowError as exc:
        raise translate_ap_error(exc) from exc


@router.post(
    "/debit-notes",
    response_model=DebitNoteRead,
    status_code=status.HTTP_201_CREATED,
)
async def post_debit_note(
    payload: DebitNoteCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        return await create_debit_note(
            session,
            payload=payload,
        )
    except ApWorkflowError as exc:
        raise translate_ap_error(exc) from exc


@router.post(
    "/debit-notes/{debit_note_id}/issue",
    response_model=DebitNoteRead,
)
async def issue_debit_note_endpoint(
    debit_note_id: UUID,
    issued_by: UUID = Query(...),
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    try:
        return await issue_debit_note(
            session,
            tenant_id=x_tenant_id,
            debit_note_id=debit_note_id,
            issued_by=issued_by,
        )
    except ApWorkflowError as exc:
        raise translate_ap_error(exc) from exc


@router.get(
    "/aging",
    response_model=PayablesAgingRead,
)
async def get_payables_aging(
    as_of_date: date,
    vendor_id: UUID | None = None,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    return await build_payables_aging(
        session,
        tenant_id=x_tenant_id,
        as_of_date=as_of_date,
        vendor_id=vendor_id,
    )
